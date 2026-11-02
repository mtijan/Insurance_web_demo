from rest_framework import serializers
from apps.dealers.models import Dealer, AgentDealerAssignment
from apps.users.models import CustomUser, UserRole


class DealerSerializer(serializers.ModelSerializer):
    """
    Full serializer for Dealer entity CRUD operations.
    """
    class Meta:
        model = Dealer
        fields = [
            "id",
            "code",
            "name",
            "address",
            "phone",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DealerSummarySerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for dropdowns and selection lists.
    """
    class Meta:
        model = Dealer
        fields = ["id", "code", "name", "is_active"]
        read_only_fields = ["id", "code", "name", "is_active"]


class AgentDealerAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for managing Agent to Dealer branch assignments.
    """
    agent_username = serializers.CharField(source="agent.username", read_only=True)
    agent_email = serializers.CharField(source="agent.email", read_only=True)
    dealer_code = serializers.CharField(source="dealer.code", read_only=True)
    dealer_name = serializers.CharField(source="dealer.name", read_only=True)

    class Meta:
        model = AgentDealerAssignment
        fields = [
            "id",
            "agent",
            "agent_username",
            "agent_email",
            "dealer",
            "dealer_code",
            "dealer_name",
            "assigned_at",
        ]
        read_only_fields = ["id", "assigned_at"]

    def validate_agent(self, value: CustomUser) -> CustomUser:
        if value.role != UserRole.AGENT:
            raise serializers.ValidationError(
                f"Assigned user must have AGENT role. Current role is '{value.role}'."
            )
        return value

    def validate(self, attrs):
        agent = attrs.get("agent")
        dealer = attrs.get("dealer")
        if not self.instance and agent and dealer:
            if AgentDealerAssignment.objects.filter(agent=agent, dealer=dealer).exists():
                raise serializers.ValidationError(
                    "This agent is already assigned to the selected dealer."
                )
        return attrs
