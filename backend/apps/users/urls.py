from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (LoginView, LogoutView, MeView, UserManagementViewSet,
                    CsrfView, TokenLoginView, RefreshView, TokenRefreshView)

router = DefaultRouter()
router.register(r"manage", UserManagementViewSet, basename="user-management")

urlpatterns = [
    path("csrf/", CsrfView.as_view(), name="auth-csrf"),
    path("token/", TokenLoginView.as_view(), name="auth-token"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("", include(router.urls)),
]
