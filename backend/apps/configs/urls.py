from django.urls import path

from apps.configs.views import AdminFeeView

urlpatterns = [path("admin-fee/", AdminFeeView.as_view(), name="admin-fee")]
