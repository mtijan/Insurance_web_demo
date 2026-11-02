from unittest.mock import patch

from django.db import DatabaseError
from rest_framework.exceptions import PermissionDenied

from apps.assurances.models import PolicyHolder, VehicleAssurance
from apps.assurances.services.assurance_service import update_assurance_draft
from apps.assurances.services.workflow_service import review_assurance, submit_assurance_application
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.middleware import audit_request
from apps.audit.models import AuditLog
from apps.audit.services.audit_service import AuditUnavailable


class AuditTests(AssuranceFeatureTestCase):
    def test_create_and_update_audit_excludes_identity_and_credentials(self):
        assurance = self.draft()
        update_assurance_draft(assurance, self.owner, {"vehicle_object": "Test motorcycle"})
        self.assertEqual(AuditLog.objects.filter(entity_id=str(assurance.pk)).count(), 2)
        for log in AuditLog.objects.all():
            self.assertNotIn(assurance.policy_holder.nik, str(log.changes))
            self.assertNotIn("password", str(log.changes))

    def test_create_audit_failure_rolls_back_holder_and_draft(self):
        with patch("apps.audit.services.audit_service.AuditLog.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            with self.assertRaises(AuditUnavailable):
                self.draft()
        self.assertFalse(VehicleAssurance.objects.exists())
        self.assertFalse(PolicyHolder.objects.exists())

    def test_update_audit_failure_rolls_back_data(self):
        assurance = self.draft()
        with patch("apps.audit.services.audit_service.AuditLog.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            with self.assertRaises(AuditUnavailable):
                update_assurance_draft(assurance, self.owner, {"vehicle_object": "Modified"})
        assurance.refresh_from_db()
        self.assertEqual(assurance.vehicle_object, "Sepeda Motor")

    def test_services_reject_peer_submit_and_agent_review(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        with self.assertRaises(PermissionDenied):
            submit_assurance_application(assurance, self.peer)
        submit_assurance_application(assurance, self.owner)
        with self.assertRaises(PermissionDenied):
            review_assurance(assurance, self.agent, {"decision": "APPROVE"})

    def test_request_context_is_reset_and_untrusted_forwarded_ip_is_ignored(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        self.post_action(assurance, "submit", REMOTE_ADDR="192.0.2.1",
                         HTTP_X_FORWARDED_FOR="203.0.113.9")
        self.assertEqual(AuditLog.objects.get(action="SUBMIT").ip_address, "192.0.2.1")
        self.assertIsNone(audit_request.get())

    def test_invalid_remote_ip_is_not_persisted(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        self.assertEqual(self.post_action(assurance, "submit", REMOTE_ADDR="bad-ip").status_code, 200)
        self.assertIsNone(AuditLog.objects.get(action="SUBMIT").ip_address)

    def test_login_audit_does_not_record_password_or_tokens(self):
        self.owner.set_password("Synthetic-password-123!")
        self.owner.save()
        response = self.client.post("/api/v1/auth/login/", {
            "username": self.owner.username, "password": "Synthetic-password-123!",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        audit = AuditLog.objects.get(action="LOGIN")
        self.assertEqual(audit.changes, {})
        self.assertEqual(audit.user, self.owner)
