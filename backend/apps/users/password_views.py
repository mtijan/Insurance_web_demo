from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.services.password_service import change_own_password


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise ValidationError({"non_field_errors": ["Only current_password and new_password are accepted."]})
        return super().to_internal_value(data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_own_password(request.user, request.auth, **serializer.validated_data)
        response = Response({"success": True, "message": "Password changed. Please log in again."})
        for name in ("access_token", "refresh_token"):
            response.delete_cookie(name, path="/", samesite=settings.AUTH_COOKIE_SAMESITE)
        response["Cache-Control"] = "no-store"
        return response
