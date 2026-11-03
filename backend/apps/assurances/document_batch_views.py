from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.documents.serializers import DocumentUploadSerializer, AssuranceDocumentSerializer
from apps.documents.services.document_write_service import upload_assurance_documents


class AssuranceBatchMixin:
    @action(detail=True, methods=["post"], url_path="documents/batch",
            parser_classes=[MultiPartParser, FormParser])
    def upload_document_batch(self, request, pk=None):
        assurance = self.get_object()
        files = request.FILES.getlist("files")
        types = request.data.getlist("document_types")
        if not files or len(files) != len(types):
            raise ValidationError("Provide matching files and document_types lists.")
        items = []
        for document_type, file in zip(types, files):
            serializer = DocumentUploadSerializer(data={"document_type": document_type, "file": file})
            serializer.is_valid(raise_exception=True)
            items.append((serializer.validated_data["document_type"], serializer.validated_data["file"]))
        documents = upload_assurance_documents(assurance, request.user, items)
        return Response({"success": True, "data": AssuranceDocumentSerializer(documents, many=True).data}, status=201)
