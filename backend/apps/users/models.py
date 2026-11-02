import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class UserRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    ADMIN = "ADMIN", "Admin Underwriting"
    AGENT = "AGENT", "Agent"
    DEALER = "DEALER", "Dealer Staff"


class CustomUser(AbstractUser):
    """
    Custom User model with UUID primary key and Role-Based Access Control (RBAC).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.DEALER,
        db_index=True
    )
    dealer = models.ForeignKey(
        "dealers.Dealer",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="staff_users",
        help_text="Dealer association for users with role DEALER."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            Lower("email"), condition=~models.Q(email=""), name="user_email_ci_unique",
        )]
        db_table = "custom_user"
        ordering = ["username"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN or self.is_superuser

    @property
    def is_admin_user(self) -> bool:
        return self.role == UserRole.ADMIN or self.is_super_admin

    @property
    def is_agent(self) -> bool:
        return self.role == UserRole.AGENT

    @property
    def is_dealer(self) -> bool:
        return self.role == UserRole.DEALER


class AuthSession(models.Model):
    """A revocable login shared by its access and refresh tokens."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="auth_sessions")
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
