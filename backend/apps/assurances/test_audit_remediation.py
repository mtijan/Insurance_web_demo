"""Regression tests for deactivated dealers, 404 locks, orphaned PII, and reports."""
from io import BytesIO
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from PIL import Image

from apps.assurances.models import AssuranceStatus, PolicyHolder, VehicleAssurance
from apps.assurances.services.assurance_service import delete_assurance_draft, update_assurance_draft
from apps.assurances.services.inspection_service import inspect_assurance
from apps.assurances.services.workflow_service import review_assurance, submit_assurance_application
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.dealers.services.dealer_service import update_dealer
from apps.users.models import AuthSession

PASSWORD = "Synthetic-dealer-remediation-429!"


class AssuranceAuditRemediationTests(AssuranceFeatureTestCase):
    def png_file(self, name="doc.png"):
        buf = BytesIO()
        Image.new("RGB", (2, 2), "white").save(buf, format="PNG")
        return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")

    def test_deactivated_dealer_blocks_patch_docs_submit_and_dealer_sessions(self):
        self.owner.set_password(PASSWORD)
        self.owner.save()
        tokens = self.client.post("/api/v1/auth/token/", {
            "username": self.owner.username, "password": PASSWORD,
        }, format="json").data["data"]
        draft = self.draft()
        self.attach_uploaded_documents(draft)
        update_dealer(self.dealer, {"is_active": False}, actor=self.superadmin)

        self.assertFalse(AuthSession.objects.filter(user=self.owner, revoked_at__isnull=True).exists())
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/token/refresh/", {
            "refresh_token": tokens["refresh_token"],
        }, format="json").status_code, 401)
        self.client.credentials()
        self.assertEqual(self.client.post("/api/v1/auth/token/", {
            "username": self.owner.username, "password": PASSWORD,
        }, format="json").status_code, 400)

        doc_id = draft.documents.first().pk
        for actor in (self.agent, self.admin, self.superadmin):
            self.client.force_authenticate(actor)
            detail = self.client.get(f"/api/v1/assurances/{draft.pk}/").data["data"]
            self.assertFalse(detail["can_edit"])
            self.assertEqual(self.client.patch(f"/api/v1/assurances/{draft.pk}/", {
                "vehicle_object": "Updated Motor",
            }, format="json").status_code, 403)
            self.assertEqual(self.client.post(f"/api/v1/assurances/{draft.pk}/documents/", {
                "document_type": "KTP", "file": self.png_file(),
            }, format="multipart").status_code, 403)
            self.assertEqual(self.client.delete(
                f"/api/v1/assurances/{draft.pk}/documents/{doc_id}/",
            ).status_code, 403)
            self.assertEqual(self.client.post(f"/api/v1/assurances/{draft.pk}/submit/", {}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/assurances/{draft.pk}/").status_code, 200)

    def test_submitted_assurance_can_complete_review_after_dealer_deactivation(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        update_dealer(self.dealer, {"is_active": False}, actor=self.superadmin)
        reviewed = review_assurance(assurance, self.admin, {"decision": "REJECT_FINAL", "review_notes": "Closed."})
        self.assertEqual(reviewed.status, AssuranceStatus.REJECTED)

    def test_missing_assurance_returns_404_instead_of_unhandled_500(self):
        ghost = VehicleAssurance(pk=uuid4())
        with self.assertRaises(Http404):
            update_assurance_draft(ghost, self.admin, {"vehicle_object": "X"})
        with self.assertRaises(Http404):
            submit_assurance_application(ghost, self.admin)
        with self.assertRaises(Http404):
            inspect_assurance(ghost, self.admin, {"action": "START", "section": "DATA"})
        with self.assertRaises(Http404):
            review_assurance(ghost, self.admin, {"decision": "APPROVE"})
        with self.assertRaises(Http404):
            delete_assurance_draft(ghost, self.admin)

    def test_update_holder_cleans_up_unreferenced_prior_holder(self):
        assurance = self.draft()
        old_id = assurance.policy_holder_id
        updated = update_assurance_draft(assurance, self.owner, {"policy_holder_name": "Updated Holder"})
        self.assertNotEqual(updated.policy_holder_id, old_id)
        self.assertFalse(PolicyHolder.objects.filter(pk=old_id).exists())

    def test_pdf_sanitizes_control_whitespace_and_excel_sets_nosniff(self):
        assurance = self.draft(vehicle_object="Motor\x0bSport\x0cOne")
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        review_assurance(assurance, self.admin, {"decision": "APPROVE"})
        self.client.force_authenticate(self.superadmin)
        pdf = self.client.get(f"/api/v1/assurances/{assurance.pk}/summary-pdf/")
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        excel = self.client.get("/api/v1/assurances/export-excel/")
        self.assertEqual(excel.status_code, 200)
        self.assertEqual(excel["X-Content-Type-Options"], "nosniff")
