from datetime import datetime, timezone as datetime_timezone

from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.services.audit_service import record_audit
from apps.users.authentication import require_session
from apps.users.models import AuthSession, CustomUser


def authenticate_identity(identity, password):
    candidates = list(CustomUser.objects.filter(
        Q(username=identity) | Q(email__iexact=identity),
    )[:2])
    if len(candidates) != 1:
        CustomUser().set_password(password)
        raise ValidationError("Invalid login credentials.")
    user = authenticate(username=candidates[0].username, password=password)
    if user is None:
        raise ValidationError("Invalid login credentials.")
    return user


@transaction.atomic
def issue_session(user):
    current = CustomUser.objects.select_for_update().get(pk=user.pk)
    if not current.is_active or current.password != user.password:
        raise AuthenticationFailed("Account changed. Please log in again.")
    user = current
    refresh = RefreshToken.for_user(user)
    session = AuthSession.objects.create(
        user=user, expires_at=datetime.fromtimestamp(refresh["exp"], datetime_timezone.utc),
    )
    refresh["sid"] = str(session.pk)
    record_audit(user, "LOGIN", "CUSTOM_USER", user.pk)
    return str(refresh.access_token), str(refresh)


@transaction.atomic
def revoke_session(user, token):
    session = require_session(token, user.pk)
    session = AuthSession.objects.select_for_update().get(pk=session.pk)
    session.revoked_at = timezone.now()
    session.save(update_fields=["revoked_at"])
    record_audit(user, "LOGOUT", "CUSTOM_USER", user.pk)


def refresh_access(raw):
    if not isinstance(raw, str) or not raw:
        raise AuthenticationFailed("Invalid refresh token.")
    try:
        refresh = RefreshToken(raw)
        session = require_session(refresh, refresh["user_id"])
    except (TokenError, KeyError) as exc:
        raise AuthenticationFailed("Invalid refresh token.") from exc
    if not session.user.is_active:
        raise AuthenticationFailed("Inactive account.")
    return str(refresh.access_token)
