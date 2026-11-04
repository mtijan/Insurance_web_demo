from decimal import Decimal
from rest_framework import serializers

from apps.assurances.models import (
    PolicyHolder,
    VehicleAssurance,
    VehicleCategory,
    CoverageType,
    nik_validator,
    AssuranceReviewEvent,
)
from apps.dealers.models import Dealer
from apps.assurances.services.input_validation import normalize_name
from apps.assurances.services.workflow_validation import require_editable, require_mutation_access
from rest_framework.exceptions import APIException
from apps.dealers.serializers import DealerSummarySerializer
from apps.documents.serializers import AssuranceDocumentSerializer
from apps.documents.services.vault_paths import available_document_types
from apps.documents.services.document_validator import (
    get_required_document_types,
    validate_document_completeness,
)


class PolicyHolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyHolder
        fields = ["id", "nik", "full_name", "phone", "address", "created_at"]
        read_only_fields = ["id", "created_at"]


class CalculatePremiumQuerySerializer(serializers.Serializer):
    sum_insured = serializers.DecimalField(
        min_value=Decimal("1000000.00"),
        max_digits=14,
        decimal_places=2
    )
    coverage_type = serializers.ChoiceField(choices=CoverageType.choices)
    tenor_years = serializers.IntegerField(min_value=1, max_value=5, default=1)


class AssuranceDraftCreateSerializer(serializers.Serializer):
    def validate_policy_holder_name(self, value):
        return normalize_name(value)

    policy_holder_name = serializers.CharField(max_length=100)
    policy_holder_nik = serializers.CharField(max_length=16, validators=[nik_validator])
    policy_holder_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    policy_holder_address = serializers.CharField(required=False, allow_blank=True)
    dealer_id = serializers.PrimaryKeyRelatedField(
        queryset=Dealer.objects.filter(is_active=True),
        source="dealer"
    )
    vehicle_category = serializers.ChoiceField(choices=VehicleCategory.choices)
    vehicle_object = serializers.CharField(max_length=50, default="Sepeda Motor", required=False)
    coverage_type = serializers.ChoiceField(choices=CoverageType.choices)
    sum_insured = serializers.DecimalField(
        min_value=Decimal("1000000.00"),
        max_digits=14,
        decimal_places=2
    )
    tenor_years = serializers.IntegerField(min_value=1, max_value=5, default=1)
    period_start = serializers.DateField()
    issuance_year = serializers.IntegerField(required=False, min_value=1000, max_value=9999)


class AssuranceListSerializer(serializers.ModelSerializer):
    policy_holder_name = serializers.CharField(source="policy_holder.full_name", read_only=True)
    policy_holder_nik = serializers.CharField(source="policy_holder.nik", read_only=True)
    dealer_code = serializers.CharField(source="dealer.code", read_only=True)
    dealer_name = serializers.CharField(source="dealer.name", read_only=True)

    class Meta:
        model = VehicleAssurance
        fields = [
            "id",
            "assurance_number",
            "policy_holder_name",
            "policy_holder_nik",
            "dealer_code",
            "dealer_name",
            "vehicle_category",
            "coverage_type",
            "sum_insured",
            "total_premium",
            "status",
            "verification_stage",
            "data_verified",
            "documents_verified",
            "created_at",
        ]


class ReviewEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssuranceReviewEvent
        fields = ["id", "action", "section", "review_notes", "actor_role", "created_at"]
        read_only_fields = fields


class AssuranceDetailSerializer(serializers.ModelSerializer):
    can_edit = serializers.SerializerMethodField()
    policy_holder = PolicyHolderSerializer(read_only=True)
    dealer = DealerSummarySerializer(read_only=True)
    documents = AssuranceDocumentSerializer(many=True, read_only=True)
    required_documents = serializers.SerializerMethodField()
    is_documents_complete = serializers.SerializerMethodField()
    missing_documents = serializers.SerializerMethodField()
    review_history = ReviewEventSerializer(many=True, read_only=True)

    class Meta:
        model = VehicleAssurance
        read_only_fields = ["verification_stage", "data_verified", "documents_verified"]
        fields = [
            "id",
            "assurance_number",
            "policy_holder",
            "dealer",
            "vehicle_category",
            "vehicle_object",
            "coverage_type",
            "sum_insured",
            "tenor_years",
            "base_premium",
            "admin_fee",
            "total_premium",
            "period_start",
            "period_end",
            "issuance_year",
            "status",
            "review_notes",
            "verification_stage",
            "data_verified",
            "documents_verified",
            "review_history",
            "created_at",
            "updated_at",
            "required_documents",
            "documents",
            "is_documents_complete",
            "missing_documents",
            "can_edit",
        ]

    def get_required_documents(self, obj: VehicleAssurance) -> list:
        return get_required_document_types(obj.vehicle_category)

    def get_can_edit(self, obj):
        request = self.context.get("request")
        if request is None:
            return False
        try:
            require_editable(obj)
            require_mutation_access(obj, request.user)
        except APIException:
            return False
        return True

    def get_is_documents_complete(self, obj: VehicleAssurance) -> bool:
        uploaded_types = available_document_types(obj)
        complete, _ = validate_document_completeness(obj.vehicle_category, uploaded_types)
        return complete

    def get_missing_documents(self, obj: VehicleAssurance) -> list:
        uploaded_types = available_document_types(obj)
        _, missing = validate_document_completeness(obj.vehicle_category, uploaded_types)
        return missing
