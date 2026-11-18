from rest_framework import serializers

from apps.assurances.models import AssuranceNote


class AssuranceNoteSerializer(serializers.ModelSerializer):
    """Read-only serializer for shared non-PII note thread entries."""

    assurance_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = AssuranceNote
        fields = [
            "id",
            "assurance_id",
            "author_role",
            "author_username",
            "message",
            "created_at",
        ]
        read_only_fields = fields


class AssuranceNoteCreateSerializer(serializers.Serializer):
    """Validate collaborative assurance note submissions."""

    message = serializers.CharField(max_length=1000, trim_whitespace=True)

    def validate_message(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Catatan tidak boleh kosong.")
        return cleaned
