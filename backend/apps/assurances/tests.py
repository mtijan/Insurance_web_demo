import datetime
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.assurances.models import (
    PolicyHolder,
    VehicleAssurance,
    VehicleCategory,
    CoverageType,
    AssuranceStatus,
)
from apps.assurances.services.pricing_calculator import calculate_premium
from apps.dealers.models import Dealer, AgentDealerAssignment
from apps.users.models import CustomUser, UserRole


class PricingCalculationUnitTests(APITestCase):
    def test_tlo_calculation(self):
        """TLO rate must be 2.0% of HP + 35,000 admin fee."""
        result = calculate_premium(sum_insured=Decimal("20000000.00"), coverage_type="TLO", tenor_years=1)
        self.assertEqual(result["base_premium"], "400000.00")
        self.assertEqual(result["admin_fee"], "35000.00")
        self.assertEqual(result["total_premium"], "435000.00")

    def test_tlo_plus_depreciation_years(self):
        """TLO+ rate must apply depreciation factors (100%, 85%, 75%, 65%, 55%) * 3.1%."""
        hp = Decimal("20000000.00")
        expected_bases = {
            1: "620000.00",  # 20M * 100% * 3.1%
            2: "527000.00",  # 20M * 85% = 17M * 3.1%
            3: "465000.00",  # 20M * 75% = 15M * 3.1%
            4: "403000.00",  # 20M * 65% = 13M * 3.1%
            5: "341000.00",  # 20M * 55% = 11M * 3.1%
        }
        for year, expected_base in expected_bases.items():
            res = calculate_premium(sum_insured=hp, coverage_type="TLO_PLUS", tenor_years=year)
            self.assertEqual(res["base_premium"], expected_base)
            expected_total = Decimal(expected_base) + Decimal("35000.00")
            self.assertEqual(res["total_premium"], f"{expected_total:.2f}")

    def test_kompre_plus_calculation(self):
        """Kompre+ rate must be 4.3% of HP + 35,000 admin fee."""
        result = calculate_premium(sum_insured=Decimal("25000000.00"), coverage_type="KOMPRE_PLUS", tenor_years=1)
        self.assertEqual(result["base_premium"], "1075000.00")
        self.assertEqual(result["admin_fee"], "35000.00")
        self.assertEqual(result["total_premium"], "1110000.00")

    def test_invalid_parameters_raise_error(self):
        """Zero HP or invalid tenor must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_premium(sum_insured=Decimal("0.00"), coverage_type="TLO")
        with self.assertRaises(ValueError):
            calculate_premium(sum_insured=Decimal("10000000.00"), coverage_type="TLO", tenor_years=6)


class AssuranceAPITests(APITestCase):
    def setUp(self):
        self.dealer_a = Dealer.objects.create(code="DLR-01", name="Dealer Honda Jakarta")
        self.dealer_b = Dealer.objects.create(code="DLR-02", name="Dealer Yamaha Bandung")

        self.superadmin = CustomUser.objects.create_user(
            username="superadmin",
            email="sa@test.com",
            password="Password123!",
            role=UserRole.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.agent = CustomUser.objects.create_user(
            username="agent_andi",
            email="andi@test.com",
            password="Password123!",
            role=UserRole.AGENT
        )
        self.dealer_user = CustomUser.objects.create_user(
            username="dealer_staff",
            email="dealer@test.com",
            password="Password123!",
            role=UserRole.DEALER,
            dealer=self.dealer_a
        )

        AgentDealerAssignment.objects.create(agent=self.agent, dealer=self.dealer_a)

        self.calc_url = reverse("assurance-calculate-premium-simulation")
        self.assurance_list_url = reverse("assurance-list")

    def test_calculate_premium_endpoint(self):
        """GET /api/v1/assurances/calculate-premium/ returns live breakdown."""
        self.client.force_authenticate(user=self.agent)
        params = {
            "sum_insured": "25000000.00",
            "coverage_type": "KOMPRE_PLUS",
            "tenor_years": 1
        }
        res = self.client.get(self.calc_url, params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["data"]["total_premium"], "1110000.00")

    def test_create_assurance_draft_success_dealer(self):
        """Dealer creates draft for own branch and verifies policyholder creation."""
        self.client.force_authenticate(user=self.dealer_user)
        payload = {
            "policy_holder_name": "Budi Santoso",
            "policy_holder_nik": "3201123456780001",
            "dealer_id": str(self.dealer_a.id),
            "vehicle_category": VehicleCategory.MOTOR_BARU,
            "coverage_type": CoverageType.KOMPRE_PLUS,
            "sum_insured": "25000000.00",
            "tenor_years": 1,
            "period_start": "2026-11-05",
            "issuance_year": 2026,
        }
        res = self.client.post(self.assurance_list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["data"]["status"], "DRAFT")
        self.assertEqual(res.data["data"]["total_premium"], "1110000.00")
        self.assertTrue(PolicyHolder.objects.filter(nik="3201123456780001").exists())

    def test_create_assurance_invalid_nik_rejected(self):
        """Non-16 digit NIK must be rejected by validator."""
        self.client.force_authenticate(user=self.dealer_user)
        payload = {
            "policy_holder_name": "Budi Invalid",
            "policy_holder_nik": "12345ABC",
            "dealer_id": str(self.dealer_a.id),
            "vehicle_category": VehicleCategory.MOTOR_BARU,
            "coverage_type": CoverageType.TLO,
            "sum_insured": "20000000.00",
            "tenor_years": 1,
            "period_start": "2026-11-05",
        }
        res = self.client.post(self.assurance_list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dealer_cannot_create_for_other_branch(self):
        """Dealer staff cannot create an assurance for an unassigned dealer branch."""
        self.client.force_authenticate(user=self.dealer_user)
        payload = {
            "policy_holder_name": "Siti Rahma",
            "policy_holder_nik": "3201123456780002",
            "dealer_id": str(self.dealer_b.id),
            "vehicle_category": VehicleCategory.MOTOR_BARU,
            "coverage_type": CoverageType.TLO,
            "sum_insured": "20000000.00",
            "tenor_years": 1,
            "period_start": "2026-11-05",
        }
        res = self.client.post(self.assurance_list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_role_scoped_list_visibility(self):
        """Dealer user only sees own dealer's assurances, Super Admin sees all."""
        # Create assurance for dealer_a
        holder_a = PolicyHolder.objects.create(nik="3201000000000001", full_name="Nasabah A")
        today = datetime.date.today()
        VehicleAssurance.objects.create(
            policy_holder=holder_a,
            dealer=self.dealer_a,
            vehicle_category=VehicleCategory.MOTOR_BARU,
            coverage_type=CoverageType.TLO,
            sum_insured=Decimal("15000000.00"),
            tenor_years=1,
            base_premium=Decimal("300000.00"),
            admin_fee=Decimal("35000.00"),
            total_premium=Decimal("335000.00"),
            period_start=today,
            period_end=today.replace(year=today.year + 1),
            issuance_year=2026,
            created_by=self.dealer_user
        )

        self.create_other_dealer_assurance(today)

        # 1. Dealer user list -> 1 record
        self.client.force_authenticate(user=self.dealer_user)
        res_dealer = self.client.get(self.assurance_list_url)
        self.assertEqual(len(res_dealer.data["data"]), 1)

        # 2. Super Admin list -> 2 records
        self.client.force_authenticate(user=self.superadmin)
        res_admin = self.client.get(self.assurance_list_url)
        self.assertEqual(len(res_admin.data["data"]), 2)

    def create_other_dealer_assurance(self, today):
        # Create assurance for dealer_b
        holder_b = PolicyHolder.objects.create(nik="3201000000000002", full_name="Nasabah B")
        VehicleAssurance.objects.create(
            policy_holder=holder_b,
            dealer=self.dealer_b,
            vehicle_category=VehicleCategory.MOTOR_BARU,
            coverage_type=CoverageType.TLO,
            sum_insured=Decimal("15000000.00"),
            tenor_years=1,
            base_premium=Decimal("300000.00"),
            admin_fee=Decimal("35000.00"),
            total_premium=Decimal("335000.00"),
            period_start=today,
            period_end=today.replace(year=today.year + 1),
            issuance_year=2026,
            created_by=self.superadmin
        )

