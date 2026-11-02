from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DealerViewSet, AgentDealerAssignmentViewSet

router = DefaultRouter()
router.register(r"assignments", AgentDealerAssignmentViewSet, basename="dealer-assignment")
router.register(r"", DealerViewSet, basename="dealer")

urlpatterns = [
    path("", include(router.urls)),
]
