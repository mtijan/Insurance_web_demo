import uuid
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Round


nik_validator = RegexValidator(
    regex=r"^[0-9]{16}$",
    message="NIK must be exactly 16 numeric digits."
)


class PolicyHolder(models.Model):
    """
    Policyholder entity representing the motorcycle owner.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nik = models.CharField(
        max_length=16,
        db_index=True,
        validators=[nik_validator]
    )
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "policy_holder"
        ordering = ["full_name"]
        verbose_name = "Policy Holder"
        verbose_name_plural = "Policy Holders"

    def __str__(self):
        return f"{self.full_name} ({self.nik})"


class VehicleCategory(models.TextChoices):
    MOTOR_BARU = "MOTOR_BARU", "Motor Baru"
    MOTOR_LAMA = "MOTOR_LAMA", "Motor Lama"


class CoverageType(models.TextChoices):
    TLO = "TLO", "Total Loss Only"
    TLO_PLUS = "TLO_PLUS", "Total Loss Only Plus"
    KOMPRE_PLUS = "KOMPRE_PLUS", "Komprehensif Plus"


class AssuranceStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    REVISION = "REVISION", "Revision"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    ACTIVE = "ACTIVE", "Active"


class VehicleAssurance(models.Model):
    """
    Motorcycle assurance transaction recording vehicle details, coverage, and premiums.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assurance_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    policy_holder = models.ForeignKey(
        PolicyHolder,
        on_delete=models.PROTECT,
        related_name="assurances"
    )
    dealer = models.ForeignKey(
        "dealers.Dealer",
        on_delete=models.PROTECT,
        related_name="assurances"
    )
    vehicle_category = models.CharField(
        max_length=20,
        choices=VehicleCategory.choices
    )
    vehicle_object = models.CharField(max_length=50, default="Sepeda Motor")
    coverage_type = models.CharField(
        max_length=20,
        choices=CoverageType.choices
    )
    sum_insured = models.DecimalField(max_digits=14, decimal_places=2)
    tenor_years = models.PositiveSmallIntegerField(default=1)
    base_premium = models.DecimalField(max_digits=12, decimal_places=2)
    admin_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=35000.00
    )
    total_premium = models.DecimalField(max_digits=12, decimal_places=2)
    period_start = models.DateField()
    period_end = models.DateField()
    issuance_year = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=AssuranceStatus.choices,
        default=AssuranceStatus.DRAFT,
        db_index=True
    )
    review_notes = models.TextField(blank=True, null=True)
    verification_stage = models.CharField(max_length=20, default="WAITING", choices=[
        ("WAITING", "Waiting"), ("DATA", "Data review"),
        ("DOCUMENTS", "Document review"), ("COMPLETE", "Verification complete"),
    ])
    data_verified = models.BooleanField(default=False)
    documents_verified = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_assurances"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_assurances"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vehicle_assurance"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(sum_insured__gt=0), name="assurance_hp_positive"),
            models.CheckConstraint(condition=models.Q(tenor_years__range=(1, 5)), name="assurance_tenor_range"),
            models.CheckConstraint(condition=models.Q(base_premium__gte=0), name="assurance_base_nonnegative"),
            models.CheckConstraint(condition=models.Q(admin_fee__gte=0), name="assurance_fee_nonnegative"),
            models.CheckConstraint(condition=models.Q(total_premium__gt=0), name="assurance_total_positive"),
            models.CheckConstraint(condition=models.Q(total_premium=Round(models.F("base_premium") + models.F("admin_fee"), 2)), name="assurance_total_consistent"),
            models.CheckConstraint(condition=models.Q(issuance_year__range=(1000, 9999)), name="assurance_year_range"),
            models.CheckConstraint(condition=models.Q(period_end__gt=models.F("period_start")), name="assurance_period_order"),
        ]
        verbose_name = "Vehicle Assurance"
        verbose_name_plural = "Vehicle Assurances"

    def __str__(self):
        return f"{self.assurance_number or 'DRAFT'} - {self.policy_holder.full_name}"


class AssuranceNumberSequence(models.Model):
    """Internal annual counter, locked in the same transaction as approval."""

    year = models.PositiveIntegerField(primary_key=True)
    last_value = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "assurance_number_sequence"


class AssuranceReviewEvent(models.Model):
    """Review history exposed read-only within the assurance's current scope."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assurance = models.ForeignKey(VehicleAssurance, on_delete=models.CASCADE,
                                  related_name="review_history")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    actor_role = models.CharField(max_length=20)
    action = models.CharField(max_length=30)
    section = models.CharField(max_length=20, default="GENERAL")
    review_notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assurance_review_event"
        ordering = ["created_at", "id"]
