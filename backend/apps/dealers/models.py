import uuid
from django.conf import settings
from django.db import models


class Dealer(models.Model):
    """
    Master dealer entity for motorcycle dealership branches.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dealer"
        ordering = ["code"]
        verbose_name = "Dealer"
        verbose_name_plural = "Dealers"

    def __str__(self):
        return f"{self.code} - {self.name}"


class AgentDealerAssignment(models.Model):
    """
    Many-to-many relationship assigning an Agent to multiple managed Dealers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dealer_assignments"
    )
    dealer = models.ForeignKey(
        Dealer,
        on_delete=models.CASCADE,
        related_name="agent_assignments"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "agent_dealer_assignment"
        unique_together = ("agent", "dealer")
        ordering = ["-assigned_at"]
        verbose_name = "Agent Dealer Assignment"
        verbose_name_plural = "Agent Dealer Assignments"

    def __str__(self):
        return f"Agent {self.agent.username} -> Dealer {self.dealer.code}"
