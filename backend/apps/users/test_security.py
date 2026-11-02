"""Real authentication, CSRF, revocation and credential lifecycle regressions."""
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.db import DatabaseError
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from datetime import timedelta
from django.utils import timezone

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.users.models import AuthSession, CustomUser

PASSWORD = "Synthetic-security-password-928!"


class AuthenticationSecurityTests(AssuranceFeatureTestCase):
    def setUp(self):
        self.owner.set_password(PASSWORD)
        self.owner.save()
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf(self):
        response = self.client.get("/api/v1/auth/csrf/")
        return response.data["data"]["csrf_token"]

    def login(self, bearer=False, **extra):
        path = "token" if bearer else "login"
        return self.client.post(f"/api/v1/auth/{path}/", {
            "username": self.owner.username, "password": PASSWORD,
        }, format="json", **extra)

    def cookie_login(self):
        response = self.login(HTTP_X_CSRFTOKEN=self.csrf())
        self.assertEqual(response.status_code, 200)
        return response

    def test_cookie_login_requires_csrf_and_rejects_foreign_origin(self):
        self.assertEqual(self.login().status_code, 403)
        response = self.login(HTTP_X_CSRFTOKEN=self.csrf(), HTTP_ORIGIN="https://evil.example.test")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(AuthSession.objects.exists())

    def test_cookie_login_has_no_token_body_and_authenticates_me(self):
        response = self.cookie_login()
        self.assertNotIn("access_token", response.data["data"])
        self.assertNotIn("refresh_token", response.data["data"])
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])
        self.assertEqual(response.cookies["access_token"]["samesite"], "Lax")
        self.assertEqual(response.cookies["access_token"]["max-age"], 900)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 200)

    @override_settings(AUTH_COOKIE_SECURE=True)
    def test_secure_cookie_flag_uses_environment(self):
        response = self.cookie_login()
        self.assertTrue(response.cookies["access_token"]["secure"])
        self.assertTrue(response.cookies["refresh_token"]["secure"])

    def test_cookie_mutations_require_csrf(self):
        self.cookie_login()
        self.assertEqual(self.client.post("/api/v1/auth/logout/").status_code, 403)
        self.assertEqual(self.client.post("/api/v1/auth/refresh/").status_code, 403)
        response = self.client.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=self.csrf())
        self.assertEqual(response.status_code, 200)

    def test_cookie_logout_revokes_copied_access_and_refresh(self):
        self.cookie_login()
        access = self.client.cookies["access_token"].value
        refresh = self.client.cookies["refresh_token"].value
        self.client.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=self.csrf())
        other = APIClient(enforce_csrf_checks=True)
        other.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(other.get("/api/v1/auth/me/").status_code, 401)
        self.assertEqual(other.post("/api/v1/auth/token/refresh/", {"refresh_token": refresh}).status_code, 401)

    def test_explicit_bearer_login_and_refresh_do_not_set_auth_cookies(self):
        response = self.login(bearer=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("access_token", response.cookies)
        token = response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        refresh = response.data["data"]["refresh_token"]
        result = self.client.post("/api/v1/auth/token/refresh/", {"refresh_token": refresh})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/logout/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_logout_does_not_revoke_another_login(self):
        first = self.login(bearer=True).data["data"]["access_token"]
        second = self.login(bearer=True).data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {first}")
        self.client.post("/api/v1/auth/logout/")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {second}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 200)

    def test_login_audit_failure_rolls_back_session(self):
        with patch("apps.audit.services.audit_service.AuditLog.objects.create", side_effect=DatabaseError("private failure")):
            response = self.login(bearer=True)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private failure", str(response.data))
        self.assertFalse(AuthSession.objects.exists())

    def test_logout_audit_failure_keeps_session_active(self):
        token = self.login(bearer=True).data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        with patch("apps.audit.services.audit_service.AuditLog.objects.create", side_effect=DatabaseError("failure")):
            response = self.client.post("/api/v1/auth/logout/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 200)

    def test_malformed_session_claim_returns_401(self):
        token = AccessToken(self.login(bearer=True).data["data"]["access_token"])
        token["sid"] = "bad-session-id"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_seed_preserves_password_and_creates_no_usable_default(self):
        before = self.owner.password
        call_command("seed_initial_users", stdout=StringIO())
        call_command("seed_initial_users", stdout=StringIO())
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.password, before)
        for name in ("superadmin", "admin_underwriter", "agent_budi", "dealer_honda_staff"):
            self.assertFalse(CustomUser.objects.get(username=name).has_usable_password())

    def test_cookie_refresh_works_without_returning_token_body(self):
        self.cookie_login()
        response = self.client.post("/api/v1/auth/refresh/", HTTP_X_CSRFTOKEN=self.csrf())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("access_token", response.data["data"])
        self.assertTrue(response.cookies["access_token"]["httponly"])

    def test_expired_session_and_legacy_token_without_session_are_rejected(self):
        token = AccessToken(self.login(bearer=True).data["data"]["access_token"])
        AuthSession.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)
        del token["sid"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_deactivate_then_reactivate_does_not_revive_old_access(self):
        from apps.users.services.user_service import update_user

        token = self.login(bearer=True).data["data"]["access_token"]
        update_user(self.superadmin, self.owner, {"is_active": False})
        update_user(self.superadmin, self.owner, {"is_active": True})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_password_update_revokes_access_and_refresh(self):
        from apps.users.services.user_service import update_user

        tokens = self.login(bearer=True).data["data"]
        update_user(self.superadmin, self.owner, {"password": "Replacement-private-password-482!"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)
        response = self.client.post("/api/v1/auth/token/refresh/", {"refresh_token": tokens["refresh_token"]})
        self.assertEqual(response.status_code, 401)

    def test_missing_malformed_or_access_token_cannot_refresh(self):
        access = self.login(bearer=True).data["data"]["access_token"]
        for raw in (None, "not-a-token", access):
            with self.subTest(raw=raw):
                response = self.client.post("/api/v1/auth/token/refresh/", {"refresh_token": raw}, format="json")
                self.assertEqual(response.status_code, 401)

    def test_explicit_password_command_is_separate_from_seed(self):
        target = "apps.users.management.commands.set_account_password.getpass"
        with patch(target, side_effect=["Operator-private-password-983!", "Operator-private-password-983!"]):
            call_command("set_account_password", self.owner.username, stdout=StringIO())
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password("Operator-private-password-983!"))
        call_command("seed_initial_users", stdout=StringIO())
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password("Operator-private-password-983!"))

    def test_refresh_rejects_nonobject_payload_without_server_error(self):
        response = self.client.post("/api/v1/auth/token/refresh/", [], format="json")
        self.assertEqual(response.status_code, 400)
