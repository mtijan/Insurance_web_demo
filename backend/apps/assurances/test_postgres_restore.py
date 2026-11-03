"""Synthetic pg_dump/pg_restore to a newly created, verified owned database."""
import hashlib
from contextlib import closing
import os
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
from unittest import skipUnless
from uuid import uuid4

from django.conf import settings
from django.db import connection
from django.test import TransactionTestCase, override_settings
import psycopg2

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.documents.services.document_write_service import upload_assurance_document
from apps.documents.services.vault_lock import vault_write_lock
from apps.documents.test_images import jpeg_bytes
from django.core.files.uploadedfile import SimpleUploadedFile


@skipUnless(connection.vendor == "postgresql", "PostgreSQL restore requires PostgreSQL")
class PostgreSQLRestoreTests(TransactionTestCase):
    payload = AssuranceFeatureTestCase.payload
    draft = AssuranceFeatureTestCase.draft

    def owned(self, name):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=%s", [name])
            row = cursor.fetchone()
        return row[0] if row else None

    def preflight(self):
        config = connection.settings_dict
        source = config["NAME"]
        self.assertRegex(source, r"^test_ka_open_[a-f0-9]{12}$")
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(),current_user,host(inet_server_addr()),inet_server_port()")
            identity = cursor.fetchone()
        self.assertEqual(identity[:2], (source, "kevin_assurance_local"))
        self.assertIn(identity[2], {"127.0.0.1", "::1"})
        self.assertEqual(identity[3], int(config["PORT"]))
        self.assertEqual(self.owned(source), "kevin_assurance_local")
        return config

    def executable(self, name):
        found = shutil.which(name)
        path = Path(found) if found else Path("C:/Program Files/PostgreSQL/18/bin") / f"{name}.exe"
        self.assertTrue(path.is_file(), f"Required PostgreSQL utility missing: {name}")
        return str(path)

    def run_utility(self, args, config):
        environment = {**os.environ, "PGPASSWORD": config["PASSWORD"], "PGCONNECT_TIMEOUT": "5"}
        result = subprocess.run(args, env=environment, capture_output=True, timeout=45)
        self.assertEqual(result.returncode, 0, "PostgreSQL backup/restore utility failed; no raw output logged")

    def restore_and_verify(self, config, target, directory, assurance, document):
        dump = directory / "synthetic.dump"
        common = ["--host", config["HOST"], "--port", str(config["PORT"]), "--username", config["USER"], "--no-password"]
        with vault_write_lock():
            self.run_utility([self.executable("pg_dump"), *common, "--format=custom", "--file", str(dump), config["NAME"]], config)
            shutil.copytree(Path(settings.MEDIA_ROOT) / "vault", directory / "media-backup")
        self.run_utility([self.executable("pg_restore"), *common, "--exit-on-error", "--single-transaction",
                          "--no-owner", "--no-acl", "--dbname", target, str(dump)], config)
        with closing(psycopg2.connect(dbname=target, user=config["USER"], password=config["PASSWORD"], host=config["HOST"],
                                     port=config["PORT"], connect_timeout=5)) as restored:
            with restored.cursor() as cursor:
                cursor.execute("SELECT current_database(),current_user")
                self.assertEqual(cursor.fetchone(), (target, config["USER"]))
                cursor.execute("SELECT status,policy_holder_id FROM vehicle_assurance WHERE id=%s", [str(assurance.pk)])
                self.assertEqual(cursor.fetchone(), ("DRAFT", assurance.policy_holder_id))
                cursor.execute("SELECT count(*) FROM audit_log WHERE entity_name='DOCUMENT'")
                self.assertEqual(cursor.fetchone()[0], 1)
                cursor.execute("SELECT count(*) FROM assurance_document WHERE id=%s", [str(document.pk)])
                self.assertEqual(cursor.fetchone()[0], 1)
        shutil.copytree(directory / "media-backup", directory / "restored-media/vault")
        original = Path(settings.MEDIA_ROOT) / document.file_path
        recovered = directory / "restored-media" / document.file_path
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), hashlib.sha256(recovered.read_bytes()).hexdigest())
        print("Disposable restore verified:", {"source": config["NAME"], "target": target,
                                                "metadata_audit_media": "PASS", "runtime": "PostgreSQL 18 local"})

    def test_synthetic_database_and_media_backup_restore(self):
        config = self.preflight()
        AssuranceFeatureTestCase.setUpTestData.__func__(type(self))
        target = "test_ka_open_" + uuid4().hex[:12]
        self.assertIsNone(self.owned(target))
        with TemporaryDirectory(prefix="ka-restore-") as temporary:
            directory = Path(temporary)
            with override_settings(MEDIA_ROOT=directory / "source-media"):
                assurance = self.draft()
                image = SimpleUploadedFile("synthetic.jpg", jpeg_bytes(), content_type="image/jpeg")
                document = upload_assurance_document(assurance, self.owner, "KTP", image)
                with connection.cursor() as cursor:
                    cursor.execute("CREATE DATABASE " + connection.ops.quote_name(target))
                try:
                    self.assertEqual(self.owned(target), config["USER"])
                    self.restore_and_verify(config, target, directory, assurance, document)
                finally:
                    self.assertTrue(re.fullmatch(r"test_ka_open_[a-f0-9]{12}", target))
                    self.assertEqual(self.owned(target), config["USER"])
                    with connection.cursor() as cursor:
                        cursor.execute("DROP DATABASE " + connection.ops.quote_name(target))
                self.assertIsNone(self.owned(target))
                print("Disposable restore target removed:", target)
