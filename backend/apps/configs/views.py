from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.configs.services.config_service import get_admin_fee, update_admin_fee
from apps.users.permissions import IsSuperAdmin


class AdminFeeView(APIView):
    def get_permissions(self):
        classes = [IsAuthenticated]
        if self.request.method == "PUT":
            classes.append(IsSuperAdmin)
        return [permission() for permission in classes]

    def get(self, request):
        return Response({"success": True, "data": {
            "key": "ADMIN_FEE_AMOUNT", "value": f"{get_admin_fee():.2f}",
        }})

    def put(self, request):
        config = update_admin_fee(request.user, request.data)
        return Response({
            "success": True, "message": "Admin fee updated successfully.",
            "data": {"key": config.key, "value": config.value,
                     "updated_at": config.updated_at},
        })
