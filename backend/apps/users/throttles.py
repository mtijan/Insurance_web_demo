"""Configurable auth endpoint throttling active when ENABLE_AUTH_THROTTLE is set."""
from django.conf import settings
from rest_framework.throttling import ScopedRateThrottle


class AuthScopedRateThrottle(ScopedRateThrottle):
    def allow_request(self, request, view):
        if not getattr(settings, "ENABLE_AUTH_THROTTLE", False):
            return True
        self.THROTTLE_RATES = getattr(settings, "REST_FRAMEWORK", {}).get("DEFAULT_THROTTLE_RATES", {})
        return super().allow_request(request, view)
