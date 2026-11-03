"""Bounded, read-only audit projection; no raw JSON, PII or credential exposure."""
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.users.permissions import IsSuperAdmin


class AuditQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, max_value=100000, default=1)
    action = serializers.CharField(max_length=30, required=False)
    entity_name = serializers.CharField(max_length=50, required=False)


class AuditListView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        serializer = AuditQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        page = values.pop("page")
        rows = AuditLog.objects.filter(**values).order_by("-created_at", "-id")
        offset = (page - 1) * 50
        # Explicit allowlist intentionally excludes raw changes, IP and actor identity.
        data = list(rows.values("id", "action", "entity_name", "entity_id", "created_at")[offset:offset+51])
        response = Response({"success": True, "data": {"results": data[:50], "page": page,
                                                      "has_next": len(data) > 50}})
        response["Cache-Control"] = "private, no-store"
        return response
