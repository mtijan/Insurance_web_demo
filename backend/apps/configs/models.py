import uuid

from django.conf import settings
from django.db import models


class SystemConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_config"
