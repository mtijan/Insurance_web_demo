from io import BytesIO
from unittest.mock import patch

from django.db import DatabaseError
from openpyxl import load_workbook
from rest_framework.exceptions import PermissionDenied

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.reports.services.excel_export_service import HEADERS, export_assurances_excel


class ExcelExportTests(AssuranceFeatureTestCase):
    url = "/api/v1/assurances/export-excel/"

    def export(self, user=None, params=None):
        self.client.force_authenticate(user or self.superadmin)
        return self.client.get(self.url, params or {})

    def test_superadmin_download_has_contract_headers_and_all_columns(self):
        assurance = self.draft()
        response = self.export()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"],
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertRegex(response["Content-Disposition"], r'attachment; filename=".*_\d{8}\.xlsx"')
        self.assertEqual(response["Cache-Control"], "no-store")
        rows = list(load_workbook(BytesIO(response.content)).active.values)
        self.assertEqual(list(rows[0]), HEADERS)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][3], assurance.policy_holder.nik)
        self.assertEqual(rows[1][6:11], (20000000, 1, 400000, 35000, 435000))
        self.assertEqual(AuditLog.objects.get(action="EXPORT_EXCEL").changes["row_count"], 1)

    def test_admin_agent_dealer_cannot_export(self):
        for user in (self.admin, self.agent, self.owner):
            with self.subTest(role=user.role):
                self.assertEqual(self.export(user).status_code, 403)
        self.assertFalse(AuditLog.objects.filter(action="EXPORT_EXCEL").exists())

    def test_anonymous_export_is_unauthorized(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_empty_export_is_valid_workbook(self):
        response = self.export()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(list(load_workbook(BytesIO(response.content)).active.values)), 1)

    def test_spreadsheet_formula_strings_are_text_and_nik_retains_zeros(self):
        self.draft(policy_holder_name='=HYPERLINK("https://example.test","test")')
        response = self.export()
        sheet = load_workbook(BytesIO(response.content)).active
        self.assertEqual(sheet["C2"].data_type, "s")
        self.assertTrue(sheet["C2"].value.startswith("="))
        self.assertEqual(sheet["D2"].value, "0000000000000001")

    def test_export_includes_records_across_dealers(self):
        assurance = self.draft()
        assurance.dealer = self.other_dealer
        assurance.save()
        self.draft(policy_holder_nik="0000000000000002")
        rows = list(load_workbook(BytesIO(self.export().content)).active.values)
        self.assertEqual(len(rows), 3)
        self.assertEqual({row[4] for row in rows[1:]}, {self.dealer.name, self.other_dealer.name})

    def test_status_filter_applies_to_export(self):
        self.draft()
        response = self.export(params={"status": "ACTIVE"})
        self.assertEqual(len(list(load_workbook(BytesIO(response.content)).active.values)), 1)

    def test_export_audit_failure_returns_503_without_workbook(self):
        self.draft()
        with patch("apps.audit.services.audit_service.AuditLog.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            response = self.export()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"PK\x03\x04", response.content)

    def test_service_enforces_superadmin_authorization(self):
        with self.assertRaises(PermissionDenied):
            export_assurances_excel(self.admin)

    def test_issued_date_uses_local_approval_date(self):
        from django.utils import timezone
        from apps.assurances.services.workflow_service import (
            review_assurance, submit_assurance_application,
        )

        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        assurance = submit_assurance_application(assurance, self.owner)
        assurance = review_assurance(assurance, self.admin, {"decision": "APPROVE"})
        sheet = load_workbook(BytesIO(self.export().content)).active
        self.assertEqual(sheet["B2"].value.date(), timezone.localtime(assurance.updated_at).date())

    def test_invalid_xml_control_characters_are_removed_from_export(self):
        self.draft(policy_holder_name="Test\x01Holder")
        response = self.export()
        self.assertEqual(response.status_code, 200)
        sheet = load_workbook(BytesIO(response.content)).active
        self.assertEqual(sheet["C2"].value, "TestHolder")
