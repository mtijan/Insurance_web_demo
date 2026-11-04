from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.assurances.models import AssuranceReviewEvent, AssuranceStatus, VehicleAssurance
from apps.assurances.workflow_serializers import InspectionSerializer
from apps.audit.services.audit_service import record_audit


def require_inspection_access(assurance, user):
    if not user.is_active:
        raise PermissionDenied("Inactive account.")
    if user.is_admin_user:
        return
    if not (user.is_agent and user.dealer_assignments.filter(dealer_id=assurance.dealer_id).exists()):
        raise PermissionDenied("Only assigned Agent, Admin or Super Admin may inspect.")


def append_review_event(assurance, user, action, section="GENERAL", notes=""):
    AssuranceReviewEvent.objects.create(assurance=assurance, actor=user, actor_role=user.role,
                                        action=action, section=section, review_notes=notes)


def apply_verification(assurance, action, section):
    if section == "DOCUMENTS" and not assurance.data_verified:
        raise ValidationError("Verify data before inspecting documents.")
    if action == "START":
        if (section == "DATA" and assurance.data_verified) or assurance.documents_verified:
            raise ValidationError("This section has already been verified.")
        assurance.verification_stage = section
    elif section == "DATA":
        assurance.data_verified = True
        assurance.verification_stage = "COMPLETE" if assurance.documents_verified else "DOCUMENTS"
    else:
        from apps.assurances.services.workflow_validation import validate_submission_data
        validate_submission_data(assurance)
        assurance.documents_verified = True
        assurance.verification_stage = "COMPLETE"


@transaction.atomic
def inspect_assurance(assurance, user, data):
    assurance = VehicleAssurance.objects.select_for_update().get(pk=assurance.pk)
    require_inspection_access(assurance, user)
    serializer = InspectionSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    action, section, notes = (serializer.validated_data[key]
                              for key in ("action", "section", "review_notes"))
    if assurance.status != AssuranceStatus.SUBMITTED:
        raise ValidationError("Only SUBMITTED assurances may be inspected.")
    if action in ("START", "VERIFY"):
        if not user.is_admin_user:
            raise PermissionDenied("Only Admin or Super Admin may verify data/documents.")
        apply_verification(assurance, action, section)
    if action == "REQUEST_REVISION":
        assurance.status = AssuranceStatus.REVISION
        assurance.review_notes = notes
        assurance.reviewed_by = user
    assurance.save(update_fields=["verification_stage", "data_verified", "documents_verified",
                                  "status", "review_notes", "reviewed_by", "updated_at"])
    append_review_event(assurance, user, action, section, notes)
    record_audit(user, "INSPECT", "VEHICLE_ASSURANCE", assurance.pk, {
        "action": action, "section": section, "status": assurance.status,
        "review_notes_present": bool(notes),
    })
    return assurance
