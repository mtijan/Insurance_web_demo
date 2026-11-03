"""First-login server enforcement with real JWT/cookie sessions."""
from unittest.mock import patch

from django.db import DatabaseError
from rest_framework.test import APIClient

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.users.models import AuthSession, CustomUser
from apps.users.services.user_service import create_user, update_user

OLD = "Synthetic-first-login-password-823!"
NEW = "Replacement-test-passphrase-957!"


class FirstLoginTests(AssuranceFeatureTestCase):
    def setUp(self):
        self.owner.set_password(OLD)
        self.owner.must_change_password = True
        self.owner.save()
        self.client = APIClient(enforce_csrf_checks=True)

    def login(self, cookie=False):
        extra = {}
        if cookie:
            extra["HTTP_X_CSRFTOKEN"] = self.client.get("/api/v1/auth/csrf/").data["data"]["csrf_token"]
        response = self.client.post(f"/api/v1/auth/{'login' if cookie else 'token'}/", {
            "username": self.owner.username, "password": OLD,
        }, format="json", **extra)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["user"]["must_change_password"])
        if not cookie:
            self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["data"]["access_token"])
        return response.data["data"]

    def change(self, **overrides):
        data = {"current_password": OLD, "new_password": NEW, **overrides}
        return self.client.post("/api/v1/auth/change-password/", data, format="json")

    def test_business_endpoints_cannot_be_bypassed_by_restricted_bearer(self):
        self.login()
        assurance = self.draft()
        paths = ("assurances/", "dealers/", "auth/manage/", "configs/admin-fee/",
                 "assurances/export-excel/", f"assurances/{assurance.pk}/",
                 "assurances/calculate-premium/?sum_insured=20000000&coverage_type=TLO")
        for path in paths:
            response = self.client.get("/api/v1/" + path)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.data["error_code"], "PASSWORD_CHANGE_REQUIRED")
        for action in ("submit", "review", "documents"):
            self.assertEqual(self.client.post(f"/api/v1/assurances/{assurance.pk}/{action}/", {}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/assurances/{assurance.pk}/", {}).status_code, 403)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/logout/").status_code, 200)

    def test_restricted_refresh_never_grants_business_access(self):
        tokens = self.login()
        response = self.client.post("/api/v1/auth/token/refresh/", {"refresh_token": tokens["refresh_token"]})
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["data"]["access_token"])
        self.assertEqual(self.client.get("/api/v1/assurances/").status_code, 403)

    def test_success_revokes_all_access_refresh_and_requires_relogin(self):
        first = self.login()
        second = self.login()
        response = self.change()
        self.assertEqual(response.status_code, 200)
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.must_change_password)
        self.assertTrue(self.owner.check_password(NEW))
        self.assertFalse(AuthSession.objects.filter(revoked_at__isnull=True).exists())
        for tokens in (first, second):
            self.client.credentials(HTTP_AUTHORIZATION="Bearer " + tokens["access_token"])
            self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)
            self.assertEqual(self.client.post("/api/v1/auth/token/refresh/", {"refresh_token": tokens["refresh_token"]}).status_code, 401)
        login = self.client.post("/api/v1/auth/token/", {"username": self.owner.username, "password": NEW})
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.data["data"]["access_token"])
        self.assertEqual(self.client.get("/api/v1/assurances/").status_code, 200)
        changes = AuditLog.objects.get(action="PASSWORD_CHANGE").changes
        self.assertEqual(changes, {"password_changed": True})

    def test_password_validators_and_current_password_fail_without_mutation(self):
        self.login()
        count = AuditLog.objects.count()
        for password in ("short", "password", "123456789012", OLD, self.owner.username):
            self.assertEqual(self.change(new_password=password).status_code, 400)
        self.assertEqual(self.change(current_password="incorrect").status_code, 400)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password(OLD))
        self.assertTrue(self.owner.must_change_password)
        self.assertEqual(AuditLog.objects.count(), count)
        self.assertFalse(AuthSession.objects.filter(revoked_at__isnull=False).exists())

    def test_cross_account_fields_cannot_choose_password_target(self):
        self.login()
        original = self.admin.password
        for key in ("user_id", "id", "username", "must_change_password"):
            self.assertEqual(self.change(**{key: str(self.admin.pk)}).status_code, 400)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.password, original)
        self.assertFalse(AuditLog.objects.filter(action="PASSWORD_CHANGE").exists())

    def test_cookie_change_requires_csrf_and_rejects_foreign_origin(self):
        data = self.login(cookie=True)
        self.assertEqual(self.change().status_code, 403)
        payload = {"current_password": OLD, "new_password": NEW}
        response = self.client.post("/api/v1/auth/change-password/", payload, format="json",
                                    HTTP_X_CSRFTOKEN=data["csrf_token"], HTTP_ORIGIN="https://evil.example.test")
        self.assertEqual(response.status_code, 403)
        response = self.client.post("/api/v1/auth/change-password/", payload, format="json", HTTP_X_CSRFTOKEN=data["csrf_token"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies["access_token"]["max-age"], 0)

    def test_audit_failure_rolls_back_password_flag_and_session_revocation(self):
        self.login()
        count = AuditLog.objects.count()
        with patch("apps.audit.services.audit_service.AuditLog.objects.create", side_effect=DatabaseError("synthetic")):
            response = self.change()
        self.assertEqual(response.status_code, 503)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password(OLD))
        self.assertTrue(self.owner.must_change_password)
        self.assertEqual(AuditLog.objects.count(), count)
        self.assertTrue(AuthSession.objects.filter(revoked_at__isnull=True).exists())

    def test_new_provisioning_reset_and_existing_account_compatibility(self):
        account = create_user(self.superadmin, {"username": "new_staff", "email": "new@example.test",
                                              "password": NEW, "role": "ADMIN"})
        self.assertTrue(account.must_change_password)
        existing = CustomUser.objects.create_user(username="existing", email="existing@example.test", password=OLD, role="ADMIN")
        self.assertFalse(existing.must_change_password)
        update_user(self.superadmin, existing, {"first_name": "Edited"})
        existing.refresh_from_db()
        self.assertFalse(existing.must_change_password)
        update_user(self.superadmin, existing, {"password": NEW})
        existing.refresh_from_db()
        self.assertTrue(existing.must_change_password)

    def test_server_reads_flag_even_for_session_issued_before_restriction(self):
        self.owner.must_change_password = False
        self.owner.save()
        response = self.client.post("/api/v1/auth/token/", {"username": self.owner.username, "password": OLD})
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["data"]["access_token"])
        CustomUser.objects.filter(pk=self.owner.pk).update(must_change_password=True)
        self.assertEqual(self.client.get("/api/v1/assurances/").status_code, 403)

    def test_django_session_cannot_bypass_first_login_on_admin(self):
        self.owner.is_staff = True
        self.owner.save()
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get("/admin/").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/auth/csrf/").status_code, 200)

    def test_existing_long_password_can_login_and_change_without_a_new_length_policy(self):
        current = "Synthetic-legacy-passphrase-953!" * 7
        replacement = "Synthetic-replacement-passphrase-842!" * 6
        self.owner.set_password(current)
        self.owner.save()
        response = self.client.post("/api/v1/auth/token/", {
            "username": self.owner.username, "password": current,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["data"]["access_token"])
        self.assertEqual(self.change(current_password=current, new_password=replacement).status_code, 200)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password(replacement))
