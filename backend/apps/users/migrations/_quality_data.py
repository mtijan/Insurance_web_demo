"""Frozen email preflight for migration 0002."""
from django.db.models import Count
from django.db.models.functions import Lower


def check_emails(apps, schema_editor):
    users = apps.get_model("users", "CustomUser").objects.using(schema_editor.connection.alias)
    duplicates = users.exclude(email="").annotate(identity=Lower("email")).values("identity").annotate(total=Count("pk")).filter(total__gt=1).count()
    if duplicates:
        raise RuntimeError(f"Migration blocked: {duplicates} duplicate email groups. Reconcile identities explicitly before retrying; no accounts changed.")
