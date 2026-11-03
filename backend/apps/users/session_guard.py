"""Protect Django-session surfaces as well as the separate JWT API transport."""
from django.http import JsonResponse


class PasswordStateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        auth_path = request.path.startswith("/api/v1/auth/") or request.path == "/admin/logout/"
        if user.is_authenticated and user.must_change_password and not auth_path:
            return JsonResponse({"success": False, "error_code": "PASSWORD_CHANGE_REQUIRED",
                                 "message": "Use the application to change your password."}, status=403)
        return self.get_response(request)
