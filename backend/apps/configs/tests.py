from decimal import Decimal
from unittest.mock import patch

from django.db import DatabaseError

from apps.assurances.services.assurance_service import update_assurance_draft
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.configs.models import SystemConfig
from apps.configs.services.config_service import update_admin_fee


class AdminFeeTests(AssuranceFeatureTestCase):
    url = "/api/v1/configs/admin-fee/"

    def update_fee(self, amount="40000.00", user=None, reason="Operational adjustment"):
        self.client.force_authenticate(user or self.superadmin)
        return self.client.put(self.url, {"admin_fee": amount, "reason": reason}, format="json")

    def test_default_fee_readable_by_all_authenticated_roles(self):
        for user in self.users.values():
            with self.subTest(role=user.role):
                self.client.force_authenticate(user)
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["data"]["value"], "35000.00")

    def test_superadmin_updates_fee_and_audit(self):
        response = self.update_fee()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["value"], "40000.00")
        config = SystemConfig.objects.get(key="ADMIN_FEE_AMOUNT")
        self.assertEqual(config.updated_by, self.superadmin)
        self.assertEqual(config.description, "Operational adjustment")
        audit = AuditLog.objects.get(action="UPDATE_CONFIG")
        self.assertEqual(audit.changes["admin_fee"], {"old": "35000.00", "new": "40000.00"})

    def test_other_roles_cannot_modify_fee(self):
        for user in (self.admin, self.agent, self.owner):
            with self.subTest(role=user.role):
                self.assertEqual(self.update_fee(user=user).status_code, 403)
        self.assertFalse(SystemConfig.objects.exists())

    def test_anonymous_cannot_read_or_write_fee(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.assertEqual(self.client.put(self.url, {}, format="json").status_code, 401)

    def test_invalid_amounts_and_reason_are_rejected(self):
        for amount in ("-1.00", "NaN", "Infinity", "abc", "1.001", "100000000.00", None):
            with self.subTest(amount=amount):
                self.assertEqual(self.update_fee(amount).status_code, 400)
        for reason in ("", " ", None):
            self.assertEqual(self.update_fee(reason=reason).status_code, 400)
        self.assertFalse(SystemConfig.objects.exists())

    def test_zero_admin_fee_is_supported(self):
        self.assertEqual(self.update_fee("0.00").status_code, 200)

    def test_new_drafts_and_simulations_use_updated_fee(self):
        old_draft = self.draft()
        self.update_fee()
        new_draft = self.draft(policy_holder_nik="0000000000000002")
        self.assertEqual(new_draft.admin_fee, Decimal("40000.00"))
        self.assertEqual(new_draft.total_premium, Decimal("440000.00"))
        old_draft.refresh_from_db()
        self.assertEqual(old_draft.admin_fee, Decimal("35000.00"))
        self.client.force_authenticate(self.owner)
        response = self.client.get("/api/v1/assurances/calculate-premium/", {
            "sum_insured": "20000000.00", "coverage_type": "TLO", "tenor_years": 1,
        })
        self.assertEqual(response.data["data"]["admin_fee"], "40000.00")

    def test_existing_draft_update_preserves_original_fee_snapshot(self):
        old_draft = self.draft()
        self.update_fee()
        updated = update_assurance_draft(old_draft, self.owner, {"sum_insured": Decimal("30000000")})
        self.assertEqual(updated.admin_fee, Decimal("35000.00"))
        self.assertEqual(updated.total_premium, Decimal("635000.00"))

    def test_audit_failure_rolls_back_fee_update(self):
        self.update_fee()
        with patch("apps.audit.services.audit_service.AuditLog.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            response = self.update_fee("50000.00")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(SystemConfig.objects.get().value, "40000.00")

    def test_service_enforces_superadmin_authorization(self):
        from rest_framework.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            update_admin_fee(self.admin, {"admin_fee": "40000.00", "reason": "test"})
