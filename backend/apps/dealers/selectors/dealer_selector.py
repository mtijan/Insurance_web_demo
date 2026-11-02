from django.db.models import QuerySet
from apps.dealers.models import Dealer, AgentDealerAssignment
from apps.users.models import CustomUser


def get_dealers_for_user(user: CustomUser, active_only: bool = False) -> QuerySet[Dealer]:
    """
    Retrieve dealers visible to the given user based on RBAC rules:
    - Super Admin & Admin: all dealers.
    - Agent: dealers assigned to the agent.
    - Dealer: only the dealer linked to the user account.
    - Other/unauthenticated: empty queryset.
    """
    if not (user and user.is_authenticated):
        return Dealer.objects.none()

    if user.is_super_admin or user.is_admin_user:
        queryset = Dealer.objects.all()
    elif user.is_agent:
        queryset = Dealer.objects.filter(agent_assignments__agent=user)
    elif user.is_dealer:
        if user.dealer_id:
            queryset = Dealer.objects.filter(id=user.dealer_id)
        else:
            queryset = Dealer.objects.none()
    else:
        queryset = Dealer.objects.none()

    if active_only:
        queryset = queryset.filter(is_active=True)

    return queryset.distinct()


def get_assignments_for_user(user: CustomUser) -> QuerySet[AgentDealerAssignment]:
    """
    Retrieve agent dealer assignments visible to the user:
    - Super Admin: all assignments with prefetched relationships.
    - Agent: assignments belonging to the agent.
    - Others: empty queryset.
    """
    if not (user and user.is_authenticated):
        return AgentDealerAssignment.objects.none()

    base_qs = AgentDealerAssignment.objects.select_related("agent", "dealer")
    if user.is_super_admin:
        return base_qs.all()
    if user.is_agent:
        return base_qs.filter(agent=user)
    return AgentDealerAssignment.objects.none()
