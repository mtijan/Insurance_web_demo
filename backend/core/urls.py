"""
URL configuration for core project.
"""

from django.contrib import admin
from django.urls import path, include
from apps.audit.views import AuditListView

urlpatterns = [
    path("api/v1/audit/", AuditListView.as_view(), name="audit-list"),
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/dealers/", include("apps.dealers.urls")),
    path("api/v1/assurances/", include("apps.assurances.urls")),
    path("api/v1/configs/", include("apps.configs.urls")),
]
