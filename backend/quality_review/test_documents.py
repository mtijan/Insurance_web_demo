from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.assurances.test_support import AssuranceFeatureTestCase


class DocumentReviewTests(AssuranceFeatureTestCase):
    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=directory))
        self.media = Path(directory)

    def test_valid_header_with_executable_extension_is_rejected(self):
        assurance = self.draft()
        self.client.force_authenticate(self.owner)
        response = self.client.post(f"/api/v1/assurances/{assurance.pk}/documents/", {
            "document_type": "KTP", "file": SimpleUploadedFile(
                "blocked.exe", b"\xff\xd8\xff\xe0" + b"\x00" * 32, content_type="image/jpeg",
            ),
        }, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_malformed_document_uuid_returns_client_error(self):
        assurance = self.draft()
        self.client.force_authenticate(self.owner)
        self.client.raise_request_exception = False
        response = self.client.get(f"/api/v1/assurances/{assurance.pk}/documents/abc/view/")
        self.assertIn(response.status_code, (400, 404))

    def test_physical_file_reference_cannot_escape_media_root(self):
        assurance = self.draft()
        self.attach_documents(assurance)
        document = assurance.documents.first()
        target = self.media.parent / f"{self.media.name}-outside.txt"
        target.write_text("synthetic outside-vault sentinel", encoding="utf-8")
        self.addCleanup(target.unlink, missing_ok=True)
        document.file_path = str(target.resolve())
        document.save()
        self.client.force_authenticate(self.owner)
        response = self.client.get(
            f"/api/v1/assurances/{assurance.pk}/documents/{document.pk}/view/",
        )
        actual = response.status_code
        response.close()
        self.assertIn(actual, (400, 404))
