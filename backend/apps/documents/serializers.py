from pathlib import PureWindowsPath

from rest_framework import serializers
from apps.documents.models import AssuranceDocument, DocumentType


def normalize_upload_filename(raw_name):
    cleaned = PureWindowsPath(str(raw_name or "")).name.strip()
    if not cleaned or any(ord(ch) < 32 or ord(ch) == 127 for ch in cleaned):
        raise serializers.ValidationError("Invalid filename.")
    if len(cleaned) > 255:
        raise serializers.ValidationError("Filename must be 255 characters or fewer.")
    return cleaned


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

    def validate_file(self, value):
        value.name = normalize_upload_filename(getattr(value, "name", ""))
        return value
