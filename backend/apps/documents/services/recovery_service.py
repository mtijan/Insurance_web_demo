"""Explicit operator reconciliation, never an automatic retention policy."""
from pathlib import Path
import re
from time import time

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.documents.models import AssuranceDocument
from apps.documents.services.vault_lock import vault_write_lock
from apps.documents.services.vault_paths import resolve_vault_path

GENERATED_FILE = re.compile(r"vault/[a-f0-9-]{36}/[a-f0-9]{32}\.(jpg|png|webp)$")


def generated_candidate(path, relative):
    return GENERATED_FILE.fullmatch(relative) and not path.is_symlink() and path.is_file()


def reconcile_vault(grace_seconds, apply=False):
    if grace_seconds < 0:
        raise ValidationError("Grace period must be nonnegative.")
    with vault_write_lock(), transaction.atomic(durable=True):
        root = Path(settings.MEDIA_ROOT)
        references = {Path(value).as_posix() for value in AssuranceDocument.objects.values_list("file_path", flat=True)}
        missing = sum(not resolve_vault_path(value).is_file() for value in references)
        result = {"missing_referenced": missing, "orphan_candidates": 0, "removed": 0,
                  "apply": apply, "grace_seconds": grace_seconds}
        for path in (root / "vault").glob("*/*"):
            relative = path.relative_to(root).as_posix()
            if not generated_candidate(path, relative):
                continue
            resolve_vault_path(relative)
            if relative in references or time() - path.stat().st_mtime < grace_seconds:
                continue
            result["orphan_candidates"] += 1
            if apply:
                path.unlink()
                result["removed"] += 1
        return result
