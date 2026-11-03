import datetime
from decimal import Decimal

from django.db import transaction
from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework.exceptions import ValidationError

from apps.assurances.models import AssuranceStatus, PolicyHolder, VehicleAssurance
from apps.assurances.services.pricing_calculator import calculate_premium
from apps.assurances.services.workflow_validation import require_editable, require_mutation_access
from apps.audit.services.audit_service import record_audit
from apps.configs.services.config_service import get_admin_fee
from apps.assurances.services.input_validation import validate_draft_input


def calculate_end_date(start_date: datetime.date, tenor_years: int) -> datetime.date:
    """Calculate coverage end date, including leap years."""
    if not 1 <= tenor_years <= 5 or start_date.year + tenor_years > 9999:
        raise ValidationError({"period_start": "Coverage end date is outside the supported range."})
    try:
        return start_date.replace(year=start_date.year + tenor_years)
    except ValueError:
        return start_date.replace(year=start_date.year + tenor_years, day=28)


def validate_dealer_access_for_creation(user, dealer):
    if user.is_super_admin or user.is_admin_user:
        return
    if user.is_dealer and user.dealer_id == dealer.id:
        return
    if user.is_agent and user.dealer_assignments.filter(dealer=dealer).exists():
        return
    raise ValidationError("User may only register assurances for authorized dealers.")


def calculate_pricing_fields(data, admin_fee):
    result = calculate_premium(
        sum_insured=Decimal(str(data["sum_insured"])), coverage_type=data["coverage_type"],
        tenor_years=data.get("tenor_years", 1), admin_fee=admin_fee,
    )
    return {key: Decimal(result[key]) for key in (
        "base_premium", "admin_fee", "total_premium",
    )}


def save_holder(data):
    return PolicyHolder.objects.create(
        nik=data["policy_holder_nik"], full_name=data["policy_holder_name"],
        phone=data.get("policy_holder_phone", ""),
        address=data.get("policy_holder_address", ""),
    )


@transaction.atomic
def create_assurance_draft(user, data):
    validate_dealer_access_for_creation(user, data["dealer"])
    data = validate_draft_input(data)
    fields = {key: data[key] for key in (
        "dealer", "vehicle_category", "coverage_type", "sum_insured", "period_start",
    )}
    tenor = data.get("tenor_years", 1)
    fields.update(calculate_pricing_fields(data, get_admin_fee()))
    validate_draft_fields(data, fields)
    assurance = VehicleAssurance.objects.create(
        **fields, policy_holder=save_holder(data), tenor_years=tenor,
        vehicle_object=data.get("vehicle_object", "Sepeda Motor"),
        period_end=calculate_end_date(data["period_start"], tenor),
        issuance_year=data.get("issuance_year", data["period_start"].year),
        status=AssuranceStatus.DRAFT, created_by=user,
    )
    record_audit(user, "CREATE", "VEHICLE_ASSURANCE", assurance.pk,
                 {"status": {"old": None, "new": assurance.status}})
    return assurance


def update_holder(holder, data):
    if not any(key.startswith("policy_holder_") for key in data):
        return holder
    # Copy on write also protects legacy records shared before migration.
    holder.pk = None
    holder._state.adding = True
    for source, target in (
        ("policy_holder_name", "full_name"), ("policy_holder_nik", "nik"),
        ("policy_holder_phone", "phone"), ("policy_holder_address", "address"),
    ):
        if source in data:
            setattr(holder, target, data[source])
    try:
        holder.full_clean()
    except ModelValidationError as exc:
        raise ValidationError(exc.message_dict) from exc
    holder.save()
    return holder


@transaction.atomic
def update_assurance_draft(assurance, user, data):
    assurance = VehicleAssurance.objects.select_for_update().get(pk=assurance.pk)
    require_mutation_access(assurance, user)
    require_editable(assurance)
    data = validate_draft_input(data)
    if "dealer" in data:
        validate_dealer_access_for_creation(user, data["dealer"])
    assurance.policy_holder = update_holder(assurance.policy_holder, data)
    for key in ("dealer", "vehicle_category", "vehicle_object", "sum_insured",
                "coverage_type", "tenor_years", "period_start", "issuance_year"):
        if key in data:
            setattr(assurance, key, data[key])
    pricing = calculate_pricing_fields({
        "sum_insured": assurance.sum_insured, "coverage_type": assurance.coverage_type,
        "tenor_years": assurance.tenor_years,
    }, assurance.admin_fee)
    for key, value in pricing.items():
        setattr(assurance, key, value)
    assurance.period_end = calculate_end_date(assurance.period_start, assurance.tenor_years)
    validate_draft_fields(vars(assurance), pricing)
    assurance.save()
    record_audit(user, "UPDATE", "VEHICLE_ASSURANCE", assurance.pk,
                 {"fields": sorted(data), "status": assurance.status})
    return assurance


def validate_draft_fields(data, pricing):
    calculate_end_date(data["period_start"], data.get("tenor_years", 1))
    year = data.get("issuance_year", data["period_start"].year)
    if not 1000 <= year <= 9999:
        raise ValidationError({"issuance_year": "Use a four-digit year (1000-9999)."})
    if pricing["total_premium"] <= 0 or pricing["total_premium"] > Decimal("9999999999.99"):
        raise ValidationError({"sum_insured": "Calculated premium exceeds the supported amount."})
