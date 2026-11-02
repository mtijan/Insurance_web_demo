from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.middleware.csrf import get_token
from apps.users.authentication import enforce_csrf
from apps.users.cookies import rotate_csrf, set_auth_cookies
from apps.users.services.auth_service import issue_session, revoke_session, refresh_access
from apps.users.services.user_service import create_user, update_user, delete_user

from .models import CustomUser
from .permissions import IsSuperAdmin
from .serializers import (
    LoginSerializer,
    UserCreateUpdateSerializer,
    UserSummarySerializer,
)


class CsrfView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        response = Response({"success": True, "data": {"csrf_token": get_token(request)}})
        response["Cache-Control"] = "no-store"
        return response


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    bearer = False

    def post(self, request):
        if not self.bearer:
            enforce_csrf(request)
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        access, refresh = issue_session(user)
        data = {"user": UserSummarySerializer(user).data}
        if self.bearer:
            data.update(access_token=access, refresh_token=refresh)
        else:
            data["csrf_token"] = rotate_csrf(request)
        response = Response({"success": True, "data": data})
        response["Cache-Control"] = "no-store"
        return response if self.bearer else set_auth_cookies(response, access, refresh)


class TokenLoginView(LoginView):
    bearer = True


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    bearer = False

    def get_authenticate_header(self, request):
        return 'Bearer realm="api"'

    def post(self, request):
        if not self.bearer:
            enforce_csrf(request)
        if self.bearer and not isinstance(request.data, dict):
            raise ValidationError("Expected an object containing refresh_token.")
        raw = request.data.get("refresh_token") if self.bearer else request.COOKIES.get("refresh_token")
        access = refresh_access(raw)
        data = {"access_token": access} if self.bearer else {}
        response = Response({"success": True, "data": data})
        response["Cache-Control"] = "no-store"
        return response if self.bearer else set_auth_cookies(response, access)


class TokenRefreshView(RefreshView):
    bearer = True


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        revoke_session(request.user, request.auth)
        response = Response({"success": True, "message": "Logged out."})
        for name in ("access_token", "refresh_token"):
            response.delete_cookie(name, path="/", samesite=settings.AUTH_COOKIE_SAMESITE)
        response["Cache-Control"] = "no-store"
        return response


class MeView(APIView):
    """
    Returns current authenticated user profile and permissions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSummarySerializer(request.user)
        return Response({
            "success": True,
            "data": serializer.data
        })


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Super Admin endpoint for managing system users across all roles.
    """
    permission_classes = [IsSuperAdmin]
    queryset = CustomUser.objects.all().select_related("dealer")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return UserCreateUpdateSerializer
        return UserSummarySerializer

    def perform_create(self, serializer):
        serializer.instance = create_user(self.request.user, serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = update_user(self.request.user, serializer.instance, serializer.validated_data)

    def perform_destroy(self, instance):
        delete_user(self.request.user, instance)
