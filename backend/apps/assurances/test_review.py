from unittest.mock import patch

from django.db import DatabaseError

from apps.assurances.models import AssuranceNumberSequence
from apps.assurances.services.workflow_service import submit_assurance_application
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog


class ReviewTests(AssuranceFeatureTestCase):
    def submitted(self, **overrides):
        assurance = self.draft(**overrides)
        self.attach_uploaded_documents(assurance)
        return submit_assurance_application(assurance, self.owner)

    def review(self, assurance, decision="APPROVE", notes="Verified", user=None):
        return self.post_action(assurance, "review", {
            "decision": decision, "review_notes": notes,
        }, user=user or self.admin)

    def test_admin_approval_activates_and_issues_number(self):
        assurance = self.submitted()
        response = self.review(assurance)
        self.assertEqual(response.status_code, 200)
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "ACTIVE")
        self.assertEqual(assurance.assurance_number, "KAS-2026-00001")
        self.assertEqual(assurance.reviewed_by, self.admin)
        self.assertEqual(assurance.review_notes, "Verified")
        self.assertTrue(AuditLog.objects.filter(action="APPROVE", user=self.admin).exists())

    def test_superadmin_can_review(self):
        self.assertEqual(self.review(self.submitted(), user=self.superadmin).status_code, 200)

    def test_approve_notes_are_optional(self):
        response = self.post_action(self.submitted(), "review", {"decision": "APPROVE"},
                                    user=self.admin)
        self.assertEqual(response.status_code, 200)

    def test_reject_requires_nonblank_notes(self):
        assurance = self.submitted()
        for notes in ("", "   ", None):
            with self.subTest(notes=notes):
                self.assertEqual(self.review(assurance, "REJECT", notes).status_code, 400)
        self.assertEqual(self.post_action(assurance, "review", {"decision": "REJECT"},
                                          user=self.admin).status_code, 400)
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "SUBMITTED")

    def test_rejection_preserves_notes_and_allows_resubmission(self):
        assurance = self.submitted()
        self.assertEqual(self.review(assurance, "REJECT", "Replace frame photo").status_code, 200)
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "REVISION")
        self.assertEqual(assurance.review_notes, "Replace frame photo")
        self.assertIsNone(assurance.assurance_number)
        self.assertEqual(self.post_action(assurance, "submit").status_code, 200)
        self.assertEqual(self.review(assurance).status_code, 200)
        self.assertEqual(AuditLog.objects.filter(action="SUBMIT").count(), 2)
        self.assertEqual(AuditLog.objects.filter(action="REJECT").count(), 1)

    def test_dealer_and_agent_cannot_review(self):
        assurance = self.submitted()
        for user in (self.owner, self.agent):
            with self.subTest(role=user.role):
                self.assertEqual(self.review(assurance, user=user).status_code, 403)

    def test_anonymous_review_is_unauthorized(self):
        assurance = self.submitted()
        response = self.client.post(f"/api/v1/assurances/{assurance.pk}/review/",
                                    {"decision": "APPROVE"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_only_submitted_state_can_be_reviewed(self):
        assurance = self.draft()
        self.assertEqual(self.review(assurance).status_code, 400)
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        self.assertEqual(self.review(assurance).status_code, 200)
        for decision in ("APPROVE", "REJECT"):
            self.assertEqual(self.review(assurance, decision).status_code, 400)
        self.assertEqual(AssuranceNumberSequence.objects.get(year=2026).last_value, 1)

    def test_invalid_decision_is_rejected(self):
        self.assertEqual(self.review(self.submitted(), "DELETE").status_code, 400)

    def test_approval_revalidates_documents(self):
        assurance = self.submitted()
        assurance.documents.filter(document_type="KTP").delete()
        self.assertEqual(self.review(assurance).status_code, 422)
        self.assertFalse(AssuranceNumberSequence.objects.exists())

    def test_unique_numbers_increment_and_restart_each_year(self):
        for year, expected in ((2026, "00001"), (2026, "00002"), (2027, "00001")):
            assurance = self.submitted(issuance_year=year)
            response = self.review(assurance)
            self.assertEqual(response.data["data"]["assurance_number"], f"KAS-{year}-{expected}")

    def test_approval_audit_failure_rolls_back_number_and_status(self):
        assurance = self.submitted()
        with patch("apps.audit.services.audit_service.AuditLog.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            self.assertEqual(self.review(assurance).status_code, 503)
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "SUBMITTED")
        self.assertIsNone(assurance.assurance_number)
        self.assertIsNone(assurance.reviewed_by)
        self.assertFalse(AssuranceNumberSequence.objects.exists())

    def test_rejection_audit_failure_rolls_back_notes(self):
        assurance = self.submitted()
        with patch("apps.audit.services.audit_service.AuditLog.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            self.assertEqual(self.review(assurance, "REJECT", "Bad photo").status_code, 503)
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "SUBMITTED")
        self.assertFalse(assurance.review_notes)

    def test_admin_queue_filters_status(self):
        assurance = self.submitted()
        self.draft()
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/assurances/?status=SUBMITTED")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data["data"]], [str(assurance.pk)])
        self.assertEqual(self.client.get("/api/v1/assurances/?status=BAD").status_code, 400)

    def test_existing_official_number_is_not_reused(self):
        previous = self.draft()
        previous.status = "ACTIVE"
        previous.assurance_number = "KAS-2026-00042"
        previous.save()
        response = self.review(self.submitted())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["assurance_number"], "KAS-2026-00043")

    def test_rejection_error_matches_standard_envelope(self):
        response = self.review(self.submitted(), "REJECT", " ")
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error_code"], "VALIDATION_ERROR")
        self.assertIn("review_notes", response.data["errors"])
