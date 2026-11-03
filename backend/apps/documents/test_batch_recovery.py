"""Aggregate metadata/audit rollback and supported filesystem compensation/recovery."""
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import DatabaseError, transaction
from django.test import override_settings
from rest_framework.exceptions import ValidationError

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.documents.services.document_write_service import upload_assurance_documents
from apps.documents.services.recovery_service import reconcile_vault
from apps.documents.services.vault_paths import StorageUnavailable
from apps.documents.test_images import jpeg_bytes


class BatchRecoveryTests(AssuranceFeatureTestCase):
    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.media = Path(directory)
        self.enterContext(override_settings(MEDIA_ROOT=directory))
        self.assurance = self.draft()

    def image(self):
        return SimpleUploadedFile("synthetic.jpg", jpeg_bytes(), content_type="image/jpeg")

    def batch(self, user=None, types=None):
        self.client.force_authenticate(user or self.owner)
        return self.client.post(f"/api/v1/assurances/{self.assurance.pk}/documents/batch/", {
            "document_types": types or ["KTP", "SURAT_JALAN"],
            "files": [self.image(), self.image()],
        }, format="multipart")

    def test_batch_success_commits_each_metadata_and_audit(self):
        response = self.batch()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data["data"]), 2)
        self.assertEqual(self.assurance.documents.count(), 2)
        self.assertEqual(AuditLog.objects.filter(entity_name="DOCUMENT").count(), 2)
        self.assertEqual(len(list(self.media.rglob("*.jpg"))), 2)

    def test_second_invalid_file_rolls_back_all_batch_files_metadata_and_audit(self):
        items = [("KTP", self.image()), ("SURAT_JALAN", SimpleUploadedFile("bad.jpg", b"invalid"))]
        with self.assertRaises(ValidationError):
            upload_assurance_documents(self.assurance, self.owner, items)
        self.assertFalse(self.assurance.documents.exists())
        self.assertFalse(AuditLog.objects.filter(entity_name="DOCUMENT").exists())
        self.assertFalse(list(self.media.rglob("*.jpg")))

    def test_second_audit_failure_is_atomic_and_preserves_existing_documents(self):
        self.assertEqual(self.batch().status_code, 201)
        previous = set(self.assurance.documents.values_list("pk", flat=True))
        original, calls = AuditLog.objects.create, []

        def fail_second(**kwargs):
            calls.append(kwargs)
            if len(calls) == 2:
                raise DatabaseError("synthetic second audit failure")
            return original(**kwargs)

        with patch("apps.audit.services.audit_service.AuditLog.objects.create", side_effect=fail_second):
            response = self.batch()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(set(self.assurance.documents.values_list("pk", flat=True)), previous)
        self.assertEqual(len(list(self.media.rglob("*.jpg"))), 2)
        self.assertEqual(AuditLog.objects.filter(entity_name="DOCUMENT").count(), 2)

    def test_batch_mismatch_invalid_type_peer_and_noneditable_rejected(self):
        self.assertEqual(self.batch(types=["KTP"]).status_code, 400)
        self.assertEqual(self.batch(types=["KTP", "INVALID"]).status_code, 400)
        self.assertEqual(self.batch(user=self.peer).status_code, 403)
        self.assurance.status = "ACTIVE"
        self.assurance.save()
        self.assertEqual(self.batch(user=self.admin).status_code, 400)
        self.assertFalse(self.assurance.documents.exists())
        self.assertFalse(list(self.media.rglob("*.jpg")))

    def test_nested_non_durable_transaction_is_rejected_before_file_write(self):
        with transaction.atomic():
            with self.assertRaisesMessage(RuntimeError, "durable"):
                upload_assurance_documents(self.assurance, self.owner, [("KTP", self.image())])
        self.assertFalse(self.assurance.documents.exists())
        self.assertFalse(list(self.media.rglob("*.jpg")))

    def orphan(self):
        path = self.media / "vault" / str(self.assurance.pk) / f"{uuid4().hex}.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(jpeg_bytes())
        return path

    def test_dryrun_apply_age_reference_and_unknown_file_safety(self):
        self.batch()
        orphan = self.orphan()
        sentinel = orphan.parent / "operator-sentinel.txt"
        sentinel.write_text("synthetic unrelated file")
        self.assertEqual(reconcile_vault(3600, apply=True)["removed"], 0)
        self.assertEqual(reconcile_vault(0)["orphan_candidates"], 1)
        self.assertTrue(orphan.exists())
        result = reconcile_vault(0, apply=True)
        self.assertEqual(result["removed"], 1)
        self.assertTrue(sentinel.exists())
        self.assertEqual(len(list(self.media.rglob("*.jpg"))), 2)
        self.assertEqual(reconcile_vault(0, apply=True)["removed"], 0)

    def test_crash_after_file_write_recovery_and_missing_reference_report(self):
        self.batch()
        path = self.media / "vault" / str(self.assurance.pk) / f"{uuid4().hex}.jpg"
        command = "import os,sys; from pathlib import Path; Path(sys.argv[1]).write_bytes(b'synthetic-partial'); os._exit(29)"
        process = subprocess.run([sys.executable, "-c", command, str(path)], timeout=10, capture_output=True)
        self.assertEqual(process.returncode, 29)
        existing = self.assurance.documents.first()
        (self.media / existing.file_path).unlink()
        result = reconcile_vault(0, apply=True)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["missing_referenced"], 1)
        self.assertTrue(self.assurance.documents.filter(pk=existing.pk).exists())

    def test_cleanup_failure_is_recoverable_without_partial_database_changes(self):
        with patch("apps.documents.services.document_write_service.cleanup_vault_file", side_effect=OSError("synthetic")):
            with self.assertRaises(ValidationError):
                upload_assurance_documents(self.assurance, self.owner,
                                           [("KTP", self.image()), ("INVALID", self.image())])
        self.assertFalse(self.assurance.documents.exists())
        self.assertFalse(AuditLog.objects.filter(entity_name="DOCUMENT").exists())
        self.assertEqual(reconcile_vault(0, apply=True)["removed"], 1)

    @override_settings(VAULT_LOCK_TIMEOUT=.05)
    def test_recovery_cannot_race_an_active_supported_writer(self):
        path = self.orphan()
        with patch("apps.documents.services.vault_lock.lock_once", side_effect=OSError("locked")):
            with self.assertRaises(StorageUnavailable):
                reconcile_vault(0, apply=True)
        self.assertTrue(path.exists())

    def test_recovery_command_dryrun_does_not_expose_paths_or_data(self):
        path = self.orphan()
        output = StringIO()
        call_command("reconcile_vault", grace_seconds=0, stdout=output)
        self.assertEqual(json.loads(output.getvalue())["removed"], 0)
        self.assertNotIn(str(path), output.getvalue())
        self.assertTrue(path.exists())
