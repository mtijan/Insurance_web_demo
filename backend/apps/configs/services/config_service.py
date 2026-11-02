from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from apps.audit.services.audit_service import record_audit
from apps.configs.models import SystemConfig
from apps.configs.serializers import AdminFeeUpdateSerializer

ADMIN_FEE_KEY = "ADMIN_FEE_AMOUNT"
DEFAULT_ADMIN_FEE = Decimal("35000.00")


def get_admin_fee():
    value = SystemConfig.objects.filter(key=ADMIN_FEE_KEY).values_list(
        "value", flat=True,
    ).first()
    return Decimal(value) if value is not None else DEFAULT_ADMIN_FEE


@transaction.atomic
def update_admin_fee(user, data):
    if not (user.is_active and user.is_super_admin):
        raise PermissionDenied("Only Super Admin may update the admin fee.")
    serializer = AdminFeeUpdateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    config, created = SystemConfig.objects.select_for_update().get_or_create(
        key=ADMIN_FEE_KEY,
        defaults={"value": f"{values['admin_fee']:.2f}",
                  "description": values["reason"], "updated_by": user},
    )
    old_value = f"{DEFAULT_ADMIN_FEE:.2f}" if created else config.value
    config.value = f"{values['admin_fee']:.2f}"
    config.description = values["reason"]
    config.updated_by = user
    config.save()
    record_audit(user, "UPDATE_CONFIG", "SYSTEM_CONFIG", config.id, {
        "admin_fee": {"old": old_value, "new": config.value},
        "reason_present": bool(config.description),
    })
    return config
