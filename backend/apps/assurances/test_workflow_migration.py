from datetime import date

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

OLD = [("assurances", "0003_quality_integrity"), ("users", "0003_first_login_password")]
NEW = [("assurances", "0004_review_workflow"), ("users", "0003_first_login_password")]


class WorkflowMigrationTests(TransactionTestCase):
    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_additive_forward_backfill_and_rollback_preserve_existing_records(self):
        apps = self.migrate(OLD)
        user = apps.get_model("users", "CustomUser").objects.create(username="migration_admin", role="ADMIN")
        dealer = apps.get_model("dealers", "Dealer").objects.create(code="MIG-WF", name="Synthetic")
        holder = apps.get_model("assurances", "PolicyHolder").objects.create(nik="0000000000000001", full_name="Test")
        model = apps.get_model("assurances", "VehicleAssurance")
        values = dict(created_by=user, dealer=dealer, policy_holder=holder, vehicle_category="MOTOR_BARU",
                      coverage_type="TLO", sum_insured=100, tenor_years=1, base_premium=2,
                      admin_fee=0, total_premium=2, period_start=date(2026, 1, 1),
                      period_end=date(2027, 1, 1), issuance_year=2026)
        active = model.objects.create(**values, status="ACTIVE", assurance_number="KAS-2026-00001")
        pending = model.objects.create(**values, status="SUBMITTED")
        before = list(model.objects.order_by("pk").values())
        apps = self.migrate(NEW)
        model = apps.get_model("assurances", "VehicleAssurance")
        row = model.objects.get(pk=active.pk)
        self.assertEqual(row.verification_stage, "COMPLETE")
        self.assertTrue(row.data_verified and row.documents_verified)
        self.assertFalse(model.objects.get(pk=pending.pk).data_verified)
        self.assertEqual(apps.get_model("assurances", "AssuranceReviewEvent").objects.count(), 0)
        apps = self.migrate(OLD)
        after = list(apps.get_model("assurances", "VehicleAssurance").objects.order_by("pk").values())
        self.assertEqual(before, after)
