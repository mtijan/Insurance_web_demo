from django.db.models import QuerySet

from apps.notifications.models import Notification
from apps.users.models import CustomUser


def get_notifications_for_user(user: CustomUser, *, unread_only: bool = False) -> QuerySet[Notification]:
    """Return notifications owned exclusively by the authenticated active user."""
    if not (user and user.is_authenticated and user.is_active):
        return Notification.objects.none()
    queryset = Notification.objects.filter(recipient=user).order_by("-created_at", "-id")
    if unread_only:
        queryset = queryset.filter(read_at__isnull=True)
    return queryset


def get_unread_count_for_user(user: CustomUser) -> int:
    """Return total unread notification count for the authenticated active user."""
    if not (user and user.is_authenticated and user.is_active):
        return 0
    return Notification.objects.filter(recipient=user, read_at__isnull=True).count()
