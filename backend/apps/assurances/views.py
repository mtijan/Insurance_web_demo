from uuid import UUID
from apps.documents.services.vault_paths import open_vault_file
from django.http import FileResponse, Http404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.assurances.models import VehicleAssurance
from apps.assurances.permissions import AssuranceAccessPermission
from apps.assurances.selectors.assurance_selector import get_assurances_for_user
from apps.assurances.serializers import (
    AssuranceDraftCreateSerializer,
    AssuranceDetailSerializer,
    AssuranceListSerializer,
    CalculatePremiumQuerySerializer,
)
from apps.assurances.services.assurance_service import (
    create_assurance_draft,
    update_assurance_draft,
)
from apps.assurances.services.pricing_calculator import calculate_premium
from apps.assurances.workflow_views import AssuranceWorkflowMixin
from apps.assurances.document_batch_views import AssuranceBatchMixin
from apps.configs.services.config_service import get_admin_fee
from apps.documents.models import AssuranceDocument
from apps.documents.serializers import (
    AssuranceDocumentSerializer,
    DocumentUploadSerializer,
)
from apps.documents.services.document_write_service import (
    upload_assurance_document,
    remove_assurance_document,
)


class AssuranceViewSet(AssuranceBatchMixin, AssuranceWorkflowMixin, viewsets.ModelViewSet):
    """
    ViewSet for vehicle assurance management:
    - List/Retrieve scoped by user role.
    - Create/Update draft applications with automatic premium computation.
    - Real-time live premium calculation simulation.
    - Protected multipart document uploads, deletion, and authenticated streaming.
    """
    permission_classes = [IsAuthenticated, AssuranceAccessPermission]

    def get_queryset(self):
        return get_assurances_for_user(self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return AssuranceListSerializer
        if self.action == "create":
            return AssuranceDraftCreateSerializer
        return AssuranceDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Assurances retrieved successfully.",
            "data": serializer.data,
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "data": serializer.data,
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assurance = create_assurance_draft(request.user, serializer.validated_data)
        out_serializer = AssuranceDetailSerializer(assurance, context=self.get_serializer_context())
        return Response({
            "success": True,
            "message": "Assurance draft created successfully.",
            "data": out_serializer.data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = AssuranceDraftCreateSerializer(
            data=request.data,
            partial=kwargs.get("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        updated = update_assurance_draft(instance, request.user, serializer.validated_data)
        out_serializer = AssuranceDetailSerializer(updated, context=self.get_serializer_context())
        return Response({
            "success": True,
            "message": "Assurance draft updated successfully.",
            "data": out_serializer.data,
        })

    @action(detail=False, methods=["get"], url_path="calculate-premium")
    def calculate_premium_simulation(self, request):
        """
        Calculates live premium simulation based on sum_insured, coverage_type, and tenor.
        """
        serializer = CalculatePremiumQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        calc_result = calculate_premium(
            sum_insured=serializer.validated_data["sum_insured"],
            coverage_type=serializer.validated_data["coverage_type"],
            tenor_years=serializer.validated_data["tenor_years"],
            admin_fee=get_admin_fee(),
        )
        return Response({
            "success": True,
            "data": calc_result,
        })

    @action(
        detail=True,
        methods=["post"],
        url_path="documents",
        parser_classes=[MultiPartParser, FormParser]
    )
    def upload_document(self, request, pk=None):
        """
        Uploads a physical verification document into the protected vault.
        """
        assurance = self.get_object()
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doc = upload_assurance_document(
            assurance=assurance,
            user=request.user,
            document_type=serializer.validated_data["document_type"],
            uploaded_file=serializer.validated_data["file"]
        )

        return Response({
            "success": True,
            "message": "Document uploaded successfully.",
            "data": {
                "document_id": str(doc.id),
                "document_type": doc.document_type,
                "original_filename": doc.original_filename,
                "file_size": doc.file_size,
                "mime_type": doc.mime_type,
                "view_url": f"/api/v1/assurances/{assurance.id}/documents/{doc.id}/view/",
            }
        }, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"documents/(?P<doc_id>[0-9a-f-]+)"
    )
    def delete_document(self, request, pk=None, doc_id=None):
        """
        Deletes an uploaded document from the vault and database.
        """
        assurance = self.get_object()
        validate_document_id(doc_id)
        try:
            remove_assurance_document(assurance, request.user, doc_id)
        except AssuranceDocument.DoesNotExist:
            raise Http404("Document not found.")

        return Response({
            "success": True,
            "message": "Document deleted successfully.",
        }, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path=r"documents/(?P<doc_id>[0-9a-f-]+)/view"
    )
    def view_document_stream(self, request, pk=None, doc_id=None):
        """
        Streams protected document image file with authorization validation.
        """
        assurance = self.get_object()
        validate_document_id(doc_id)
        try:
            document = assurance.documents.get(id=doc_id)
        except AssuranceDocument.DoesNotExist:
            raise Http404("Document not found.")

        response = FileResponse(open_vault_file(document.file_path), content_type=document.mime_type)
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


def validate_document_id(value):
    try:
        UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise Http404("Document not found.") from exc
