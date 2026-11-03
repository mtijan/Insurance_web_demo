from django.db import migrations, models


def guard_pending_password_changes(apps, schema_editor):
    users = apps.get_model("users", "CustomUser").objects.using(schema_editor.connection.alias)
    if users.filter(must_change_password=True).exists():
        raise RuntimeError("Rollback blocked: resolve pending password changes before removing enforcement state.")


class Migration(migrations.Migration):
    dependencies = [("users", "0002_quality_integrity")]
    operations = [migrations.AddField(
        model_name="customuser", name="must_change_password",
        field=models.BooleanField(default=False),
    ), migrations.RunPython(migrations.RunPython.noop, guard_pending_password_changes)]
