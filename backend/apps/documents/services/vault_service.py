import logging
import uuid
from pathlib import Path
from django.db import transaction
from django.core.files.uploadedfile import UploadedFile
from rest_framework.exceptions import ValidationError

from apps.documents.models import AssuranceDocument
from apps.documents.services.vault_paths import resolve_vault_path, StorageUnavailable
from apps.documents.services.image_validation import verify_decodable_image

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
logger = logging.getLogger(__name__)


def verify_image_magic_bytes(file_obj: UploadedFile) -> str:
    """
    Verifies that the uploaded file binary header matches valid image types.
    Returns detected mime type string or raises ValidationError.
    """
    initial_pos = file_obj.tell()
    file_obj.seek(0)
    header = file_obj.read(32)
    file_obj.seek(initial_pos)

    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    elif header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    elif len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"

    raise ValidationError("Invalid file content. Only JPEG, PNG, and WebP images are allowed.")


def store_document_to_vault(assurance, doc_type: str, uploaded_file: UploadedFile) -> AssuranceDocument:
    """
    Stores an uploaded physical document into the protected vault.
    Obfuscates the filename using UUIDv4 and records metadata.
    """
    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValidationError(f"File size exceeds maximum allowed limit of 5 MB ({uploaded_file.size} bytes).")

    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix in {".exe", ".sh", ".bat", ".php", ".js"}:
        raise ValidationError("Executable file extensions are forbidden.")
    mime_type = verify_image_magic_bytes(uploaded_file)
    verify_decodable_image(uploaded_file)

    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[mime_type]

    obfuscated_name = f"{uuid.uuid4().hex}{ext}"
    rel_path = str(Path("vault") / str(assurance.id) / obfuscated_name)
    target_path = resolve_vault_path(rel_path)

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        return AssuranceDocument.objects.create(
            assurance=assurance, document_type=doc_type, file_path=rel_path,
            original_filename=uploaded_file.name, file_size=uploaded_file.size,
            mime_type=mime_type,
        )
    except Exception:
        cleanup_vault_file(rel_path)
        raise


def delete_document_from_vault(document: AssuranceDocument) -> None:
    """
    Deletes the physical file from the vault and removes the database record.
    """
    resolve_vault_path(document.file_path)
    relative = document.file_path
    document.delete()
    transaction.on_commit(lambda: remove_vault_file(relative))


def remove_vault_file(relative):
    try:
        cleanup_vault_file(relative)
    except (OSError, ValidationError, StorageUnavailable):
        logger.error("Could not remove a vault file after transaction completion.")


def cleanup_vault_file(relative):
    resolve_vault_path(relative).unlink(missing_ok=True)
