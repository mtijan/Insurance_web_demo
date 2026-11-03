from io import BytesIO
from unittest.mock import patch

from django.db import DatabaseError
from pypdf import PdfReader

from apps.assurances.models import VehicleAssurance
from apps.assurances.services.workflow_service import review_assurance, submit_assurance_application
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.users.models import CustomUser


class SummaryPDFTests(AssuranceFeatureTestCase):
    def active(self):
        assurance = self.draft(policy_holder_name="Élodie O'Neil-Santoso.")
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        return review_assurance(assurance, self.admin, {"decision": "APPROVE"})

    def url(self, assurance):
        return f"/api/v1/assurances/{assurance.pk}/summary-pdf/"

    def test_active_summary_content_minimization_headers_and_audit(self):
        assurance = self.active()
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.url(assurance))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        reader = PdfReader(BytesIO(response.content))
        self.assertEqual(len(reader.pages), 1)
        text = reader.pages[0].extract_text()
        for value in (assurance.assurance_number, assurance.policy_holder.full_name,
                      assurance.dealer.name, "ACTIVE", "435,000.00", "Ringkasan Jaminan Aktif"):
            self.assertIn(value, text)
        self.assertNotIn(assurance.policy_holder.nik, text)
        self.assertNotIn("vault", text)
        self.assertEqual(AuditLog.objects.get(action="DOWNLOAD").changes, {"format": "PDF_SUMMARY"})

    def test_anonymous_cross_dealer_unassigned_agent_denied_no_download_audit(self):
        assurance = self.active()
        self.assertEqual(self.client.get(self.url(assurance)).status_code, 401)
        outsider = CustomUser.objects.create_user(username="outside", role="DEALER", dealer=self.other_dealer)
        self.client.force_authenticate(outsider)
        self.assertEqual(self.client.get(self.url(assurance)).status_code, 404)
        self.agent.dealer_assignments.all().delete()
        self.client.force_authenticate(self.agent)
        self.assertEqual(self.client.get(self.url(assurance)).status_code, 404)
        self.assertFalse(AuditLog.objects.filter(action="DOWNLOAD").exists())

    def test_all_scoped_roles_can_download_and_other_statuses_cannot(self):
        assurance = self.active()
        for user in (self.owner, self.agent, self.admin, self.superadmin):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.url(assurance)).status_code, 200)
        for status in ("DRAFT", "REVISION", "SUBMITTED", "APPROVED", "REJECTED"):
            VehicleAssurance.objects.filter(pk=assurance.pk).update(status=status)
            self.assertEqual(self.client.get(self.url(assurance)).status_code, 400)

    def test_audit_failure_does_not_return_pdf_or_partial_audit(self):
        assurance = self.active()
        self.client.force_authenticate(self.owner)
        before = AuditLog.objects.count()
        with patch("apps.audit.services.audit_service.AuditLog.objects.create", side_effect=DatabaseError("private")):
            response = self.client.get(self.url(assurance))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"%PDF", response.content)
        self.assertEqual(AuditLog.objects.count(), before)

    def test_boundary_content_wraps_without_page_overflow(self):
        import fitz
        assurance = self.active()
        assurance.policy_holder.full_name = "W" * 100
        assurance.policy_holder.save()
        assurance.dealer.name = "D" * 100
        assurance.dealer.save()
        assurance.vehicle_object = "V" * 50
        assurance.save()
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.url(assurance))
        pdf = fitz.open(stream=response.content, filetype="pdf")
        self.assertEqual(len(pdf), 1)
        for page in pdf:
            boxes = [fitz.Rect(word[:4]) for word in page.get_text("words")]
            self.assertTrue(all(box.x0 >= 40 and box.x1 <= page.rect.width - 40 for box in boxes))
            self.assertTrue(all(box.y0 >= 30 and box.y1 <= page.rect.height - 30 for box in boxes))

    def test_unsupported_unicode_font_fails_closed_without_incorrect_pdf(self):
        assurance = self.active()
        assurance.policy_holder.full_name = "李 小明"
        assurance.policy_holder.save()
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.url(assurance))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"%PDF", response.content)
        self.assertFalse(AuditLog.objects.filter(action="DOWNLOAD").exists())
