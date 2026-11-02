from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from apps.assurances.models import AssuranceStatus, VehicleCategory
from apps.documents.services.document_validator import validate_document_completeness
from apps.documents.services.vault_paths import available_document_types


class IncompleteDocuments(APIException):
    status_code = 422

    def __init__(self, missing):
        super().__init__({
            "success": False, "error_code": "INCOMPLETE_DOCUMENTS",
            "message": "Cannot submit assurance. Required documents are missing.",
            "missing_documents": missing,
        })
        self.detail["success"] = False


def require_mutation_access(assurance, user):
    if not user.is_active:
        raise PermissionDenied("Inactive account.")
    if user.is_admin_user:
        return
    is_owner = assurance.created_by_id == user.id
    dealer_access = user.is_dealer and assurance.dealer_id == user.dealer_id
    agent_access = user.is_agent and user.dealer_assignments.filter(
        dealer_id=assurance.dealer_id,
    ).exists()
    if not (is_owner and (dealer_access or agent_access)):
        raise PermissionDenied("Only the creator or Admin may change this assurance.")


def require_editable(assurance):
    if assurance.status not in (AssuranceStatus.DRAFT, AssuranceStatus.REVISION):
        raise ValidationError("Only DRAFT or REVISION assurances may be changed.")


def validate_submission_data(assurance):
    try:
        assurance.policy_holder.full_clean()
        assurance.full_clean()
    except ModelValidationError as exc:
        raise ValidationError(exc.message_dict) from exc
    if assurance.vehicle_category not in VehicleCategory.values:
        raise ValidationError("Invalid vehicle category.")
    validate_financial_fields(assurance)
    uploaded = available_document_types(assurance)
    complete, missing = validate_document_completeness(assurance.vehicle_category, uploaded)
    if not complete:
        raise IncompleteDocuments(missing)


def validate_financial_fields(assurance):
    if assurance.sum_insured <= 0 or not 1 <= assurance.tenor_years <= 5:
        raise ValidationError("Invalid sum insured or tenor.")
    if assurance.period_end <= assurance.period_start or assurance.total_premium <= 0:
        raise ValidationError("Invalid coverage period or premium.")
    if assurance.admin_fee < 0 or assurance.base_premium < 0:
        raise ValidationError("Premium and admin fee cannot be negative.")
    if assurance.total_premium != assurance.base_premium + assurance.admin_fee:
        raise ValidationError("Premium total is inconsistent.")
