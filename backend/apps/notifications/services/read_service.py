from uuid import UUID

from django.db import transaction
from django.http import Http404
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.selectors.notification_selector import get_unread_count_for_user
from apps.users.models import CustomUser


def _parse_notification_uuid(notification_id: str) -> UUID:
    try:
        return UUID(str(notification_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise Http404("Notification not found.") from exc


@transaction.atomic
def mark_notification_read(user: CustomUser, notification_id: str) -> tuple[Notification, int]:
    """Mark one user-owned notification as read idempotently and return updated unread count."""
    parsed_id = _parse_notification_uuid(notification_id)
    try:
        item = Notification.objects.select_for_update().get(pk=parsed_id, recipient=user)
    except Notification.DoesNotExist as exc:
        raise Http404("Notification not found.") from exc
    if item.read_at is None:
        item.read_at = timezone.now()
        item.save(update_fields=["read_at"])
    return item, get_unread_count_for_user(user)


@transaction.atomic
def mark_all_notifications_read(user: CustomUser) -> int:
    """Mark all unread notifications owned by user as read and return updated row count."""
    now = timezone.now()
    return Notification.objects.filter(recipient=user, read_at__isnull=True).update(read_at=now)
