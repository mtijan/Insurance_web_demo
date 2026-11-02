from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services.audit_service import record_audit
from apps.users.models import CustomUser, UserRole


def validate_user(user, password=None):
    if user.role == UserRole.DEALER and not user.dealer_id:
        raise ValidationError({"dealer": "A dealer account must be associated with a dealer."})
    if user.dealer_assignments.exists() and user.role != UserRole.AGENT:
        raise ValidationError({"role": "Remove agent assignments before changing this role."})
    if CustomUser.objects.exclude(pk=user.pk).filter(email__iexact=user.email).exists():
        raise ValidationError({"email": "This email is already registered."})
    try:
        user.full_clean(exclude=["password", "last_login", "date_joined"])
        if password is not None:
            validate_password(password, user=user)
    except ModelValidationError as exc:
        raise ValidationError(getattr(exc, "message_dict", {"password": exc.messages})) from exc


def apply_fields(user, data):
    for name, value in data.items():
        if name != "password":
            setattr(user, name, value)
    validate_user(user, data.get("password"))
    if "password" in data:
        user.set_password(data["password"])


def save_user(user):
    try:
        with transaction.atomic():
            user.save()
    except IntegrityError as exc:
        raise ValidationError("User identity conflicts with an existing account.") from exc


@transaction.atomic
def create_user(actor, data):
    user = CustomUser()
    user.set_unusable_password()
    apply_fields(user, data)
    save_user(user)
    record_audit(actor, "CREATE", "CUSTOM_USER", user.pk,
                 {"role": user.role, "is_active": user.is_active,
                  "dealer_id": str(user.dealer_id) if user.dealer_id else None})
    return user


@transaction.atomic
def update_user(actor, user, data):
    user = CustomUser.objects.select_for_update().get(pk=user.pk)
    before = {name: getattr(user, name) for name in ("role", "is_active")}
    old_dealer = str(user.dealer_id) if user.dealer_id else None
    apply_fields(user, data)
    save_user(user)
    changes = {name: {"old": old, "new": getattr(user, name)} for name, old in before.items()}
    changes["dealer_id"] = {"old": old_dealer,
                            "new": str(user.dealer_id) if user.dealer_id else None}
    changes["fields"] = sorted(set(data) - {"password"})
    if "password" in data:
        changes["password_changed"] = True
    if "password" in data or not user.is_active:
        user.auth_sessions.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())
    record_audit(actor, "UPDATE", "CUSTOM_USER", user.pk, changes)
    return user


@transaction.atomic
def delete_user(actor, user):
    from apps.dealers.services.dealer_service import audit_assignment_deletions

    user = CustomUser.objects.select_for_update().get(pk=user.pk)
    identity = user.pk
    audit_assignment_deletions(actor, user.dealer_assignments.all())
    record_audit(actor, "DELETE", "CUSTOM_USER", identity)
    try:
        user.delete()
    except ProtectedError as exc:
        raise ValidationError("User has transaction history. Deactivate the account instead.") from exc
