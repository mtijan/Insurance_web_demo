from contextvars import ContextVar


audit_request = ContextVar("audit_request", default=None)


class AuditContextMiddleware:
    """Expose request metadata to transactional audit services; never log bodies."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = audit_request.set(request)
        try:
            return self.get_response(request)
        finally:
            audit_request.reset(token)
