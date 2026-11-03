from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog


class AuditViewerTests(AssuranceFeatureTestCase):
    def test_only_superadmin_can_read_and_nobody_can_mutate(self):
        self.assertEqual(self.client.get("/api/v1/audit/").status_code, 401)
        for user in (self.admin, self.agent, self.owner):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get("/api/v1/audit/").status_code, 403)
        self.client.force_authenticate(self.superadmin)
        for method in (self.client.post, self.client.put, self.client.patch, self.client.delete):
            self.assertEqual(method("/api/v1/audit/", {}).status_code, 405)

    def test_projection_filters_bounded_pagination_and_cache(self):
        AuditLog.objects.bulk_create([AuditLog(action="UPDATE", entity_name="SYNTHETIC", entity_id=str(index),
                                             changes={"private": "synthetic-secret-must-not-appear"},
                                             ip_address="127.0.0.1") for index in range(52)])
        self.client.force_authenticate(self.superadmin)
        response = self.client.get("/api/v1/audit/?action=UPDATE&entity_name=SYNTHETIC")
        data = response.data["data"]
        self.assertEqual(len(data["results"]), 50)
        self.assertTrue(data["has_next"])
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertNotIn("synthetic-secret", str(response.data))
        self.assertEqual(set(data["results"][0]), {"id", "action", "entity_name", "entity_id", "created_at"})
        second = self.client.get("/api/v1/audit/?page=2").data["data"]
        self.assertEqual(len(second["results"]), 2)
        self.assertFalse(second["has_next"])
        self.assertEqual(self.client.get("/api/v1/audit/?page=0").status_code, 400)
