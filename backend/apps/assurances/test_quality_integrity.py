from datetime import date
from unittest.mock import patch

from django.db import IntegrityError, transaction

from apps.assurances.models import PolicyHolder, VehicleAssurance
from apps.assurances.services.assurance_service import calculate_end_date, update_assurance_draft
from apps.assurances.services.workflow_service import submit_assurance_application, review_assurance
from apps.assurances.test_support import AssuranceFeatureTestCase


class QualityIntegrityTests(AssuranceFeatureTestCase):
    def test_legacy_shared_holder_is_copied_on_write(self):
        first = self.draft()
        second = self.draft()
        VehicleAssurance.objects.filter(pk=second.pk).update(policy_holder=first.policy_holder)
        changed = update_assurance_draft(second, self.owner, {"policy_holder_name": "Changed draft"})
        first.refresh_from_db()
        self.assertEqual(first.policy_holder.full_name, "Test Holder")
        self.assertEqual(changed.policy_holder.full_name, "Changed draft")
        self.assertNotEqual(first.policy_holder_id, changed.policy_holder_id)

    def test_all_history_references_protect_policy_and_documents(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        review_assurance(assurance, self.admin, {"decision": "APPROVE"})
        document_paths = list(assurance.documents.values_list("file_path", flat=True))
        self.client.force_authenticate(self.superadmin)
        for url in (f"/api/v1/dealers/{self.dealer.pk}/", f"/api/v1/auth/manage/{self.owner.pk}/"):
            self.assertEqual(self.client.delete(url).status_code, 400)
        self.assertEqual(list(assurance.documents.values_list("file_path", flat=True)), document_paths)
        for path in document_paths:
            self.assertTrue((self.media / path).exists())
        with self.assertRaises(IntegrityError):
            assurance.policy_holder.delete()

    def test_financial_constraints_reject_every_invalid_component(self):
        assurance = self.draft()
        cases = ({"sum_insured": 0}, {"sum_insured": -1}, {"tenor_years": 0},
                 {"tenor_years": 6}, {"base_premium": -1}, {"admin_fee": -1},
                 {"total_premium": 0}, {"total_premium": 1}, {"issuance_year": 999},
                 {"issuance_year": 10000}, {"period_end": assurance.period_start})
        for values in cases:
            with self.subTest(values=values), self.assertRaises(IntegrityError), transaction.atomic():
                VehicleAssurance.objects.filter(pk=assurance.pk).update(**values)

    def test_financial_boundaries_and_leap_year(self):
        self.assertEqual(calculate_end_date(date(2024, 2, 29), 1), date(2025, 2, 28))
        for tenor in (1, 5):
            assurance = self.draft(tenor_years=tenor, issuance_year=9999)
            VehicleAssurance.objects.filter(pk=assurance.pk).update(admin_fee=0, base_premium=1, total_premium=1)
            assurance.refresh_from_db()
            self.assertEqual(assurance.total_premium, 1)

    def test_fractional_currency_consistency_uses_cent_precision(self):
        assurance = self.draft()
        VehicleAssurance.objects.filter(pk=assurance.pk).update(
            base_premium="20000.10", admin_fee="35000.20", total_premium="55000.30",
        )
        assurance.refresh_from_db()
        self.assertEqual(str(assurance.total_premium), "55000.30")
        with self.assertRaises(IntegrityError), transaction.atomic():
            VehicleAssurance.objects.filter(pk=assurance.pk).update(total_premium="55000.31")

    def test_invalid_date_year_and_premium_limits_are_400_and_atomic(self):
        self.client.force_authenticate(self.owner)
        data = self.payload()
        data["dealer_id"] = str(data.pop("dealer").pk)
        for change in ({"period_start": "9999-01-01"}, {"issuance_year": 10000},
                       {"sum_insured": "999999999999.99", "coverage_type": "KOMPRE_PLUS"}):
            with self.subTest(change=change):
                response = self.client.post("/api/v1/assurances/", {**data, **change}, format="json")
                self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(VehicleAssurance.objects.exists())
        self.assertFalse(PolicyHolder.objects.exists())

    def test_partial_date_update_combines_existing_tenor(self):
        assurance = self.draft(tenor_years=5)
        self.client.force_authenticate(self.owner)
        response = self.client.patch(f"/api/v1/assurances/{assurance.pk}/", {"period_start": "9998-01-01"})
        self.assertEqual(response.status_code, 400)
        assurance.refresh_from_db()
        self.assertEqual(assurance.period_start, date(2026, 11, 2))

    def test_annual_counter_only_scans_during_initialization(self):
        from apps.assurances.services.workflow_service import existing_number_maximum

        with patch("apps.assurances.services.workflow_service.existing_number_maximum", wraps=existing_number_maximum) as scan:
            for _ in range(2):
                assurance = self.draft()
                self.attach_uploaded_documents(assurance)
                submit_assurance_application(assurance, self.owner)
                review_assurance(assurance, self.admin, {"decision": "APPROVE"})
        self.assertEqual(scan.call_count, 1)
