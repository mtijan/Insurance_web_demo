"""Factual ACTIVE summary; no benefit wording, identity scans or raw NIK."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from django.conf import settings
from django.db import transaction
from django.http import Http404
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework.exceptions import ValidationError, APIException

from apps.assurances.selectors.assurance_selector import get_assurances_for_user
from apps.audit.services.audit_service import record_audit


class PDFUnavailable(APIException):
    status_code = 503
    default_detail = "PDF font support is unavailable for this summary. Contact your administrator."


def summary_style():
    font = Path(getattr(settings, "SUMMARY_PDF_FONT", Path(reportlab.__file__).parent / "fonts/Vera.ttf"))
    name = "SummaryFont-" + str(hash(str(font)))
    if name not in pdfmetrics.getRegisteredFontNames():
        try:
            pdfmetrics.registerFont(TTFont(name, str(font)))
        except (OSError, reportlab.pdfbase.ttfonts.TTFError) as exc:
            raise PDFUnavailable() from exc
    return ParagraphStyle("Summary", fontName=name, fontSize=10, leading=16,
                          wordWrap="CJK", spaceAfter=8)


def summary_rows(assurance):
    return [
        ("Nomor jaminan", assurance.assurance_number),
        ("Status", assurance.status),
        ("Nama tertanggung", assurance.policy_holder.full_name),
        ("Dealer", assurance.dealer.name),
        ("Objek kendaraan", assurance.vehicle_object),
        ("Kategori / produk", f"{assurance.vehicle_category} / {assurance.coverage_type}"),
        ("Periode", f"{assurance.period_start:%d-%m-%Y} s.d. {assurance.period_end:%d-%m-%Y}"),
        ("Tenor", f"{assurance.tenor_years} tahun"),
        ("Harga pertanggungan", f"IDR {assurance.sum_insured:,.2f}"),
        ("Premi murni", f"IDR {assurance.base_premium:,.2f}"),
        ("Biaya administrasi", f"IDR {assurance.admin_fee:,.2f}"),
        ("Total premi", f"IDR {assurance.total_premium:,.2f}"),
    ]


def render_summary(assurance):
    buffer = BytesIO()
    style = summary_style()
    glyphs = pdfmetrics.getFont(style.fontName).face.charToGlyph
    values = [str(value) for row in summary_rows(assurance) for value in row]
    if any(ord(char) not in glyphs for value in values for char in value if not char.isspace()):
        raise PDFUnavailable()
    paragraph = lambda value: Paragraph(escape(str(value or "")), style)
    rows = [[paragraph(key), paragraph(value)] for key, value in summary_rows(assurance)]
    table = Table(rows, colWidths=[160, 339], hAlign="LEFT")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                               ("LINEBELOW", (0, 0), (-1, -1), .3, colors.lightgrey)]))
    content = [paragraph("KEVIN ASSURANCE"), paragraph("Ringkasan Jaminan Aktif"), Spacer(1, 12), table,
               Spacer(1, 16), paragraph("Ringkasan data pengajuan yang telah disetujui. "
                                       "Manfaat dan pengecualian mengacu pada dokumen produk yang disahkan.")]
    SimpleDocTemplate(buffer, pagesize=A4, rightMargin=48, leftMargin=48,
                      topMargin=40, bottomMargin=40, title="Ringkasan Jaminan").build(content)
    return buffer.getvalue()


@transaction.atomic
def export_summary_pdf(user, assurance_id):
    assurance = get_assurances_for_user(user).filter(pk=assurance_id).first()
    if assurance is None:
        raise Http404("Assurance not found.")
    if assurance.status != "ACTIVE" or not assurance.assurance_number:
        raise ValidationError("A summary is available only for an ACTIVE assurance with an issued number.")
    content = render_summary(assurance)
    record_audit(user, "DOWNLOAD", "VEHICLE_ASSURANCE", assurance.pk, {"format": "PDF_SUMMARY"})
    return content
