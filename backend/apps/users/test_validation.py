from django.db import IntegrityError, transaction

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.users.models import CustomUser


class UserValidationTests(AssuranceFeatureTestCase):
    def setUp(self):
        self.client.force_authenticate(self.superadmin)

    def patch_user(self, user, **data):
        return self.client.patch(f"/api/v1/auth/manage/{user.pk}/", data, format="json")

    def test_patch_cannot_clear_dealer_from_existing_dealer_role(self):
        response = self.patch_user(self.owner, dealer=None)
        self.assertEqual(response.status_code, 400)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.dealer_id, self.dealer.pk)

    def test_role_change_to_dealer_requires_combined_association(self):
        self.assertEqual(self.patch_user(self.admin, role="DEALER").status_code, 400)
        self.assertEqual(self.patch_user(self.admin, role="DEALER", dealer=str(self.dealer.pk)).status_code, 200)

    def test_assigned_agent_role_change_is_rejected_until_assignment_removed(self):
        self.assertEqual(self.patch_user(self.agent, role="ADMIN").status_code, 400)
        self.agent.dealer_assignments.all().delete()
        self.assertEqual(self.patch_user(self.agent, role="ADMIN").status_code, 200)

    def test_duplicate_email_patch_and_database_constraint(self):
        self.assertEqual(self.patch_user(self.admin, email=self.owner.email.upper()).status_code, 400)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CustomUser.objects.filter(pk=self.admin.pk).update(email=self.owner.email.upper())

    def test_password_patch_uses_django_validators_and_preserves_existing_hash(self):
        before = self.owner.password
        self.assertEqual(self.patch_user(self.owner, password="1").status_code, 400)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.password, before)

    def test_username_and_case_insensitive_email_login(self):
        self.owner.set_password("Valid-identity-password-938!")
        self.owner.save()
        self.client.force_authenticate(None)
        for identity in (self.owner.username, self.owner.email.upper()):
            with self.subTest(identity=identity):
                response = self.client.post("/api/v1/auth/login/", {
                    "username": identity, "password": "Valid-identity-password-938!",
                })
                self.assertEqual(response.status_code, 200)

    def test_ambiguous_username_email_and_inactive_login_are_rejected(self):
        self.owner.set_password("Valid-identity-password-938!")
        self.owner.save()
        CustomUser.objects.create_user(username=self.owner.email, email="different@example.test", role="ADMIN")
        self.client.force_authenticate(None)
        response = self.client.post("/api/v1/auth/login/", {
            "username": self.owner.email, "password": "Valid-identity-password-938!",
        })
        self.assertEqual(response.status_code, 400)
        self.owner.is_active = False
        self.owner.save()
        response = self.client.post("/api/v1/auth/login/", {
            "username": self.owner.username, "password": "Valid-identity-password-938!",
        })
        self.assertEqual(response.status_code, 400)
