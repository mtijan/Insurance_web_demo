"""Self-service password rotation; never accepts a target account from clients."""
from django.contrib.auth.password_validation import validate_password, password_changed
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services.audit_service import record_audit
from apps.users.authentication import require_session
from apps.users.models import CustomUser


@transaction.atomic
def change_own_password(user, token, current_password, new_password):
    user = CustomUser.objects.select_for_update().get(pk=user.pk)
    require_session(token, user.pk)
    if not user.is_active or not user.check_password(current_password):
        raise ValidationError({"current_password": "Current password is incorrect."})
    if user.check_password(new_password):
        raise ValidationError({"new_password": "Choose a different password."})
    try:
        validate_password(new_password, user=user)
    except ModelValidationError as exc:
        raise ValidationError({"new_password": exc.messages}) from exc
    user.set_password(new_password)
    user.must_change_password = False
    user.save(update_fields=["password", "must_change_password", "updated_at"])
    user.auth_sessions.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())
    record_audit(user, "PASSWORD_CHANGE", "CUSTOM_USER", user.pk, {"password_changed": True})
    password_changed(new_password, user=user)
