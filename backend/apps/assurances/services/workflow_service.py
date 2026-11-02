from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.assurances.models import (
    AssuranceNumberSequence, AssuranceStatus, VehicleAssurance,
)
from apps.assurances.services.workflow_validation import (
    require_editable, require_mutation_access, validate_submission_data,
)
from apps.assurances.workflow_serializers import ReviewAssuranceSerializer
from apps.audit.services.audit_service import record_audit


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
    assurance = VehicleAssurance.objects.select_for_update().get(pk=assurance.pk)
    require_mutation_access(assurance, user)
    require_editable(assurance)
    validate_submission_data(assurance)
    previous_status = assurance.status
    assurance.status = AssuranceStatus.SUBMITTED
    assurance.save(update_fields=["status", "updated_at"])
    record_audit(user, "SUBMIT", "VEHICLE_ASSURANCE", assurance.pk, {
        "status": {"old": previous_status, "new": assurance.status},
    })
    return assurance


@transaction.atomic
def review_assurance(assurance, user, data):
    if not (user.is_active and user.is_admin_user):
        raise PermissionDenied("Only Admin or Super Admin may review assurances.")
    serializer = ReviewAssuranceSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    decision = serializer.validated_data["decision"]
    notes = serializer.validated_data["review_notes"]
    assurance = VehicleAssurance.objects.select_for_update().get(pk=assurance.pk)
    if assurance.status != AssuranceStatus.SUBMITTED:
        raise ValidationError("Only SUBMITTED assurances may be reviewed.")
    if decision == "APPROVE":
        validate_submission_data(assurance)
        assurance.assurance_number = next_assurance_number(assurance.issuance_year)
        assurance.status = AssuranceStatus.ACTIVE
    else:
        assurance.status = AssuranceStatus.REVISION
    assurance.review_notes = notes
    assurance.reviewed_by = user
    assurance.save(update_fields=["status", "assurance_number", "review_notes",
                                  "reviewed_by", "updated_at"])
    record_audit(user, decision, "VEHICLE_ASSURANCE", assurance.pk, {
        "status": {"old": AssuranceStatus.SUBMITTED, "new": assurance.status},
        "review_notes_present": bool(notes), "assurance_number": assurance.assurance_number,
    })
    return assurance
