"""Regression tests for bounded multipart uploads, sharded vault lock, and defaults."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.documents.services.recovery_service import reconcile_vault
from apps.documents.services.vault_lock import vault_write_lock
from apps.documents.test_images import jpeg_bytes


class DocumentAuditRemediationTests(TransactionTestCase):
    payload = AssuranceFeatureTestCase.payload
    draft = AssuranceFeatureTestCase.draft

    def setUp(self):
        AssuranceFeatureTestCase.setUpTestData.__func__(type(self))
        self.temp_root = Path(self.enterContext(TemporaryDirectory()))
        self.media = self.temp_root / "media"
        self.upload_tmp = self.temp_root / "tmp"
        self.media.mkdir()
        self.upload_tmp.mkdir()
        self.enterContext(override_settings(
            MEDIA_ROOT=str(self.media), FILE_UPLOAD_TEMP_DIR=str(self.upload_tmp),
        ))
        self.assurance = self.draft()
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def test_oversized_or_over_batch_multipart_aborts_before_disk_spooling(self):
        files = [SimpleUploadedFile(f"f{idx}.jpg", jpeg_bytes()) for idx in range(11)]
        over_batch = self.client.post(f"/api/v1/assurances/{self.assurance.pk}/documents/batch/", {
            "document_types": ["KTP"] * 11, "files": files,
        }, format="multipart")
        self.assertEqual(over_batch.status_code, 400)
        self.assertFalse(list(self.upload_tmp.iterdir()))

        huge = SimpleUploadedFile("huge.jpg", b"\xff\xd8\xff" + b"0" * (5 * 1024 * 1024 + 64))
        over_size = self.client.post(f"/api/v1/assurances/{self.assurance.pk}/documents/", {
            "document_type": "KTP", "file": huge,
        }, format="multipart")
        self.assertEqual(over_size.status_code, 400)
        self.assertFalse(list(self.upload_tmp.iterdir()))

    def test_long_filename_and_control_char_rejected_400(self):
        from rest_framework.exceptions import ValidationError
        from apps.documents.services.vault_service import store_document_to_vault

        for bad_name in ("a" * 256 + ".jpg", "bad\x07name.jpg"):
            bad_file = SimpleUploadedFile("ok.jpg", jpeg_bytes(), content_type="image/jpeg")
            bad_file._name = bad_name
            with self.assertRaises(ValidationError):
                store_document_to_vault(self.assurance, "KTP", bad_file)
            http_resp = self.client.post(f"/api/v1/assurances/{self.assurance.pk}/documents/", {
                "document_type": "KTP", "file": SimpleUploadedFile(bad_name, jpeg_bytes(), content_type="image/jpeg"),
            }, format="multipart")
            if http_resp.status_code == 201:
                saved = http_resp.data["data"]["original_filename"]
                self.assertLessEqual(len(saved), 255)
                self.assertFalse(any(ord(ch) < 32 or ord(ch) == 127 for ch in saved))
            else:
                self.assertEqual(http_resp.status_code, 400)

    def test_vault_lock_stays_one_byte_and_scopes_do_not_starve_reconcile(self):
        second = self.draft()
        for _ in range(3):
            with vault_write_lock(scope=str(self.assurance.pk), shared=True):
                with vault_write_lock(scope=str(second.pk), shared=True):
                    pass
        lock_file = self.media / ".vault-write.lock"
        if os.name != "nt":
            self.assertEqual(lock_file.stat().st_size, 1)
        self.assertEqual(reconcile_vault(0)["orphan_candidates"], 0)

    def test_wsgi_and_asgi_default_to_production_settings(self):
        base = Path(__file__).resolve().parents[2] / "core"
        for name in ("wsgi.py", "asgi.py"):
            content = (base / name).read_text(encoding="utf-8")
            self.assertIn("core.production_settings", content)

    def test_production_settings_strips_hosts_and_disables_browsable_renderer(self):
        import importlib
        import sys

        env = {
            "DJANGO_SECRET_KEY": "x" * 60,
            "DJANGO_ALLOWED_HOSTS": " app.example.test , api.example.test ",
            "DJANGO_TRUSTED_ORIGINS": " https://app.example.test ",
            "POSTGRES_DB": "db", "POSTGRES_USER": "user",
            "POSTGRES_PASSWORD": "pw", "POSTGRES_HOST": "127.0.0.1",
            "KEVIN_MEDIA_ROOT": str(self.media),
        }
        sys.modules.pop("core.production_settings", None)
        with patch.dict(os.environ, env, clear=False):
            prod = importlib.import_module("core.production_settings")
            self.assertEqual(prod.ALLOWED_HOSTS, ["app.example.test", "api.example.test"])
            self.assertEqual(prod.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"],
                             ("rest_framework.renderers.JSONRenderer",))
