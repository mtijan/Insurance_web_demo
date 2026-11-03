from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class PasswordStateMigrationTests(TransactionTestCase):
    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_forward_existing_password_sessions_and_rollback_compatibility(self):
        old = [("users", "0002_quality_integrity")]
        new = [("users", "0003_first_login_password")]
        apps = self.migrate(old)
        user = apps.get_model("users", "CustomUser").objects.create(
            username="legacy-compatible", password="synthetic-hash-preserved", email="legacy@example.test",
        )
        apps = self.migrate(new)
        current = apps.get_model("users", "CustomUser").objects.get(pk=user.pk)
        self.assertFalse(current.must_change_password)
        self.assertEqual(current.password, "synthetic-hash-preserved")
        current.must_change_password = True
        current.save()
        with self.assertRaisesMessage(RuntimeError, "Rollback blocked"):
            self.migrate(old)
        current.must_change_password = False
        current.save()
        apps = self.migrate(old)
        current = apps.get_model("users", "CustomUser").objects.get(pk=user.pk)
        self.assertEqual(current.password, "synthetic-hash-preserved")
        apps = self.migrate(new)
        self.assertFalse(apps.get_model("users", "CustomUser").objects.get(pk=user.pk).must_change_password)
