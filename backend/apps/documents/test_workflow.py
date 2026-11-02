from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.test import override_settings

from apps.assurances.services.workflow_service import submit_assurance_application
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.documents.services.vault_service import store_document_to_vault
from apps.documents.test_images import jpeg_bytes


class DocumentWorkflowTests(AssuranceFeatureTestCase):
    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.media = Path(directory)
        self.enterContext(override_settings(MEDIA_ROOT=directory))

    def image(self, filename="test.jpg"):
        return SimpleUploadedFile(filename, jpeg_bytes(),
                                  content_type="image/jpeg")

    def upload(self, assurance, user=None):
        self.client.force_authenticate(user or self.owner)
        return self.client.post(f"/api/v1/assurances/{assurance.pk}/documents/", {
            "document_type": "KTP", "file": self.image(),
        }, format="multipart")

    def test_upload_creates_document_audit_and_removes_file_on_delete_commit(self):
        assurance = self.draft()
        self.assertEqual(self.upload(assurance).status_code, 201)
        document = assurance.documents.get()
        file_path = self.media / document.file_path
        self.assertTrue(file_path.exists())
        self.assertTrue(AuditLog.objects.filter(action="CREATE", entity_name="DOCUMENT").exists())
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(
                f"/api/v1/assurances/{assurance.pk}/documents/{document.pk}/",
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(file_path.exists())
        self.assertTrue(AuditLog.objects.filter(action="DELETE", entity_name="DOCUMENT").exists())

    def test_upload_audit_failure_rolls_back_metadata_and_cleans_file(self):
        assurance = self.draft()
        with patch("apps.audit.services.audit_service.AuditLog.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            response = self.upload(assurance)
        self.assertEqual(response.status_code, 503)
        self.assertFalse(assurance.documents.exists())
        self.assertFalse(list(self.media.rglob("*.jpg")))

    def test_failed_metadata_insert_cleans_written_file(self):
        assurance = self.draft()
        with patch("apps.documents.services.vault_service.AssuranceDocument.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            with self.assertRaises(DatabaseError):
                store_document_to_vault(assurance, "KTP", self.image())
        self.assertFalse(list(self.media.rglob("*.jpg")))

    def test_delete_audit_failure_preserves_metadata_and_file(self):
        assurance = self.draft()
        self.upload(assurance)
        document = assurance.documents.get()
        with patch("apps.audit.services.audit_service.AuditLog.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            response = self.client.delete(
                f"/api/v1/assurances/{assurance.pk}/documents/{document.pk}/",
            )
        self.assertEqual(response.status_code, 503)
        self.assertTrue(assurance.documents.filter(pk=document.pk).exists())
        self.assertTrue((self.media / document.file_path).exists())

    def test_submitted_document_upload_is_blocked_even_for_admin(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        self.assertEqual(self.upload(assurance, self.admin).status_code, 400)
        self.assertEqual(len(list(self.media.rglob("*.png"))), 4)

    def test_revision_allows_document_replacement(self):
        from apps.assurances.services.workflow_service import review_assurance

        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        review_assurance(assurance, self.admin, {"decision": "REJECT", "review_notes": "Replace KTP"})
        self.assertEqual(self.upload(assurance).status_code, 201)

    def test_detected_image_type_controls_stored_extension(self):
        assurance = self.draft()
        document = store_document_to_vault(assurance, "KTP", self.image("camera.bin"))
        self.assertEqual(Path(document.file_path).suffix, ".jpg")

    def test_upload_rejects_out_of_scope_and_peer_users(self):
        assurance = self.draft()
        self.assertEqual(self.upload(assurance, self.peer).status_code, 403)
        assurance.dealer = self.other_dealer
        assurance.save()
        self.assertEqual(self.upload(assurance).status_code, 404)
