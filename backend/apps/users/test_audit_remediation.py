"""Regression tests for role-flag sync, post-expiry logout, and auth hardening."""
from io import StringIO

from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APIClient

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.users.models import AuthSession, CustomUser, UserRole

PASSWORD = "Synthetic-remediation-password-819!"


class UserAuditRemediationTests(AssuranceFeatureTestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf(self):
        return self.client.get("/api/v1/auth/csrf/").data["data"]["csrf_token"]

    def test_createsuperuser_sets_super_admin_role(self):
        admin = CustomUser.objects.create_superuser(
            username="cli_super", email="cli_super@example.test", password=PASSWORD,
        )
        self.assertEqual(admin.role, UserRole.SUPER_ADMIN)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_demoting_seeded_superuser_revokes_privilege_and_sessions(self):
        call_command("seed_initial_users", stdout=StringIO())
        seeded = CustomUser.objects.get(username="superadmin")
        seeded.set_password(PASSWORD)
        seeded.must_change_password = False
        seeded.save()
        tokens = self.client.post("/api/v1/auth/token/", {
            "username": "superadmin", "password": PASSWORD,
        }, format="json").data["data"]
        self.client.force_authenticate(self.superadmin)
        demote = self.client.patch(f"/api/v1/auth/manage/{seeded.pk}/", {
            "role": UserRole.DEALER, "dealer": str(self.dealer.pk),
        }, format="json")
        self.assertEqual(demote.status_code, 200)
        seeded.refresh_from_db()
        self.assertFalse(seeded.is_superuser)
        self.assertFalse(seeded.is_staff)
        self.assertFalse(seeded.is_super_admin)
        self.client.force_authenticate(None)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)
        fresh = self.client.post("/api/v1/auth/token/", {
            "username": "superadmin", "password": PASSWORD,
        }, format="json").data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {fresh}")
        for path in ("auth/manage/", "audit/"):
            self.assertEqual(self.client.get(f"/api/v1/{path}").status_code, 403)
        self.assertEqual(self.client.put("/api/v1/configs/admin-fee/", {"value": "1000"}, format="json").status_code, 403)

    def test_non_dealer_role_cannot_bind_dealer_fk(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.patch(f"/api/v1/auth/manage/{self.admin.pk}/", {
            "dealer": str(self.dealer.pk),
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_spa_logout_after_access_expiry_revokes_session_and_clears_refresh(self):
        self.owner.set_password(PASSWORD)
        self.owner.save()
        login = self.client.post("/api/v1/auth/login/", {
            "username": self.owner.username, "password": PASSWORD,
        }, format="json", HTTP_X_CSRFTOKEN=self.csrf())
        self.assertEqual(login.status_code, 200)
        del self.client.cookies["access_token"]
        logout = self.client.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=self.csrf())
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(logout.cookies["refresh_token"]["max-age"], 0)
        self.assertFalse(AuthSession.objects.filter(user=self.owner, revoked_at__isnull=True).exists())
        refresh = self.client.post("/api/v1/auth/refresh/", HTTP_X_CSRFTOKEN=self.csrf())
        self.assertEqual(refresh.status_code, 401)

    @override_settings(
        ENABLE_AUTH_THROTTLE=True,
        REST_FRAMEWORK={
            "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
            "DEFAULT_AUTHENTICATION_CLASSES": ("apps.users.authentication.RevocableJWTAuthentication",),
            "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
            "DEFAULT_THROTTLE_RATES": {"auth_login": "2/min", "auth_refresh": "2/min", "auth_password": "2/min"},
        },
    )
    def test_auth_login_throttles_when_scoped_throttle_enabled(self):
        from django.core.cache import cache

        cache.clear()
        for code in (400, 400, 429):
            resp = self.client.post("/api/v1/auth/token/", {
                "username": self.owner.username, "password": "wrong-password",
            }, format="json")
            self.assertEqual(resp.status_code, code)

    def test_me_and_manage_responses_disable_shared_caching(self):
        self.client.force_authenticate(self.superadmin)
        for path in ("/api/v1/auth/me/", "/api/v1/auth/manage/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Cache-Control"], "private, no-store")
