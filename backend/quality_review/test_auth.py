"""Audit probes assert required behavior; failures identify open findings."""
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.users.models import CustomUser


class AuthenticationReviewTests(AssuranceFeatureTestCase):
    def setUp(self):
        self.owner.set_password("Synthetic-review-password-123!")
        self.owner.save()

    def login(self, username=None):
        return self.client.post("/api/v1/auth/login/", {
            "username": username or self.owner.username,
            "password": "Synthetic-review-password-123!",
        }, format="json")

    def test_login_cookie_authenticates_following_request(self):
        self.assertEqual(self.login().status_code, 200)
        self.assertIn("access_token", self.client.cookies)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 200)

    def test_logout_invalidates_previously_issued_access_token(self):
        login = self.login()
        token = login.cookies["access_token"].value
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.post("/api/v1/auth/logout/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_login_accepts_email_identity(self):
        self.assertEqual(self.login(self.owner.email).status_code, 200)

    def test_dealer_account_requires_dealer_association(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.post("/api/v1/auth/manage/", {
            "username": "review_unbound_dealer", "email": "unbound@example.test",
            "role": "DEALER", "password": "Synthetic-review-password-123!",
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_user_email_is_unique_as_required_by_data_contract(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.post("/api/v1/auth/manage/", {
            "username": "review_duplicate_email", "email": self.owner.email,
            "role": "ADMIN", "password": "Synthetic-review-password-123!",
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_user_api_enforces_configured_password_validators(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.post("/api/v1/auth/manage/", {
            "username": "review_weak_password", "email": "weak@example.test",
            "role": "ADMIN", "password": "1",
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_disabled_account_cannot_use_bearer_token(self):
        token = self.login().cookies["access_token"].value
        CustomUser.objects.filter(pk=self.owner.pk).update(is_active=False)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_repeated_seed_does_not_reset_an_existing_admin_password(self):
        from io import StringIO
        from django.core.management import call_command

        user = CustomUser.objects.create_user(
            username="superadmin", role="SUPER_ADMIN", password="Existing-private-password-123!",
        )
        call_command("seed_initial_users", stdout=StringIO())
        user.refresh_from_db()
        self.assertTrue(user.check_password("Existing-private-password-123!"))
