"""DOC-OPEN-13 preserves explicit v1 DRF exceptions and binary/204 semantics."""
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.users.models import CustomUser


class ResponseCompatibilityTests(AssuranceFeatureTestCase):
    def test_user_existing_response_shapes_and_204_remain_compatible(self):
        self.client.force_authenticate(self.superadmin)
        listing = self.client.get("/api/v1/auth/manage/")
        self.assertIsInstance(listing.data, list)
        target = CustomUser.objects.create_user(username="removable", email="remove@example.test", role="ADMIN")
        detail = self.client.get(f"/api/v1/auth/manage/{target.pk}/")
        self.assertEqual(str(detail.data["id"]), str(target.pk))
        self.assertNotIn("success", detail.data)
        update = self.client.patch(f"/api/v1/auth/manage/{target.pk}/", {"first_name": "Edited"})
        self.assertEqual(update.data["first_name"], "Edited")
        response = self.client.delete(f"/api/v1/auth/manage/{target.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

    def test_assignment_exceptions_and_new_endpoint_envelopes(self):
        assignment = self.agent.dealer_assignments.get()
        self.client.force_authenticate(self.superadmin)
        root = "/api/v1/dealers/assignments/"
        listing = self.client.get(root)
        self.assertTrue(listing.data["success"])
        detail = self.client.get(f"{root}{assignment.pk}/")
        self.assertNotIn("success", detail.data)
        self.assertEqual(str(detail.data["id"]), str(assignment.pk))
        update = self.client.patch(f"{root}{assignment.pk}/", {"dealer": str(self.other_dealer.pk)})
        self.assertEqual(update.status_code, 200)
        self.assertNotIn("success", update.data)
        self.assertTrue(self.client.get("/api/v1/audit/").data["success"])
        error = self.client.get("/api/v1/audit/?page=0")
        self.assertFalse(error.data["success"])
        self.assertEqual(error.data["error_code"], "VALIDATION_ERROR")
