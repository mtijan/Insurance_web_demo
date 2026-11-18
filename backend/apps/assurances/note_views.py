from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.assurances.note_serializers import AssuranceNoteSerializer
from apps.assurances.services.note_service import create_assurance_note, list_assurance_notes


class AssuranceNotePermission(BasePermission):
    """Scoped participant authorization for reading and posting shared assurance notes."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_active)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if not (user and user.is_authenticated and user.is_active):
            return False
        if user.is_admin_user:
            return True
        in_scope = (
            (user.is_dealer and str(obj.dealer_id) == str(user.dealer_id))
            or (user.is_agent and obj.dealer.agent_assignments.filter(agent=user).exists())
        )
        if not in_scope:
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(obj.dealer.is_active)


class AssuranceNoteMixin:
    """ViewSet actions exposing collaborative assurance notes."""

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="notes",
        permission_classes=[IsAuthenticated, AssuranceNotePermission],
    )
    def notes(self, request, pk=None):
        assurance = self.get_object()
        if request.method == "GET":
            items = list_assurance_notes(assurance)
            return Response({"success": True, "data": AssuranceNoteSerializer(items, many=True).data})
        note = create_assurance_note(assurance, request.user, request.data)
        return Response(
            {
                "success": True,
                "message": "Catatan berhasil ditambahkan.",
                "data": AssuranceNoteSerializer(note).data,
            },
            status=status.HTTP_201_CREATED,
        )
