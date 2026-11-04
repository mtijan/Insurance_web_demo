from unittest.mock import patch

from django.db import DatabaseError
from rest_framework.exceptions import PermissionDenied

from apps.assurances.models import AssuranceNumberSequence
from apps.assurances.services.inspection_service import inspect_assurance
from apps.assurances.services.assurance_service import create_assurance_draft
from apps.assurances.services.workflow_service import submit_assurance_application
from apps.assurances.test_inspection import InspectionSupport
from apps.audit.models import AuditLog


class InspectionSecurityTests(InspectionSupport):
    def test_owner_cannot_inspect_and_agent_cannot_verify(self):
        assurance = self.submitted()
        self.assertEqual(self.inspect(assurance, user=self.owner).status_code, 403)
        for action in ("START", "VERIFY"):
            self.assertEqual(self.inspect(assurance, action, "DATA").status_code, 403)
        self.assertFalse(assurance.review_history.filter(action="VERIFY").exists())

    def test_anonymous_inspection_cannot_write(self):
        assurance = self.submitted()
        response = self.client.post(f"/api/v1/assurances/{assurance.pk}/inspection/", {
            "action": "NOTE", "section": "DATA", "review_notes": "Denied",
        }, format="json")
        self.assertEqual(response.status_code, 401)

    def test_only_superadmin_can_provision_dealers_accounts_and_assignments(self):
        for user in (self.owner, self.agent, self.admin):
            self.client.force_authenticate(user)
            for endpoint in ("dealers/", "dealers/assignments/", "auth/manage/"):
                response = self.client.post(f"/api/v1/{endpoint}", {}, format="json")
                self.assertEqual(response.status_code, 403)
        self.client.force_authenticate(self.superadmin)
        response = self.client.post("/api/v1/auth/manage/", {
            "username": "synthetic_new_agent", "email": "new-agent@example.test", "role": "AGENT",
            "password": "LongSyntheticProvision!2026", "is_active": True,
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotIn("password", response.data)

    def test_cross_dealer_and_revoked_assignment_cannot_read_or_inspect(self):
        assurance = create_assurance_draft(self.admin, self.payload(dealer=self.other_dealer))
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.admin)
        self.assertEqual(self.inspect(assurance).status_code, 404)
        self.client.force_authenticate(self.agent)
        self.assertEqual(self.client.get(f"/api/v1/assurances/{assurance.pk}/").status_code, 404)
        own = self.submitted()
        self.agent.dealer_assignments.all().delete()
        self.assertEqual(self.inspect(own).status_code, 404)
        with self.assertRaises(PermissionDenied):
            inspect_assurance(own, self.agent, {"action": "NOTE", "section": "DATA", "review_notes": "x"})

    def test_notes_sections_and_action_validation(self):
        assurance = self.submitted()
        for notes in ("", "  ", None, "x" * 2001):
            self.assertEqual(self.inspect(assurance, notes=notes).status_code, 400)
        for action, section in (("VERIFY", "GENERAL"), ("START", "GENERAL"),
                                ("APPROVE", "DATA"), ("NOTE", "PASSWORD")):
            self.assertEqual(self.inspect(assurance, action, section, user=self.admin).status_code, 400)
        self.assertEqual(assurance.review_history.count(), 1)

    def test_documents_cannot_be_verified_before_data_or_with_missing_file(self):
        assurance = self.submitted()
        self.assertEqual(self.inspect(assurance, "VERIFY", user=self.admin).status_code, 400)
        self.assertEqual(self.inspect(assurance, "VERIFY", "DATA", user=self.admin).status_code, 200)
        assurance.documents.filter(document_type="KTP").delete()
        self.assertEqual(self.inspect(assurance, "VERIFY", user=self.admin).status_code, 422)
        assurance.refresh_from_db()
        self.assertFalse(assurance.documents_verified)

    def test_resubmission_resets_flags_preserves_old_notes_and_accepts_fresh_review(self):
        assurance = self.submitted()
        self.inspect(assurance, "VERIFY", "DATA", user=self.admin)
        self.inspect(assurance, "VERIFY", "DOCUMENTS", user=self.admin)
        self.assertEqual(self.inspect(assurance, "REQUEST_REVISION").status_code, 200)
        before = assurance.review_history.count()
        self.assertEqual(self.post_action(assurance, "submit").status_code, 200)
        assurance.refresh_from_db()
        self.assertEqual(assurance.verification_stage, "WAITING")
        self.assertFalse(assurance.data_verified or assurance.documents_verified)
        self.assertEqual(assurance.review_history.count(), before + 1)
        self.assertTrue(assurance.review_history.filter(review_notes="KTP kurang jelas").exists())
        response = self.post_action(assurance, "review", {"decision": "APPROVE"}, user=self.superadmin)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["data_verified"])
        self.assertTrue(response.data["data"]["documents_verified"])

    def test_final_rejection_and_explicit_revision_require_reasons(self):
        assurance = self.submitted()
        for decision in ("REQUEST_REVISION", "REJECT_FINAL"):
            for notes in ("", "  ", None):
                self.assertEqual(self.post_action(assurance, "review", {
                    "decision": decision, "review_notes": notes,
                }, user=self.admin).status_code, 400)
        response = self.post_action(assurance, "review", {
            "decision": "REQUEST_REVISION", "review_notes": "Perbaiki nama",
        }, user=self.admin)
        self.assertEqual(response.data["data"]["status"], "REVISION")

    def test_final_rejection_audit_failure_and_stale_decisions(self):
        assurance = self.submitted()
        before = assurance.review_history.count()
        with patch("apps.audit.services.audit_service.AuditLog.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            response = self.post_action(assurance, "review", {
                "decision": "REJECT_FINAL", "review_notes": "Tidak memenuhi",
            }, user=self.superadmin)
        self.assertEqual(response.status_code, 503)
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "SUBMITTED")
        self.assertEqual(assurance.review_history.count(), before)
        self.assertEqual(self.post_action(assurance, "review", {
            "decision": "REJECT_FINAL", "review_notes": "Tidak memenuhi",
        }, user=self.superadmin).status_code, 200)
        self.assertEqual(self.post_action(assurance, "review", {"decision": "APPROVE"}, user=self.admin).status_code, 400)
        self.assertFalse(AssuranceNumberSequence.objects.exists())

    def test_inspection_metadata_audit_excludes_free_text(self):
        assurance = self.submitted()
        self.assertEqual(self.inspect(assurance).status_code, 200)
        audit = AuditLog.objects.get(action="INSPECT")
        self.assertNotIn("KTP kurang jelas", str(audit.changes))
        self.assertTrue(audit.changes["review_notes_present"])

    def test_only_submitted_can_receive_review_even_from_superadmin(self):
        assurance = self.draft()
        for status in ("DRAFT", "REVISION", "ACTIVE", "REJECTED"):
            assurance.status = status
            assurance.save(update_fields=["status"])
            self.assertEqual(self.inspect(assurance, user=self.superadmin).status_code, 400)

    def test_verification_flags_and_history_cannot_be_patched_by_dealer(self):
        assurance = self.draft()
        self.client.force_authenticate(self.owner)
        response = self.client.patch(f"/api/v1/assurances/{assurance.pk}/", {
            "data_verified": True, "documents_verified": True,
            "verification_stage": "COMPLETE", "review_history": [{"action": "APPROVE"}],
        }, format="json")
        self.assertEqual(response.status_code, 200)
        assurance.refresh_from_db()
        self.assertFalse(assurance.data_verified or assurance.documents_verified)
        self.assertEqual(assurance.review_history.count(), 0)
