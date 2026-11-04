"""Additive read filters; always intersect an already authorized queryset."""
from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from rest_framework.exceptions import ValidationError
from apps.assurances.models import AssuranceStatus


def parse_date(params, name):
    value = params.get(name)
    if not value:
        return None
    try:
        result = date.fromisoformat(value)
        if result.isoformat() != value or result == date.max:
            raise ValueError()
        return result
    except (ValueError, TypeError) as exc:
        raise ValidationError({name: "Use YYYY-MM-DD before 9999-12-31."}) from exc


def filter_assurances(queryset, params):
    status = params.get("status")
    if status:
        if status not in AssuranceStatus.values:
            raise ValidationError({"status": "Invalid assurance status."})
        queryset = queryset.filter(status=status)
    dealer = params.get("dealer_id")
    if dealer:
        try:
            dealer = UUID(dealer)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValidationError({"dealer_id": "Use a valid dealer UUID."}) from exc
        queryset = queryset.filter(dealer_id=dealer)
    return filter_dates(queryset, params)


def filter_dates(queryset, params):
    first, last = parse_date(params, "date_from"), parse_date(params, "date_to")
    if first and last and first > last:
        raise ValidationError({"date_to": "End date must not precede start date."})
    zone = ZoneInfo("Asia/Jakarta")
    if first:
        queryset = queryset.filter(created_at__gte=datetime.combine(first, time.min, zone))
    if last:
        queryset = queryset.filter(created_at__lt=datetime.combine(last + timedelta(days=1), time.min, zone))
    return queryset
