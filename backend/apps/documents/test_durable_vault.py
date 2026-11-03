"""Actual commits and interprocess OS locks, outside TestCase's enclosing transaction."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import subprocess
import sys
from time import monotonic, sleep
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, DatabaseError
from django.test import TransactionTestCase, override_settings

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.documents.services.document_write_service import upload_assurance_documents, remove_assurance_document
from apps.documents.services.recovery_service import reconcile_vault
from apps.documents.services.vault_paths import StorageUnavailable
from apps.documents.test_images import jpeg_bytes


class DurableVaultTests(TransactionTestCase):
    payload = AssuranceFeatureTestCase.payload
    draft = AssuranceFeatureTestCase.draft

    def setUp(self):
        AssuranceFeatureTestCase.setUpTestData.__func__(type(self))
        directory = self.enterContext(TemporaryDirectory())
        self.media = Path(directory)
        self.enterContext(override_settings(MEDIA_ROOT=directory))
        self.assurance = self.draft()

    def upload(self):
        image = SimpleUploadedFile("synthetic.jpg", jpeg_bytes(), content_type="image/jpeg")
        return upload_assurance_documents(self.assurance, self.owner, [("KTP", image)])[0]

    def test_commit_failure_compensates_file_and_database_and_audit(self):
        with patch.object(connection, "commit", side_effect=DatabaseError("synthetic commit failure")):
            with self.assertRaises(DatabaseError):
                self.upload()
        self.assertFalse(self.assurance.documents.exists())
        self.assertFalse(AuditLog.objects.filter(entity_name="DOCUMENT").exists())
        self.assertFalse(list(self.media.rglob("*.jpg")))

    def test_post_commit_delete_failure_is_recovered_idempotently(self):
        document = self.upload()
        with patch("pathlib.Path.unlink", side_effect=OSError("synthetic unlink failure")):
            remove_assurance_document(self.assurance, self.owner, document.pk)
        self.assertFalse(self.assurance.documents.exists())
        self.assertTrue((self.media / document.file_path).exists())
        self.assertEqual(AuditLog.objects.filter(action="DELETE", entity_name="DOCUMENT").count(), 1)
        self.assertEqual(reconcile_vault(0, apply=True)["removed"], 1)
        self.assertEqual(reconcile_vault(0, apply=True)["removed"], 0)

    @override_settings(VAULT_LOCK_TIMEOUT=.05)
    def test_recovery_excludes_another_process_holding_real_vault_lock(self):
        (self.media / "vault" / str(self.assurance.pk)).mkdir(parents=True)
        orphan = self.media / "vault" / str(self.assurance.pk) / f"{uuid4().hex}.jpg"
        orphan.write_bytes(jpeg_bytes())
        ready = self.media / "ready"
        code = ("import sys,os; os.environ['DJANGO_SETTINGS_MODULE']='core.settings'; "
                "import django; django.setup(); from pathlib import Path; from django.conf import settings; "
                "settings.MEDIA_ROOT=sys.argv[1]; "
                "from apps.documents.services.vault_lock import vault_write_lock; "
                "ctx=vault_write_lock(); ctx.__enter__(); Path(sys.argv[2]).touch(); "
                "sys.stdin.readline(); ctx.__exit__(None,None,None)")
        process = subprocess.Popen([sys.executable, "-c", code, str(self.media), str(ready)], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = monotonic() + 5
            while not ready.exists() and monotonic() < deadline:
                sleep(.02)
            self.assertTrue(ready.exists())
            with self.assertRaises(StorageUnavailable):
                reconcile_vault(0, apply=True)
            self.assertTrue(orphan.exists())
        finally:
            process.communicate(input=b"\n", timeout=8)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(reconcile_vault(0, apply=True)["removed"], 1)
