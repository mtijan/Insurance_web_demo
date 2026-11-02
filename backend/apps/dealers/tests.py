import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.dealers.models import Dealer, AgentDealerAssignment
from apps.users.models import CustomUser, UserRole


class DealerAndAssignmentTests(APITestCase):
    def setUp(self):
        # Create test dealers
        self.dealer_a = Dealer.objects.create(
            code="DLR-JKT-001",
            name="PT Nusantara Honda Jakarta",
            address="Jl. Sudirman No. 1, Jakarta",
            phone="021-5551234",
            is_active=True
        )
        self.dealer_b = Dealer.objects.create(
            code="DLR-BDG-002",
            name="PT Bandung Motor Perkasa",
            address="Jl. Asia Afrika No. 2, Bandung",
            phone="022-7771234",
            is_active=True
        )

        self.create_test_users()
        self.configure_assignments()

    def create_test_users(self):
        # Create test users for all 4 roles
        self.superadmin = CustomUser.objects.create_user(
            username="superadmin_test",
            email="superadmin@test.com",
            password="Password123!",
            role=UserRole.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.admin_user = CustomUser.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="Password123!",
            role=UserRole.ADMIN
        )
        self.agent_user = CustomUser.objects.create_user(
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
            dealer=self.dealer_a
        )

    def configure_assignments(self):
        # Assign agent_user to dealer_a only
        self.assignment = AgentDealerAssignment.objects.create(
            agent=self.agent_user,
            dealer=self.dealer_a
        )

        self.dealer_list_url = reverse("dealer-list")
        self.assignment_list_url = reverse("dealer-assignment-list")

    def test_dealer_model_uuid_and_str(self):
        """Verify dealer primary key is UUID and string representation matches format."""
        self.assertIsInstance(self.dealer_a.id, uuid.UUID)
        self.assertEqual(str(self.dealer_a), "DLR-JKT-001 - PT Nusantara Honda Jakarta")

    def test_superadmin_dealer_crud(self):
        """Super Admin should have full CRUD access on Dealer."""
        self.client.force_authenticate(user=self.superadmin)

        # 1. Create
        payload = {
            "code": "DLR-SBY-003",
            "name": "PT Surabaya Gemilang Motor",
            "address": "Jl. Pemuda No. 10, Surabaya",
            "phone": "031-8881234",
            "is_active": True
        }
        res_create = self.client.post(self.dealer_list_url, payload, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        new_dealer_id = res_create.data["data"]["id"]

        # 2. Retrieve
        detail_url = reverse("dealer-detail", kwargs={"pk": new_dealer_id})
        res_get = self.client.get(detail_url)
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data["data"]["code"], "DLR-SBY-003")

        # 3. Update
        res_update = self.client.patch(detail_url, {"name": "PT Surabaya Gemilang Updated"})
        self.assertEqual(res_update.status_code, status.HTTP_200_OK)
        self.assertEqual(res_update.data["data"]["name"], "PT Surabaya Gemilang Updated")

        # 4. Delete
        res_delete = self.client.delete(detail_url)
        self.assertEqual(res_delete.status_code, status.HTTP_200_OK)
        self.assertFalse(Dealer.objects.filter(id=new_dealer_id).exists())

    def test_admin_read_all_dealers_cannot_write(self):
        """Underwriter Admin can read all dealers but cannot create or update."""
        self.client.force_authenticate(user=self.admin_user)

        # Read all
        res_list = self.client.get(self.dealer_list_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data["data"]), 2)

        # Attempt to create (must fail 403)
        res_create = self.client.post(self.dealer_list_url, {"code": "DLR-NEW", "name": "New"}, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_403_FORBIDDEN)

    def test_dealer_user_reads_only_own_dealer(self):
        """Dealer staff should only list and retrieve their own dealer branch."""
        self.client.force_authenticate(user=self.dealer_user)

        # List must contain only dealer_a
        res_list = self.client.get(self.dealer_list_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data["data"]), 1)
        self.assertEqual(res_list.data["data"][0]["code"], "DLR-JKT-001")

        # Detail own dealer
        own_url = reverse("dealer-detail", kwargs={"pk": self.dealer_a.id})
        res_own = self.client.get(own_url)
        self.assertEqual(res_own.status_code, status.HTTP_200_OK)

        # Detail other dealer (must return 404 because out of scoped queryset)
        other_url = reverse("dealer-detail", kwargs={"pk": self.dealer_b.id})
        res_other = self.client.get(other_url)
        self.assertEqual(res_other.status_code, status.HTTP_404_NOT_FOUND)

        # Dealer cannot create or delete
        res_create = self.client.post(self.dealer_list_url, {"code": "X", "name": "X"}, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_403_FORBIDDEN)

    def test_agent_user_reads_only_assigned_dealers(self):
        """Agent should only see dealers assigned to them."""
        self.client.force_authenticate(user=self.agent_user)

        # List should return only dealer_a
        res_list = self.client.get(self.dealer_list_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data["data"]), 1)
        self.assertEqual(res_list.data["data"][0]["code"], "DLR-JKT-001")

        # Detail assigned dealer
        assigned_url = reverse("dealer-detail", kwargs={"pk": self.dealer_a.id})
        res_assigned = self.client.get(assigned_url)
        self.assertEqual(res_assigned.status_code, status.HTTP_200_OK)

        # Detail unassigned dealer returns 404
        unassigned_url = reverse("dealer-detail", kwargs={"pk": self.dealer_b.id})
        res_unassigned = self.client.get(unassigned_url)
        self.assertEqual(res_unassigned.status_code, status.HTTP_404_NOT_FOUND)

        # Agent cannot create dealer
        res_create = self.client.post(self.dealer_list_url, {"code": "X", "name": "X"}, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_403_FORBIDDEN)

    def test_agent_dealer_assignment_lifecycle(self):
        """Super Admin assigns an Agent to Dealer, rejects invalid roles and duplicates."""
        self.client.force_authenticate(user=self.superadmin)

        # Assign agent to dealer_b
        payload = {
            "agent": str(self.agent_user.id),
            "dealer": str(self.dealer_b.id)
        }
        res_assign = self.client.post(self.assignment_list_url, payload, format="json")
        self.assertEqual(res_assign.status_code, status.HTTP_201_CREATED)
        assignment_id = res_assign.data["data"]["id"]

        # Duplicate assignment attempt should be rejected with 400
        res_dup = self.client.post(self.assignment_list_url, payload, format="json")
        self.assertEqual(res_dup.status_code, status.HTTP_400_BAD_REQUEST)

        # Assign non-agent user should fail
        invalid_payload = {
            "agent": str(self.dealer_user.id),
            "dealer": str(self.dealer_b.id)
        }
        res_invalid = self.client.post(self.assignment_list_url, invalid_payload, format="json")
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)

        # Delete assignment
        detail_assign_url = reverse("dealer-assignment-detail", kwargs={"pk": assignment_id})
        res_del = self.client.delete(detail_assign_url)
        self.assertEqual(res_del.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access_denied(self):
        """Unauthenticated requests must receive HTTP 401 Unauthorized."""
        res_dealers = self.client.get(self.dealer_list_url)
        self.assertEqual(res_dealers.status_code, status.HTTP_401_UNAUTHORIZED)
