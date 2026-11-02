"""
URL configuration for core project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/dealers/", include("apps.dealers.urls")),
    path("api/v1/assurances/", include("apps.assurances.urls")),
    path("api/v1/configs/", include("apps.configs.urls")),
]
