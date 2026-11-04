"""Expose only allowlisted CSRF failure categories, never raw headers/secrets."""
import logging

from django.middleware.csrf import REASON_CSRF_TOKEN_MISSING, REASON_NO_CSRF_COOKIE
from rest_framework.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


def failure_category(reason):
    exact = {REASON_NO_CSRF_COOKIE: "COOKIE_MISSING",
             REASON_CSRF_TOKEN_MISSING: "TOKEN_MISSING"}
    if reason in exact:
        return exact[reason]
    prefixes = {"Origin checking failed": "ORIGIN_REJECTED",
                "Referer checking failed": "REFERER_REJECTED"}
    for prefix, category in prefixes.items():
        if reason.startswith(prefix):
            return category
    if reason.startswith(("CSRF token", "CSRF cookie")):
        return "TOKEN_MISMATCH" if "incorrect." in reason else "TOKEN_INVALID"
    return "UNKNOWN"


class CsrfRejected(PermissionDenied):
    default_code = "csrf_failed"
    default_detail = "CSRF verification failed."

    def __init__(self, reason):
        self.reason = failure_category(reason)
        logger.warning("CSRF rejected: %s", self.reason)
        super().__init__()
