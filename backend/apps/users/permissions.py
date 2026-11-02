from rest_framework.permissions import BasePermission
from .models import UserRole


class IsSuperAdmin(BasePermission):
    """
    Allows access only to Super Admins.
    """
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_super_admin
        )


class IsAdminUserOrReadOnly(BasePermission):
    """
    Allows access to Admin and Super Admin for modifications, read-only for others.
    """
    def has_permission(self, request, view) -> bool:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_admin_user
        )


class IsAdmin(BasePermission):
    """
    Allows access to Underwriting Admins and Super Admins.
    """
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_admin_user
        )


class IsAgent(BasePermission):
    """
    Allows access only to Agents.
    """
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_agent
        )


class IsDealer(BasePermission):
    """
    Allows access only to Dealer staff.
    """
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_dealer
        )
