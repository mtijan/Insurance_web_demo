"""Audit evidence for each CRUD mutation group, including fail-closed rollback."""
from unittest.mock import patch

from django.db import DatabaseError

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.dealers.models import AgentDealerAssignment, Dealer
from apps.users.models import CustomUser


class MasterAuditTests(AssuranceFeatureTestCase):
    def setUp(self):
        self.client.force_authenticate(self.superadmin)

    def mutation_case(self, group):
        if group == "CUSTOM_USER":
            return "/api/v1/auth/manage/", {"username": "new_audited", "email": "new@example.test", "role": "ADMIN"}, CustomUser, {"is_active": False}
        if group == "DEALER":
            return "/api/v1/dealers/", {"code": "AUDIT-NEW", "name": "Audited"}, Dealer, {"is_active": False}
        return "/api/v1/dealers/assignments/", {"agent": str(self.agent.pk), "dealer": str(self.other_dealer.pk)}, AgentDealerAssignment, {"dealer": str(self.dealer.pk)}

    def prepare_update(self, group):
        url, payload, model, change = self.mutation_case(group)
        response = self.client.post(url, payload, format="json")
        data = response.data.get("data", response.data)
        identity = data["id"]
        if group == "AGENT_DEALER_ASSIGNMENT":
            self.agent.dealer_assignments.filter(dealer=self.dealer).delete()
        return f"{url}{identity}/", model.objects.get(pk=identity), change

    def assert_audit(self, group, identity, action):
        log = AuditLog.objects.get(entity_name=group, entity_id=str(identity), action=action)
        self.assertEqual(log.user_id, self.superadmin.pk)
        self.assertEqual(log.ip_address, "192.0.2.25")
        self.assertNotIn("new@example.test", str(log.changes))
        self.assertNotIn("password", str(log.changes))

    def test_create_audit_records_actor_ip_and_safe_entity(self):
        for group in ("CUSTOM_USER", "DEALER", "AGENT_DEALER_ASSIGNMENT"):
            with self.subTest(group=group):
                url, payload, model, _ = self.mutation_case(group)
                response = self.client.post(url, payload, format="json", REMOTE_ADDR="192.0.2.25")
                self.assertEqual(response.status_code, 201, response.data)
                identity = response.data.get("data", response.data)["id"]
                self.assert_audit(group, identity, "CREATE")

    def test_update_audit_records_role_activity_and_assignment_changes(self):
        for group in ("CUSTOM_USER", "DEALER", "AGENT_DEALER_ASSIGNMENT"):
            with self.subTest(group=group):
                url, instance, change = self.prepare_update(group)
                response = self.client.patch(url, change, format="json", REMOTE_ADDR="192.0.2.25")
                self.assertEqual(response.status_code, 200, response.data)
                self.assert_audit(group, instance.pk, "UPDATE")

    def test_delete_audit_for_each_group(self):
        for group in ("CUSTOM_USER", "DEALER", "AGENT_DEALER_ASSIGNMENT"):
            with self.subTest(group=group):
                url, instance, _ = self.prepare_update(group)
                response = self.client.delete(url, REMOTE_ADDR="192.0.2.25")
                self.assertIn(response.status_code, (200, 204))
                self.assert_audit(group, instance.pk, "DELETE")

    def test_failed_create_audit_rolls_back_each_group(self):
        for group in ("CUSTOM_USER", "DEALER", "AGENT_DEALER_ASSIGNMENT"):
            with self.subTest(group=group):
                url, payload, model, _ = self.mutation_case(group)
                count = model.objects.count()
                with patch("apps.audit.services.audit_service.AuditLog.objects.create", side_effect=DatabaseError("private failure")):
                    response = self.client.post(url, payload, format="json")
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("private failure", str(response.data))
                self.assertEqual(model.objects.count(), count)

    def test_failed_update_audit_rolls_back_each_group(self):
        for group in ("CUSTOM_USER", "DEALER", "AGENT_DEALER_ASSIGNMENT"):
            with self.subTest(group=group):
                url, instance, change = self.prepare_update(group)
                original = {field: getattr(instance, field) for field in change}
                with patch("apps.audit.services.audit_service.AuditLog.objects.create", side_effect=DatabaseError("failure")):
                    response = self.client.patch(url, change, format="json")
                self.assertEqual(response.status_code, 503)
                instance.refresh_from_db()
                self.assertEqual({field: getattr(instance, field) for field in change}, original)

    def test_failed_delete_audit_rolls_back_each_group(self):
        for group in ("CUSTOM_USER", "DEALER", "AGENT_DEALER_ASSIGNMENT"):
            with self.subTest(group=group):
                url, instance, _ = self.prepare_update(group)
                identity = instance.pk
                with patch("apps.audit.services.audit_service.AuditLog.objects.create", side_effect=DatabaseError("failure")):
                    response = self.client.delete(url)
                self.assertEqual(response.status_code, 503)
                self.assertTrue(type(instance).objects.filter(pk=identity).exists())

    def test_user_role_and_password_changes_do_not_log_secrets(self):
        response = self.client.patch(f"/api/v1/auth/manage/{self.admin.pk}/", {
            "role": "SUPER_ADMIN", "password": "Sensitive-password-1938!",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        log = AuditLog.objects.get(entity_name="CUSTOM_USER", entity_id=str(self.admin.pk), action="UPDATE")
        self.assertEqual(log.changes["role"], {"old": "ADMIN", "new": "SUPER_ADMIN"})
        self.assertTrue(log.changes["password_changed"])
        self.assertNotIn("Sensitive-password", str(log.changes))
