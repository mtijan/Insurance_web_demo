import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.dealers.models import Dealer
from apps.users.models import CustomUser, UserRole


class UserModelAndAuthAPITests(APITestCase):
    def setUp(self):
        self.dealer = Dealer.objects.create(
            code="DLR-TEST-01",
            name="Dealer Test Honda",
            is_active=True
        )

        self.superadmin = CustomUser.objects.create_user(
            username="superadmin_test",
            email="superadmin@test.com",
            password="Password123!",
            role=UserRole.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True
        )

        self.agent = CustomUser.objects.create_user(
            username="agent_test",
            email="agent@test.com",
            password="Password123!",
            role=UserRole.AGENT
        )

        self.dealer_user = CustomUser.objects.create_user(
            username="dealer_test",
            email="dealer@test.com",
            password="Password123!",
            role=UserRole.DEALER,
            dealer=self.dealer
        )

        self.login_url = reverse("auth-login")
        self.me_url = reverse("auth-me")
        self.manage_url = reverse("user-management-list")

    def test_custom_user_uuid_and_roles(self):
        """Verify user ID is UUID and role properties work as expected."""
        self.assertIsInstance(self.superadmin.id, uuid.UUID)
        self.assertTrue(self.superadmin.is_super_admin)
        self.assertTrue(self.superadmin.is_admin_user)
        self.assertFalse(self.superadmin.is_agent)

        self.assertTrue(self.agent.is_agent)
        self.assertFalse(self.agent.is_admin_user)

        self.assertTrue(self.dealer_user.is_dealer)
        self.assertEqual(self.dealer_user.dealer.code, "DLR-TEST-01")

    def test_login_success(self):
        """FR-AUTH-01: cookie login returns a profile without JavaScript token copies."""
        payload = {
            "username": "agent_test",
            "password": "Password123!"
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertNotIn("access_token", response.data["data"])
        self.assertIn("access_token", response.cookies)
        self.assertEqual(response.data["data"]["user"]["username"], "agent_test")
        self.assertEqual(response.data["data"]["user"]["role"], "AGENT")

    def test_login_invalid_password(self):
        """Verify login with wrong password returns 400 error."""
        payload = {
            "username": "agent_test",
            "password": "WrongPassword!"
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_endpoint_authenticated(self):
        """Verify /auth/me/ endpoint returns current authenticated user info."""
        self.client.force_authenticate(user=self.agent)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["username"], "agent_test")
        self.assertEqual(response.data["data"]["role"], "AGENT")

    def test_rbac_superadmin_user_management(self):
        """Verify Super Admin can list users, but Agent gets 403 Forbidden."""
        # 1. Agent attempt
        self.client.force_authenticate(user=self.agent)
        response_agent = self.client.get(self.manage_url)
        self.assertEqual(response_agent.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Super Admin attempt
        self.client.force_authenticate(user=self.superadmin)
        response_admin = self.client.get(self.manage_url)
        self.assertEqual(response_admin.status_code, status.HTTP_200_OK)
