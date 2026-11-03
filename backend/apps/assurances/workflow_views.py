from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.assurances.models import AssuranceStatus
from apps.assurances.serializers import AssuranceDetailSerializer
from apps.assurances.services.workflow_service import (
    review_assurance, submit_assurance_application,
)
from apps.reports.services.excel_export_service import export_assurances_excel
from apps.users.permissions import IsAdmin, IsSuperAdmin
from apps.reports.services.pdf_summary_service import export_summary_pdf


class AssuranceWorkflowMixin:
    @action(detail=True, methods=["get"], url_path="summary-pdf")
    def summary_pdf(self, request, pk=None):
        assurance = self.get_object()
        content = export_summary_pdf(request.user, assurance.pk)
        response = HttpResponse(content, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="jaminan-{assurance.pk}.pdf"'
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        assurance = submit_assurance_application(self.get_object(), request.user)
        return Response({
            "success": True,
            "message": "Assurance submitted successfully and is now under review.",
            "data": {"id": str(assurance.id), "status": assurance.status,
                     "submitted_at": assurance.updated_at},
        })

    @action(detail=True, methods=["post"], url_path="review",
            permission_classes=[IsAuthenticated, IsAdmin])
    def review(self, request, pk=None):
        assurance = review_assurance(self.get_object(), request.user, request.data)
        return Response({"success": True, "message": "Review completed successfully.",
                         "data": AssuranceDetailSerializer(assurance, context=self.get_serializer_context()).data})

    @action(detail=False, methods=["get"], url_path="export-excel",
            permission_classes=[IsAuthenticated, IsSuperAdmin])
    def export_excel(self, request):
        content = export_assurances_excel(request.user, self.filter_queryset(self.get_queryset()))
        response = HttpResponse(
            content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        filename = f"Rekapitulasi_Jaminan_Kevin_Assurance_{timezone.localdate():%Y%m%d}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "no-store"
        return response

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        status = self.request.query_params.get("status")
        if status:
            if status not in AssuranceStatus.values:
                raise ValidationError({"status": "Invalid assurance status."})
            queryset = queryset.filter(status=status)
        return queryset

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE")
