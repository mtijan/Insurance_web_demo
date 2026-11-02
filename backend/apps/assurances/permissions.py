from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.assurances.models import AssuranceStatus


class AssuranceAccessPermission(BasePermission):
    """
    Object-level permission checking data visibility and mutation rules:
    - Read: Super Admin, Admin, assigned Agent, and owner Dealer.
    - Write/Edit: Super Admin, Admin, or the creator (while in DRAFT / REVISION).
    """
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if not (user and user.is_authenticated):
            return False

        if user.is_super_admin or user.is_admin_user:
            return True

        if request.method in SAFE_METHODS:
            return self.has_dealer_scope(user, obj)

        # Mutation: only allowed for creator in DRAFT or REVISION
        if obj.status not in (AssuranceStatus.DRAFT, AssuranceStatus.REVISION):
            return False

        if obj.created_by_id != user.id:
            return False

        return self.has_dealer_scope(user, obj)

    def has_dealer_scope(self, user, obj):
        if user.is_dealer:
            return str(obj.dealer_id) == str(user.dealer_id)
        if user.is_agent:
            return obj.dealer.agent_assignments.filter(agent=user).exists()

        return False
