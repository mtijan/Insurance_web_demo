from io import BytesIO

from django.db import transaction
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from rest_framework.exceptions import PermissionDenied

from apps.assurances.selectors.assurance_selector import get_assurances_for_user
from apps.audit.services.audit_service import record_audit

HEADERS = ["No Polis", "Tanggal Terbit", "Nama Nasabah", "NIK", "Asal Dealer",
           "Kategori Motor", "HP", "Tenor", "Premi", "Admin", "Total Premi", "Status"]


def export_row(assurance):
    issue_date = timezone.localtime(assurance.updated_at).date() if assurance.assurance_number else None
    return [assurance.assurance_number or "", issue_date,
            assurance.policy_holder.full_name, assurance.policy_holder.nik,
            assurance.dealer.name, assurance.vehicle_category,
            assurance.sum_insured, assurance.tenor_years, assurance.base_premium,
            assurance.admin_fee, assurance.total_premium, assurance.status]


def safe_cells(sheet, values):
    """Write user-controlled strings as text, including formula-like values."""
    cells = []
    for value in values:
        if isinstance(value, str):
            value = ILLEGAL_CHARACTERS_RE.sub("", value)
        cell = WriteOnlyCell(sheet, value=value)
        if isinstance(value, str):
            cell.data_type = "s"
        cells.append(cell)
    return cells


@transaction.atomic
def export_assurances_excel(user, queryset=None):
    if not (user.is_active and user.is_super_admin):
        raise PermissionDenied("Only Super Admin may export assurances.")
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Rekapitulasi Jaminan")
    sheet.append(HEADERS)
    records = queryset if queryset is not None else get_assurances_for_user(user)
    count = 0
    for assurance in records.iterator(chunk_size=500):
        sheet.append(safe_cells(sheet, export_row(assurance)))
        count += 1
    output = BytesIO()
    workbook.save(output)
    record_audit(user, "EXPORT_EXCEL", "VEHICLE_ASSURANCE", "ALL",
                 {"row_count": count})
    return output.getvalue()
