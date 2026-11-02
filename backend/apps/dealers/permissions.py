from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperAdminOrReadOnly(BasePermission):
    """
    Allows Super Admin full access, other authenticated users read-only access.
    """
    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user.is_super_admin)


class DealerAccessPermission(BasePermission):
    """
    Controls read and write permissions for Dealer objects based on role:
    - Super Admin: Full CRUD.
    - Admin (Underwriter): Read all dealers.
    - Dealer: Read only their own dealer branch.
    - Agent: Read only dealers assigned to them.
    - Non-Super Admin cannot create, update, or delete dealers.
    """
    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user.is_super_admin)

    def has_object_permission(self, request, view, obj) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method not in SAFE_METHODS:
            return bool(request.user.is_super_admin)

        if request.user.is_super_admin or request.user.is_admin_user:
            return True

        if request.user.is_dealer:
            return str(obj.id) == str(request.user.dealer_id)

        if request.user.is_agent:
            return obj.agent_assignments.filter(agent=request.user).exists()

        return False


class AssignmentAccessPermission(BasePermission):
    """
    Controls access to AgentDealerAssignment:
    - Super Admin: Full CRUD.
    - Agent: Read only their own assignments.
    - Others: No access.
    """
    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_super_admin:
            return True
        if request.method in SAFE_METHODS and request.user.is_agent:
            return True
        return False

    def has_object_permission(self, request, view, obj) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_super_admin:
            return True
        if request.method in SAFE_METHODS and request.user.is_agent:
            return obj.agent_id == request.user.id
        return False
