from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.selectors.notification_selector import (
    get_notifications_for_user,
    get_unread_count_for_user,
)
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.services.read_service import (
    mark_all_notifications_read,
    mark_notification_read,
)

DEFAULT_LIMIT = 20
MAX_LIMIT = 50


def _parse_limit(raw_limit: str | None) -> int:
    if not raw_limit:
        return DEFAULT_LIMIT
    try:
        value = int(raw_limit)
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return max(1, min(value, MAX_LIMIT))


class NotificationListView(APIView):
    """List in-app notifications scoped to the authenticated active user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_only = str(request.query_params.get("unread_only", "")).lower() == "true"
        limit = _parse_limit(request.query_params.get("limit"))
        items = list(get_notifications_for_user(request.user, unread_only=unread_only)[:limit])
        serializer = NotificationSerializer(items, many=True)
        return Response(
            {
                "success": True,
                "data": {
                    "unread_count": get_unread_count_for_user(request.user),
                    "items": serializer.data,
                },
            },
            status=status.HTTP_200_OK,
        )


class NotificationReadView(APIView):
    """Mark a single notification belonging to the current user as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        item, unread_count = mark_notification_read(request.user, pk)
        return Response(
            {
                "success": True,
                "message": "Notification marked as read.",
                "data": {
                    "item": NotificationSerializer(item).data,
                    "unread_count": unread_count,
                },
            },
            status=status.HTTP_200_OK,
        )


class NotificationReadAllView(APIView):
    """Mark all unread notifications belonging to the current user as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        marked_count = mark_all_notifications_read(request.user)
        return Response(
            {
                "success": True,
                "message": "All notifications marked as read.",
                "data": {
                    "marked_count": marked_count,
                    "unread_count": 0,
                },
            },
            status=status.HTTP_200_OK,
        )
