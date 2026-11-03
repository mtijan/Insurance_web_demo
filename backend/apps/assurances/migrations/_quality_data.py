"""Frozen data checks for migration 0003; never import runtime models."""
import uuid

from django.db.models import Count, F, Q
from django.db.models.functions import Round


def preflight(apps, schema_editor):
    assurances = apps.get_model("assurances", "VehicleAssurance").objects.using(schema_editor.connection.alias)
    valid = (Q(sum_insured__gt=0) & Q(tenor_years__range=(1, 5)) &
             Q(base_premium__gte=0) & Q(admin_fee__gte=0) & Q(total_premium__gt=0) &
             Q(total_premium=Round(F("base_premium") + F("admin_fee"), 2)) &
             Q(issuance_year__range=(1000, 9999)) & Q(period_end__gt=F("period_start")))
    invalid = assurances.exclude(valid).count()
    if invalid:
        raise RuntimeError(f"Migration blocked: {invalid} invalid financial rows. Reconcile with backup before retrying; no rows deleted.")


def split_shared_holders(apps, schema_editor):
    alias = schema_editor.connection.alias
    holder_model = apps.get_model("assurances", "PolicyHolder")
    assurances = apps.get_model("assurances", "VehicleAssurance").objects.using(alias)
    shared = assurances.values("policy_holder_id").annotate(total=Count("pk")).filter(total__gt=1)
    for group in list(shared):
        holder = holder_model.objects.using(alias).get(pk=group["policy_holder_id"])
        references = assurances.filter(policy_holder_id=holder.pk).order_by("created_at", "pk")
        for assurance in list(references)[1:]:
            clone = holder_model.objects.using(alias).create(
                id=uuid.uuid4(), nik=holder.nik, full_name=holder.full_name,
                phone=holder.phone, address=holder.address,
            )
            holder_model.objects.using(alias).filter(pk=clone.pk).update(created_at=holder.created_at)
            assurances.filter(pk=assurance.pk).update(policy_holder_id=clone.pk)


def validate_pending_constraints(apps, schema_editor):
    """Drain deferred PostgreSQL FK checks before schema changes, still atomically."""
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("SET CONSTRAINTS ALL IMMEDIATE")


def ensure_unique_nik(apps, schema_editor):
    holders = apps.get_model("assurances", "PolicyHolder").objects.using(schema_editor.connection.alias)
    if holders.values("nik").annotate(total=Count("pk")).filter(total__gt=1).exists():
        raise RuntimeError("Rollback blocked: repeated NIK snapshots cannot safely regain global uniqueness. Restore backup or reconcile explicitly; no records deleted.")
