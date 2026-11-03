from apps.users.services.auth_service import authenticate_identity
from rest_framework import serializers
from .models import CustomUser, UserRole


class UserSummarySerializer(serializers.ModelSerializer):
    dealer_code = serializers.CharField(source="dealer.code", read_only=True)
    dealer_name = serializers.CharField(source="dealer.name", read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "dealer",
            "dealer_code",
            "dealer_name",
            "is_active",
            "must_change_password",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "must_change_password"]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        attrs["user"] = authenticate_identity(attrs["username"], attrs["password"])
        return attrs


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(required=True, allow_blank=False)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "dealer",
            "password",
            "is_active",
        ]

