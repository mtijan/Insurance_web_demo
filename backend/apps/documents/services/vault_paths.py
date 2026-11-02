"""Contain all I/O within the configured private vault."""
from pathlib import Path, PureWindowsPath

from django.conf import settings
from rest_framework.exceptions import APIException, NotFound, ValidationError


class StorageUnavailable(APIException):
    status_code = 503
    default_detail = "Document storage is unavailable. Please retry."


def resolve_vault_path(relative):
    path = Path(relative)
    windows = PureWindowsPath(relative)
    if path.is_absolute() or windows.is_absolute() or windows.drive:
        raise ValidationError("Invalid document storage reference.")
    try:
        root = (Path(settings.MEDIA_ROOT) / "vault").resolve()
        target = (Path(settings.MEDIA_ROOT) / path).resolve()
        target.relative_to(root)
    except (ValueError, RuntimeError) as exc:
        raise ValidationError("Invalid document storage reference.") from exc
    except OSError as exc:
        raise StorageUnavailable() from exc
    if target == root:
        raise ValidationError("Invalid document storage reference.")
    return target


def open_vault_file(relative):
    path = resolve_vault_path(relative)
    try:
        return path.open("rb")
    except FileNotFoundError as exc:
        raise NotFound("Document file is missing.") from exc
    except OSError as exc:
        raise StorageUnavailable() from exc


def available_document_types(assurance):
    available = set()
    for document in assurance.documents.all():
        try:
            with open_vault_file(document.file_path) as stream:
                if stream.read(1):
                    available.add(document.document_type)
        except (NotFound, ValidationError):
            continue
        except OSError as exc:
            raise StorageUnavailable() from exc
    return available
