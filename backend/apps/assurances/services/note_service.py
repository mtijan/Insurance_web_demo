from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from apps.assurances.models import AssuranceNote, VehicleAssurance
from apps.assurances.note_serializers import AssuranceNoteCreateSerializer
from apps.assurances.services.workflow_validation import get_locked_assurance
from apps.audit.services.audit_service import record_audit
from apps.notifications.models import NotificationEventType
from apps.notifications.services.notification_service import dispatch_assurance_notifications
from apps.users.models import CustomUser


def list_assurance_notes(assurance: VehicleAssurance):
    """Return assurance notes ordered chronologically for scoped participants."""
    return AssuranceNote.objects.filter(assurance=assurance).order_by("created_at", "id")


def require_note_write_access(assurance: VehicleAssurance, user: CustomUser) -> None:
    """Enforce server-side role, dealer assignment, and active-dealer controls."""
    if not (user and user.is_authenticated and user.is_active):
        raise PermissionDenied("Inactive account.")
    if user.is_admin_user:
        return
    if not assurance.dealer.is_active:
        raise PermissionDenied("Dealer is inactive.")
    dealer_match = user.is_dealer and user.dealer_id == assurance.dealer_id
    agent_match = user.is_agent and user.dealer_assignments.filter(
        dealer_id=assurance.dealer_id,
    ).exists()
    if not (dealer_match or agent_match):
        raise PermissionDenied("User does not have note access for this assurance.")


@transaction.atomic
def create_assurance_note(assurance: VehicleAssurance, user: CustomUser, data) -> AssuranceNote:
    """Persist a shared note, append non-PII audit log, and enqueue in-app notifications."""
    locked = get_locked_assurance(assurance.pk)
    require_note_write_access(locked, user)
    serializer = AssuranceNoteCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    note = AssuranceNote.objects.create(
        assurance=locked,
        author=user,
        author_role=user.role,
        author_username=user.username,
        message=serializer.validated_data["message"],
    )
    record_audit(
        user,
        "NOTE_CREATE",
        "ASSURANCE_NOTE",
        note.pk,
        {
            "assurance_id": str(locked.pk),
            "author_role": user.role,
            "length": len(note.message),
        },
    )
    dispatch_assurance_notifications(
        assurance=locked,
        actor=user,
        event_type=NotificationEventType.ASSURANCE_NOTE,
        dedupe_key=f"note:{note.pk}",
    )
    return note
