from decimal import Decimal

from rest_framework import serializers


class AdminFeeUpdateSerializer(serializers.Serializer):
    admin_fee = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.00"),
    )
    reason = serializers.CharField(max_length=1000)
