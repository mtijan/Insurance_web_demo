from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.assurances.models import (
    AssuranceNumberSequence, AssuranceStatus, VehicleAssurance,
)
from apps.assurances.services.workflow_validation import (
    get_locked_assurance, require_editable, require_mutation_access, validate_submission_data,
)
from apps.assurances.workflow_serializers import ReviewAssuranceSerializer
from apps.audit.services.audit_service import record_audit
from apps.assurances.services.inspection_service import append_review_event
from apps.notifications.models import NotificationEventType
from apps.notifications.services.notification_service import dispatch_assurance_notifications

_REVIEW_NOTIFICATION_EVENTS = {
    "APPROVE": NotificationEventType.ASSURANCE_APPROVED,
    "REJECT_FINAL": NotificationEventType.ASSURANCE_REJECTED,
    "REQUEST_REVISION": NotificationEventType.REVISION_REQUESTED,
    "REJECT": NotificationEventType.REVISION_REQUESTED,
}


def next_assurance_number(year):
    sequence, _ = AssuranceNumberSequence.objects.select_for_update().get_or_create(
        year=year, defaults={"last_value": lambda: existing_number_maximum(year)},
    )
    sequence.last_value += 1
    sequence.save(update_fields=["last_value"])
    return f"KAS-{year}-{sequence.last_value:05d}"


def existing_number_maximum(year):
    prefix = f"KAS-{year}-"
    numbers = VehicleAssurance.objects.filter(
        assurance_number__startswith=prefix,
    ).values_list("assurance_number", flat=True)
    return max((int(number[len(prefix):]) for number in numbers
                if number[len(prefix):].isdigit()), default=0)


@transaction.atomic
def submit_assurance_application(assurance, user):
    assurance = get_locked_assurance(assurance.pk)
    require_mutation_access(assurance, user)
    require_editable(assurance)
    validate_submission_data(assurance)
    previous_status = assurance.status
    assurance.status = AssuranceStatus.SUBMITTED
    assurance.verification_stage = "WAITING"
    assurance.data_verified = assurance.documents_verified = False
    assurance.save(update_fields=["status", "verification_stage", "data_verified",
                                  "documents_verified", "updated_at"])
    append_review_event(assurance, user, "SUBMIT")
    audit = record_audit(user, "SUBMIT", "VEHICLE_ASSURANCE", assurance.pk, {
        "status": {"old": previous_status, "new": assurance.status},
    })
    dispatch_assurance_notifications(
        assurance=assurance,
        actor=user,
        event_type=NotificationEventType.ASSURANCE_SUBMITTED,
        dedupe_key=f"submit:{assurance.pk}:{audit.pk}",
    )
    return assurance


@transaction.atomic
def review_assurance(assurance, user, data):
    if not (user.is_active and user.is_admin_user):
        raise PermissionDenied("Only Admin or Super Admin may review assurances.")
    serializer = ReviewAssuranceSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    decision = serializer.validated_data["decision"]
    notes = serializer.validated_data["review_notes"]
    assurance = get_locked_assurance(assurance.pk)
    if assurance.status != AssuranceStatus.SUBMITTED:
        raise ValidationError("Only SUBMITTED assurances may be reviewed.")
    if decision == "APPROVE":
        validate_submission_data(assurance)
        assurance.assurance_number = next_assurance_number(assurance.issuance_year)
        assurance.status = AssuranceStatus.ACTIVE
        assurance.data_verified = assurance.documents_verified = True
        assurance.verification_stage = "COMPLETE"
    elif decision == "REJECT_FINAL":
        assurance.status = AssuranceStatus.REJECTED
    else:
        assurance.status = AssuranceStatus.REVISION
    assurance.review_notes = notes
    assurance.reviewed_by = user
    assurance.save(update_fields=["status", "assurance_number", "review_notes",
                                  "reviewed_by", "verification_stage", "data_verified",
                                  "documents_verified", "updated_at"])
    append_review_event(assurance, user, decision, notes=notes)
    audit = record_audit(user, decision, "VEHICLE_ASSURANCE", assurance.pk, {
        "status": {"old": AssuranceStatus.SUBMITTED, "new": assurance.status},
        "review_notes_present": bool(notes), "assurance_number": assurance.assurance_number,
    })
    notif_event = _REVIEW_NOTIFICATION_EVENTS.get(decision)
    if notif_event:
        dispatch_assurance_notifications(
            assurance=assurance,
            actor=user,
            event_type=notif_event,
            dedupe_key=f"review:{assurance.pk}:{audit.pk}",
        )
    return assurance
