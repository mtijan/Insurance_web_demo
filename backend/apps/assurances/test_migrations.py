"""Forward, preflight and rollback checks against disposable historical schemas."""
from datetime import date, timedelta

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone

OLD = [("assurances", "0002_assurancenumbersequence"), ("users", "0001_initial")]
NEW = [("assurances", "0003_quality_integrity"), ("users", "0002_quality_integrity")]


class QualityMigrationTests(TransactionTestCase):
    def setUp(self):
        self.migrate(OLD)

    def tearDown(self):
        self.migrate(NEW)
        super().tearDown()

    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def legacy_data(self, shared=False, invalid=False):
        apps = MigrationExecutor(connection).loader.project_state(OLD).apps
        dealer = apps.get_model("dealers", "Dealer").objects.create(code="LEGACY", name="Legacy")
        user = apps.get_model("users", "CustomUser").objects.create(username="legacy", email="legacy@example.test", role="ADMIN")
        holder = apps.get_model("assurances", "PolicyHolder").objects.create(nik="0000000000000001", full_name="Original")
        model = apps.get_model("assurances", "VehicleAssurance")
        values = dict(policy_holder=holder, dealer=dealer, created_by=user,
                      vehicle_category="MOTOR_BARU", coverage_type="TLO", sum_insured=-1 if invalid else 100,
                      tenor_years=1, base_premium=2, admin_fee=0, total_premium=2,
                      period_start=date(2026, 1, 1), period_end=date(2027, 1, 1), issuance_year=2026)
        first = model.objects.create(**values)
        model.objects.filter(pk=first.pk).update(created_at=timezone.now() - timedelta(days=1))
        if shared:
            model.objects.create(**values)
        return first.pk, holder.pk, user.pk

    def test_forward_migration_splits_shared_existing_holder_without_losing_values(self):
        first, holder, _ = self.legacy_data(shared=True)
        apps = self.migrate(NEW)
        assurances = apps.get_model("assurances", "VehicleAssurance").objects
        self.assertEqual(assurances.count(), 2)
        self.assertEqual(assurances.values("policy_holder_id").distinct().count(), 2)
        self.assertEqual(set(assurances.values_list("policy_holder__full_name", flat=True)), {"Original"})
        self.assertTrue(assurances.filter(pk=first, policy_holder_id=holder).exists())
        with self.assertRaisesMessage(RuntimeError, "Rollback blocked"):
            self.migrate(OLD)

    def test_reversible_schema_migration_preserves_nonshared_existing_transaction(self):
        identity, _, _ = self.legacy_data()
        self.migrate(NEW)
        apps = self.migrate(OLD)
        self.assertTrue(apps.get_model("assurances", "VehicleAssurance").objects.filter(pk=identity).exists())

    def test_invalid_financial_preflight_stops_without_deleting_data(self):
        identity, _, _ = self.legacy_data(invalid=True)
        with self.assertRaisesMessage(RuntimeError, "invalid financial rows"):
            self.migrate(NEW)
        apps = MigrationExecutor(connection).loader.project_state(OLD).apps
        rows = apps.get_model("assurances", "VehicleAssurance").objects
        self.assertEqual(rows.get(pk=identity).sum_insured, -1)
        rows.filter(pk=identity).update(sum_insured=100)

    def test_existing_fractional_currency_does_not_fail_preflight(self):
        identity, _, _ = self.legacy_data()
        apps = MigrationExecutor(connection).loader.project_state(OLD).apps
        apps.get_model("assurances", "VehicleAssurance").objects.filter(pk=identity).update(
            base_premium="20000.10", admin_fee="35000.20", total_premium="55000.30",
        )
        apps = self.migrate(NEW)
        row = apps.get_model("assurances", "VehicleAssurance").objects.get(pk=identity)
        self.assertEqual(str(row.total_premium), "55000.30")

    def test_duplicate_existing_email_blocks_constraint_without_changing_accounts(self):
        apps = MigrationExecutor(connection).loader.project_state(OLD).apps
        users = apps.get_model("users", "CustomUser").objects
        users.create(username="first", email="Legacy@example.test")
        second = users.create(username="second", email="legacy@example.test")
        with self.assertRaisesMessage(RuntimeError, "duplicate email groups"):
            self.migrate(NEW)
        self.assertEqual(users.count(), 2)
        users.filter(pk=second.pk).update(email="second@example.test")
