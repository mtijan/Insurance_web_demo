from ipaddress import ip_address

from django.db import DatabaseError
from rest_framework.exceptions import APIException

from apps.audit.middleware import audit_request
from apps.audit.models import AuditLog


class AuditUnavailable(APIException):
    status_code = 503
    default_detail = "Audit recording is unavailable. Please retry."


def record_audit(user, action, entity_name, entity_id, changes=None):
    request = audit_request.get()
    address = request.META.get("REMOTE_ADDR") if request else None
    try:
        address = str(ip_address(address)) if address else None
    except ValueError:
        address = None
    try:
        return AuditLog.objects.create(
            user=user, action=action, entity_name=entity_name,
            entity_id=str(entity_id), changes=changes or {}, ip_address=address,
        )
    except DatabaseError as exc:
        raise AuditUnavailable() from exc
