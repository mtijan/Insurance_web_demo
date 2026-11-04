"""JWT transport with server revocation and CSRF enforcement for cookies."""
from django.middleware.csrf import CsrfViewMiddleware
from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone

from apps.users.models import AuthSession
from apps.users.csrf import CsrfRejected


class CsrfCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return reason


class PasswordChangeRequired(PermissionDenied):
    default_detail = "Change your password before accessing business features."
    default_code = "password_change_required"


def enforce_password_state(user, request):
    allowed = {"auth-me", "auth-logout", "auth-change-password"}
    match = request.resolver_match
    if user.must_change_password and (match is None or match.url_name not in allowed):
        raise PasswordChangeRequired()


def enforce_csrf(request):
    check = CsrfCheck(lambda request: None)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise CsrfRejected(reason)


def require_session(token, user_id):
    session_id = token.get("sid")
    if not session_id:
        raise AuthenticationFailed("Session expired. Please log in again.")
    try:
        return AuthSession.objects.get(
            pk=session_id, user_id=user_id, revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
    except (AuthSession.DoesNotExist, ValueError, ModelValidationError) as exc:
        raise AuthenticationFailed("Session expired. Please log in again.") from exc


class RevocableJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        cookie_auth = header is None
        raw = request.COOKIES.get("access_token") if cookie_auth else self.get_raw_token(header)
        if raw is None:
            return None
        token = self.get_validated_token(raw)
        user = self.get_user(token)
        require_session(token, user.pk)
        if cookie_auth:
            enforce_csrf(request)
        enforce_password_state(user, request)
        return user, token
