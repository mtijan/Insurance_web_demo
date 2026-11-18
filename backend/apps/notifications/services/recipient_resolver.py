from apps.assurances.models import AssuranceNote, VehicleAssurance
from apps.dealers.models import AgentDealerAssignment
from apps.notifications.models import NotificationEventType
from apps.users.models import CustomUser, UserRole


def _active_dealer_staff_ids(assurance: VehicleAssurance) -> set:
    if not assurance.dealer.is_active:
        return set()
    return set(
        CustomUser.objects.filter(
            role=UserRole.DEALER,
            dealer_id=assurance.dealer_id,
            is_active=True,
        ).values_list("id", flat=True)
    )


def _assigned_agent_ids(assurance: VehicleAssurance) -> set:
    return set(
        AgentDealerAssignment.objects.filter(
            dealer_id=assurance.dealer_id,
            agent__role=UserRole.AGENT,
            agent__is_active=True,
        ).values_list("agent_id", flat=True)
    )


def _scoped_creator_id(assurance: VehicleAssurance) -> set:
    creator = assurance.created_by
    if not (creator and creator.is_active):
        return set()
    if creator.is_admin_user:
        return {creator.id}
    if creator.is_dealer:
        return {creator.id} if (assurance.dealer.is_active and creator.dealer_id == assurance.dealer_id) else set()
    if creator.is_agent and creator.dealer_assignments.filter(dealer_id=assurance.dealer_id).exists():
        return {creator.id}
    return set()


def _all_active_admin_ids() -> set:
    return set(
        CustomUser.objects.filter(role=UserRole.ADMIN, is_active=True).values_list("id", flat=True)
    )


def _note_admin_ids(assurance: VehicleAssurance) -> set:
    involved = set(
        AssuranceNote.objects.filter(
            assurance=assurance,
            author__role=UserRole.ADMIN,
            author__is_active=True,
        ).values_list("author_id", flat=True)
    )
    reviewer = assurance.reviewed_by
    if reviewer and reviewer.is_active and reviewer.role == UserRole.ADMIN:
        involved.add(reviewer.id)
    return involved or _all_active_admin_ids()


def _super_admin_ids() -> set:
    return set(
        CustomUser.objects.filter(role=UserRole.SUPER_ADMIN, is_active=True).values_list("id", flat=True)
    )


def resolve_assurance_recipients(
    assurance: VehicleAssurance,
    actor: CustomUser | None,
    event_type: str,
) -> list:
    """Resolve active, authorized recipient IDs without self-notification or cross-tenant leakage."""
    recipients = _super_admin_ids()
    if event_type == NotificationEventType.ASSURANCE_SUBMITTED:
        recipients |= _assigned_agent_ids(assurance) | _all_active_admin_ids()
    elif event_type == NotificationEventType.ASSURANCE_NOTE:
        recipients |= (
            _active_dealer_staff_ids(assurance)
            | _assigned_agent_ids(assurance)
            | _scoped_creator_id(assurance)
            | _note_admin_ids(assurance)
        )
    else:
        recipients |= _active_dealer_staff_ids(assurance) | _assigned_agent_ids(assurance) | _scoped_creator_id(assurance)
        if event_type == NotificationEventType.REVISION_REQUESTED and actor and actor.is_agent:
            recipients |= _all_active_admin_ids()
    if actor and actor.id:
        recipients.discard(actor.id)
    return list(recipients)
