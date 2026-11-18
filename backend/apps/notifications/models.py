import uuid

from django.conf import settings
from django.db import models


class NotificationEventType(models.TextChoices):
    """Supported in-app assurance lifecycle and note notification event types."""

    ASSURANCE_SUBMITTED = "ASSURANCE_SUBMITTED", "Assurance submitted"
    REVISION_REQUESTED = "REVISION_REQUESTED", "Revision requested"
    ASSURANCE_APPROVED = "ASSURANCE_APPROVED", "Assurance approved"
    ASSURANCE_REJECTED = "ASSURANCE_REJECTED", "Assurance rejected"
    ASSURANCE_NOTE = "ASSURANCE_NOTE", "Assurance note added"


class Notification(models.Model):
    """Transactional in-app notification scoped strictly to a single recipient."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
    )
    assurance = models.ForeignKey(
        "assurances.VehicleAssurance",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    event_type = models.CharField(max_length=40, choices=NotificationEventType.choices)
    actor_role = models.CharField(max_length=20, blank=True, default="")
    actor_username = models.CharField(max_length=150, blank=True, default="")
    title = models.CharField(max_length=120)
    message = models.CharField(max_length=255)
    target_path = models.CharField(max_length=200)
    dedupe_key = models.CharField(max_length=120, null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["recipient", "-created_at", "-id"], name="notif_recipient_created_idx"),
            models.Index(fields=["recipient", "read_at"], name="notif_recipient_unread_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "dedupe_key"],
                condition=models.Q(dedupe_key__isnull=False),
                name="notif_recipient_dedupe_uq",
            ),
        ]

    def __str__(self):
        return f"{self.event_type} -> {self.recipient_id}"
