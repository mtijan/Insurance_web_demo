from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import DealerAccessPermission, AssignmentAccessPermission
from .selectors.dealer_selector import get_dealers_for_user, get_assignments_for_user
from .serializers import (
    DealerSerializer,
    DealerSummarySerializer,
    AgentDealerAssignmentSerializer,
)
from .services.dealer_service import (
    create_dealer,
    update_dealer,
    assign_agent_to_dealer, delete_dealer, delete_assignment, update_assignment,
)


class DealerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Dealer branches.
    - Super Admin: Full CRUD.
    - Admin: Read all dealers.
    - Agent: Read assigned dealers only.
    - Dealer: Read own dealer only.
    """
    permission_classes = [IsAuthenticated, DealerAccessPermission]

    def get_queryset(self):
        active_only = self.request.query_params.get("active_only", "false").lower() == "true"
        return get_dealers_for_user(self.request.user, active_only=active_only)

    def get_serializer_class(self):
        if self.action == "list" and self.request.query_params.get("summary") == "true":
            return DealerSummarySerializer
        return DealerSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Dealer list retrieved successfully.",
            "data": serializer.data,
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "data": serializer.data,
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dealer = create_dealer(serializer.validated_data, actor=request.user)
        output_serializer = self.get_serializer(dealer)
        return Response({
            "success": True,
            "message": "Dealer created successfully.",
            "data": output_serializer.data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=kwargs.get("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        dealer = update_dealer(instance, serializer.validated_data, actor=request.user)
        output_serializer = self.get_serializer(dealer)
        return Response({
            "success": True,
            "message": "Dealer updated successfully.",
            "data": output_serializer.data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_dealer(instance, request.user)
        return Response({
            "success": True,
            "message": "Dealer deleted successfully.",
        }, status=status.HTTP_200_OK)


class AgentDealerAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Agent to Dealer branch assignments.
    - Super Admin: Full CRUD.
    - Agent: Read own assignments only.
    """
    permission_classes = [IsAuthenticated, AssignmentAccessPermission]
    serializer_class = AgentDealerAssignmentSerializer

    def get_queryset(self):
        return get_assignments_for_user(self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Agent assignments retrieved successfully.",
            "data": serializer.data,
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = serializer.validated_data["agent"]
        dealer = serializer.validated_data["dealer"]
        assignment = assign_agent_to_dealer(agent=agent, dealer=dealer, actor=request.user)
        output_serializer = self.get_serializer(assignment)
        return Response({
            "success": True,
            "message": "Agent assigned to dealer successfully.",
            "data": output_serializer.data,
        }, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_assignment(instance, request.user)
        return Response({
            "success": True,
            "message": "Assignment deleted successfully.",
        }, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.instance = update_assignment(serializer.instance, serializer.validated_data,
                                                actor=self.request.user)
