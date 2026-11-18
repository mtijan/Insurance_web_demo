from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Django configuration for transactional in-app notifications."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
