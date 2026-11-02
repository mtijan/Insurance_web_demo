from django.db.models import QuerySet
from apps.documents.models import AssuranceDocument
from apps.users.models import CustomUser


def get_documents_for_assurance(user: CustomUser, assurance_id) -> QuerySet[AssuranceDocument]:
    """
    Returns documents for a given assurance if the user is authorized.
    """
    if not (user and user.is_authenticated):
        return AssuranceDocument.objects.none()

    if user.is_super_admin or user.is_admin_user:
        return AssuranceDocument.objects.filter(assurance_id=assurance_id)

    if user.is_agent:
        return AssuranceDocument.objects.filter(
            assurance_id=assurance_id,
            assurance__dealer__agent_assignments__agent=user
        )

    if user.is_dealer:
        return AssuranceDocument.objects.filter(
            assurance_id=assurance_id,
            assurance__dealer_id=user.dealer_id
        )

    return AssuranceDocument.objects.none()
