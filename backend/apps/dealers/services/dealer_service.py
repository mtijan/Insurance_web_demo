from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit.services.audit_service import record_audit
from apps.dealers.models import Dealer, AgentDealerAssignment
from apps.users.models import AuthSession, CustomUser, UserRole


def require_dealer_actor(actor):
    if actor is not None and not (actor.is_active and actor.is_super_admin):
        raise PermissionDenied("Only active Super Admin may manage dealers.")


def revoke_inactive_dealer_sessions(dealer):
    AuthSession.objects.filter(
        revoked_at__isnull=True, user__role=UserRole.DEALER, user__dealer=dealer,
    ).update(revoked_at=timezone.now())


def clean_and_save(instance):
    try:
        instance.full_clean()
        with transaction.atomic():
            instance.save()
    except ModelValidationError as exc:
        raise ValidationError(exc.message_dict) from exc
    except IntegrityError as exc:
        raise ValidationError("Conflicting master data.") from exc
    return instance


@transaction.atomic
def create_dealer(validated_data, actor=None):
    require_dealer_actor(actor)
    dealer = clean_and_save(Dealer(**validated_data))
    record_audit(actor, "CREATE", "DEALER", dealer.pk,
                 {"fields": sorted(validated_data), "is_active": dealer.is_active})
    return dealer


@transaction.atomic
def update_dealer(dealer, validated_data, actor=None):
    require_dealer_actor(actor)
    dealer = Dealer.objects.select_for_update().get(pk=dealer.pk)
    old_active = dealer.is_active
    for field, value in validated_data.items():
        setattr(dealer, field, value)
    clean_and_save(dealer)
    if old_active and not dealer.is_active:
        revoke_inactive_dealer_sessions(dealer)
    record_audit(actor, "UPDATE", "DEALER", dealer.pk, {
        "fields": sorted(validated_data), "is_active": {"old": old_active, "new": dealer.is_active},
    })
    return dealer


def audit_assignment_deletions(actor, assignments):
    for assignment in assignments:
        record_audit(actor, "DELETE", "AGENT_DEALER_ASSIGNMENT", assignment.pk,
                     {"agent_id": str(assignment.agent_id), "dealer_id": str(assignment.dealer_id)})


@transaction.atomic
def delete_dealer(dealer, actor):
    require_dealer_actor(actor)
    dealer = Dealer.objects.select_for_update().get(pk=dealer.pk)
    identity = dealer.pk
    audit_assignment_deletions(actor, dealer.agent_assignments.all())
    try:
        dealer.delete()
    except ProtectedError as exc:
        raise ValidationError("Dealer has users or transaction history. Deactivate it instead.") from exc
    record_audit(actor, "DELETE", "DEALER", identity)


def require_agent(agent):
    if agent.role != UserRole.AGENT:
        raise ValidationError({"agent": "Assigned user must have AGENT role."})


@transaction.atomic
def assign_agent_to_dealer(agent, dealer, actor=None):
    require_dealer_actor(actor)
    agent = CustomUser.objects.select_for_update().get(pk=agent.pk)
    require_agent(agent)
    assignment = clean_and_save(AgentDealerAssignment(agent=agent, dealer=dealer))
    record_audit(actor, "CREATE", "AGENT_DEALER_ASSIGNMENT", assignment.pk,
                 {"agent_id": str(agent.pk), "dealer_id": str(dealer.pk)})
    return assignment


@transaction.atomic
def update_assignment(assignment, data, actor=None):
    require_dealer_actor(actor)
    assignment = AgentDealerAssignment.objects.select_for_update().get(pk=assignment.pk)
    previous = {name: str(getattr(assignment, name)) for name in ("agent_id", "dealer_id")}
    agent = data.get("agent", assignment.agent)
    agent = CustomUser.objects.select_for_update().get(pk=agent.pk)
    require_agent(agent)
    assignment.agent = agent
    assignment.dealer = data.get("dealer", assignment.dealer)
    clean_and_save(assignment)
    record_audit(actor, "UPDATE", "AGENT_DEALER_ASSIGNMENT", assignment.pk, {
        "old": previous, "new": {"agent_id": str(agent.pk), "dealer_id": str(assignment.dealer_id)},
    })
    return assignment


@transaction.atomic
def delete_assignment(assignment, actor=None):
    require_dealer_actor(actor)
    assignment = AgentDealerAssignment.objects.select_for_update().get(pk=assignment.pk)
    audit_assignment_deletions(actor, [assignment])
    assignment.delete()


@transaction.atomic
def remove_agent_from_dealer(agent, dealer, actor=None):
    assignment = AgentDealerAssignment.objects.filter(agent=agent, dealer=dealer).first()
    if assignment is None:
        return False
    delete_assignment(assignment, actor)
    return True
