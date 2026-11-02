from rest_framework import serializers
from apps.documents.models import AssuranceDocument, DocumentType


class AssuranceDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer representing uploaded physical verification documents.
    """
    view_url = serializers.SerializerMethodField()

    class Meta:
        model = AssuranceDocument
        fields = [
            "id",
            "document_type",
            "original_filename",
            "file_size",
            "mime_type",
            "uploaded_at",
            "view_url",
        ]
        read_only_fields = fields

    def get_view_url(self, obj: AssuranceDocument) -> str:
        return f"/api/v1/assurances/{obj.assurance_id}/documents/{obj.id}/view/"


class DocumentUploadSerializer(serializers.Serializer):
    """
    Serializer for handling multipart document upload payloads.
    """
    document_type = serializers.ChoiceField(choices=DocumentType.choices)
    file = serializers.FileField()
