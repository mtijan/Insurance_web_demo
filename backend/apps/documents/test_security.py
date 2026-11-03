"""Storage failures, vault containment and real upload-to-approval evidence."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.exceptions import ValidationError

from apps.assurances.models import AssuranceNumberSequence
from apps.assurances.services.workflow_service import submit_assurance_application
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.documents.services.vault_service import cleanup_vault_file


class DocumentSecurityTests(AssuranceFeatureTestCase):
    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.media = Path(directory)
        self.enterContext(override_settings(MEDIA_ROOT=directory))

    def test_all_sop_executable_extensions_are_rejected_even_with_image_magic(self):
        assurance = self.draft()
        self.client.force_authenticate(self.owner)
        for extension in ("exe", "SH", "bat", "php", "js"):
            with self.subTest(extension=extension):
                response = self.client.post(f"/api/v1/assurances/{assurance.pk}/documents/", {
                    "document_type": "KTP", "file": SimpleUploadedFile(
                        f"blocked.{extension}", b"\xff\xd8\xff\xe0" + b"\0" * 32, content_type="image/jpeg"),
                }, format="multipart")
                self.assertEqual(response.status_code, 400)
        self.assertFalse(assurance.documents.exists())

    def test_real_upload_submit_approve_stream_with_real_logins_and_csrf(self):
        from rest_framework.test import APIClient

        assurance = self.draft()
        self.owner.set_password("Workflow-real-password-938!")
        self.owner.save()
        self.client = APIClient(enforce_csrf_checks=True)
        csrf = self.client.get("/api/v1/auth/csrf/").data["data"]["csrf_token"]
        response = self.client.post("/api/v1/auth/login/", {
            "username": self.owner.username, "password": "Workflow-real-password-938!",
        }, HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 200)
        self.upload_real_documents_with_cookie(assurance, response.data["data"]["csrf_token"])
        csrf = self.client.get("/api/v1/auth/csrf/").data["data"]["csrf_token"]
        self.assertEqual(self.client.post(f"/api/v1/assurances/{assurance.pk}/submit/", HTTP_X_CSRFTOKEN=csrf).status_code, 200)
        self.admin.set_password("Workflow-admin-password-938!")
        self.admin.save()
        response = self.client.post("/api/v1/auth/token/", {"username": self.admin.username, "password": "Workflow-admin-password-938!"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['access_token']}")
        response = self.client.post(f"/api/v1/assurances/{assurance.pk}/review/", {"decision": "APPROVE"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["status"], "ACTIVE")

    def upload_real_documents_with_cookie(self, assurance, csrf):
        from io import BytesIO
        from PIL import Image
        from apps.documents.services.document_validator import get_required_document_types

        for document_type in get_required_document_types(assurance.vehicle_category):
            content = BytesIO()
            Image.new("RGB", (2, 2)).save(content, format="PNG")
            response = self.client.post(f"/api/v1/assurances/{assurance.pk}/documents/", {
                "document_type": document_type,
                "file": SimpleUploadedFile("real.png", content.getvalue(), content_type="image/png"),
            }, format="multipart", HTTP_X_CSRFTOKEN=csrf)
            self.assertEqual(response.status_code, 201, response.data)

    def test_missing_file_at_approval_is_422_and_does_not_allocate_number(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        document = assurance.documents.get(document_type="KTP")
        (self.media / document.file_path).unlink()
        response = self.post_action(assurance, "review", {"decision": "APPROVE"}, user=self.admin)
        self.assertEqual(response.status_code, 422)
        self.assertIn("KTP", response.data["missing_documents"])
        self.assertFalse(AssuranceNumberSequence.objects.exists())

    def test_storage_permission_failure_is_generic_503_without_status_change(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        with patch("pathlib.Path.open", side_effect=PermissionError("private storage path")):
            response = self.post_action(assurance, "submit")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private storage path", str(response.data))
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "DRAFT")

    def test_storage_failure_at_approval_rolls_back_status_and_counter(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        with patch("pathlib.Path.open", side_effect=PermissionError("private storage path")):
            response = self.post_action(assurance, "review", {"decision": "APPROVE"}, user=self.admin)
        self.assertEqual(response.status_code, 503)
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "SUBMITTED")
        self.assertFalse(AssuranceNumberSequence.objects.exists())

    def test_corrupt_metadata_cannot_read_delete_or_cleanup_outside_vault(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        document = assurance.documents.first()
        outside = self.media / "outside.txt"
        outside.write_text("synthetic sentinel")
        for value in (str(outside.resolve()), "vault/../../outside.txt", "outside.txt"):
            with self.subTest(value=value):
                document.file_path = value
                document.save()
                self.client.force_authenticate(self.owner)
                url = f"/api/v1/assurances/{assurance.pk}/documents/{document.pk}/"
                self.assertIn(self.client.get(url + "view/").status_code, (400, 404))
                self.assertEqual(self.client.delete(url).status_code, 400)
                with self.assertRaises(ValidationError):
                    cleanup_vault_file(value)
                self.assertTrue(outside.exists())
        self.assertTrue(assurance.documents.filter(pk=document.pk).exists())

    def test_stream_cache_policy_and_malformed_uuid_delete(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        document = assurance.documents.first()
        self.client.force_authenticate(self.owner)
        url = f"/api/v1/assurances/{assurance.pk}/documents/"
        response = self.client.get(f"{url}{document.pk}/view/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        expected = (self.media / document.file_path).read_bytes()
        self.assertEqual(b"".join(response.streaming_content), expected)
        self.assertTrue(response.closed)
        self.assertIn(self.client.delete(url + "abc/").status_code, (400, 404))

    def test_upload_size_and_binary_validation_remain_enforced(self):
        assurance = self.draft()
        self.client.force_authenticate(self.owner)
        for content in (b"MZ invalid executable", b"\xff\xd8\xff" + b"0" * 32,
                        b"\xff\xd8\xff" + b"0" * (5 * 1024 * 1024)):
            response = self.client.post(f"/api/v1/assurances/{assurance.pk}/documents/", {
                "document_type": "KTP", "file": SimpleUploadedFile("input.jpg", content),
            }, format="multipart")
            self.assertEqual(response.status_code, 400)
        self.assertFalse(assurance.documents.exists())
