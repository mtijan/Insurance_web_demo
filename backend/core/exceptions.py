from rest_framework.views import exception_handler

ERROR_CODES = {
    400: "VALIDATION_ERROR", 401: "AUTHENTICATION_REQUIRED", 403: "FORBIDDEN",
    404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 503: "SERVICE_UNAVAILABLE",
}


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    if isinstance(response.data, dict) and "error_code" in response.data:
        return response
    errors = response.data
    message = errors.get("detail") if isinstance(errors, dict) else None
    response.data = {
        "success": False,
        "error_code": ERROR_CODES.get(response.status_code, "API_ERROR"),
        "message": message or "Validation failed for one or more fields.",
        "errors": errors,
    }
    if getattr(exc, "default_code", None) == "password_change_required":
        response.data["error_code"] = "PASSWORD_CHANGE_REQUIRED"
    return response
