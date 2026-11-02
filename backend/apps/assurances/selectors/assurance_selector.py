from django.db.models import QuerySet
from apps.assurances.models import VehicleAssurance
from apps.users.models import CustomUser


def get_assurances_for_user(user: CustomUser) -> QuerySet[VehicleAssurance]:
    """
    Returns scoped VehicleAssurance queryset based on user role:
    - Super Admin & Admin: all assurances across all dealers.
    - Agent: assurances belonging to assigned dealers.
    - Dealer: assurances belonging to own dealer branch.
    - Others/unauthenticated: empty queryset.
    """
    if not (user and user.is_authenticated):
        return VehicleAssurance.objects.none()

    base_qs = VehicleAssurance.objects.select_related(
        "policy_holder",
        "dealer",
        "created_by",
        "reviewed_by"
    ).prefetch_related("documents")

    if user.is_super_admin or user.is_admin_user:
        return base_qs.all()

    if user.is_agent:
        return base_qs.filter(dealer__agent_assignments__agent=user).distinct()

    if user.is_dealer:
        if user.dealer_id:
            return base_qs.filter(dealer_id=user.dealer_id)
        return VehicleAssurance.objects.none()

    return VehicleAssurance.objects.none()
