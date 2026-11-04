from unittest.mock import patch

from django.db import DatabaseError

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.assurances.services.workflow_service import submit_assurance_application


class InspectionSupport(AssuranceFeatureTestCase):
    def submitted(self, **overrides):
        assurance = self.draft(**overrides)
        self.attach_uploaded_documents(assurance)
        return submit_assurance_application(assurance, self.owner)

    def inspect(self, assurance, action="NOTE", section="DOCUMENTS", notes="KTP kurang jelas",
                user=None):
        return self.post_action(assurance, "inspection", {
            "action": action, "section": section, "review_notes": notes,
        }, user=user or self.agent)


class InspectionTests(InspectionSupport):
    def test_agent_can_record_specific_shortcoming_visible_to_dealer(self):
        assurance = self.submitted()
        response = self.inspect(assurance)
        self.assertEqual(response.status_code, 200, getattr(response, "data", response.content))
        self.assertEqual(response.data["data"]["status"], "SUBMITTED")
        self.client.force_authenticate(self.owner)
        detail = self.client.get(f"/api/v1/assurances/{assurance.pk}/").data["data"]
        event = detail["review_history"][-1]
        self.assertEqual(event["section"], "DOCUMENTS")
        self.assertEqual(event["review_notes"], "KTP kurang jelas")
        self.assertEqual(event["actor_role"], "AGENT")

    def test_agent_can_request_correction_without_final_approval_permission(self):
        assurance = self.submitted()
        response = self.inspect(assurance, "REQUEST_REVISION")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["status"], "REVISION")
        self.assertEqual(self.post_action(assurance, "submit").status_code, 200)
        for decision in ("APPROVE", "REJECT_FINAL"):
            self.assertEqual(self.post_action(assurance, "review", {
                "decision": decision, "review_notes": "Catatan",
            }, user=self.agent).status_code, 403)

    def test_admin_verification_stages_visible_to_dealer(self):
        assurance = self.submitted()
        for action, section, stage in (("START", "DATA", "DATA"),
                                       ("VERIFY", "DATA", "DOCUMENTS"),
                                       ("VERIFY", "DOCUMENTS", "COMPLETE")):
            response = self.inspect(assurance, action, section, user=self.admin)
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["data"]["verification_stage"], stage)
        self.client.force_authenticate(self.owner)
        data = self.client.get(f"/api/v1/assurances/{assurance.pk}/").data["data"]
        self.assertTrue(data["data_verified"])
        self.assertTrue(data["documents_verified"])

    def test_final_rejection_is_distinct_and_terminal(self):
        assurance = self.submitted()
        response = self.post_action(assurance, "review", {
            "decision": "REJECT_FINAL", "review_notes": "Tidak memenuhi kriteria",
        }, user=self.admin)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["status"], "REJECTED")
        self.assertFalse(response.data["data"]["can_edit"])
        self.assertEqual(self.post_action(assurance, "submit").status_code, 403)
        self.assertEqual(self.inspect(assurance, user=self.superadmin).status_code, 400)

    def test_inspection_audit_failure_rolls_back_state_and_history(self):
        assurance = self.submitted()
        count = assurance.review_history.count()
        with patch("apps.audit.services.audit_service.AuditLog.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            response = self.inspect(assurance, "REQUEST_REVISION")
        self.assertEqual(response.status_code, 503, response.data)
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "SUBMITTED")
        self.assertEqual(assurance.review_history.count(), count)
