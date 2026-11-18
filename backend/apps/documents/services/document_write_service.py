import logging

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.assurances.services.workflow_validation import (
    get_locked_assurance, require_editable, require_mutation_access,
)
from apps.audit.services.audit_service import record_audit
from apps.documents.services.vault_lock import vault_write_lock
from apps.documents.services.vault_paths import StorageUnavailable
from apps.documents.services.vault_service import (
    cleanup_vault_file, delete_document_from_vault, store_document_to_vault,
)

MAX_DOCUMENTS_PER_ASSURANCE = 20


def upload_assurance_document(assurance, user, document_type, uploaded_file):
    return upload_assurance_documents(assurance, user, [(document_type, uploaded_file)])[0]


def compensate(documents):
    for document in documents:
        try:
            cleanup_vault_file(document.file_path)
        except (OSError, ValidationError, StorageUnavailable):
            logging.getLogger(__name__).error("Vault compensation deferred to explicit recovery.")


def persist_documents_batch(assurance, user, items, documents):
    with transaction.atomic(durable=True):
        locked = get_locked_assurance(assurance.pk)
        require_mutation_access(locked, user)
        require_editable(locked)
        if locked.documents.count() + len(items) > MAX_DOCUMENTS_PER_ASSURANCE:
            raise ValidationError(f"Maximum {MAX_DOCUMENTS_PER_ASSURANCE} documents allowed per assurance.")
        for document_type, uploaded_file in items:
            document = store_document_to_vault(locked, document_type, uploaded_file)
            documents.append(document)
            record_audit(user, "CREATE", "DOCUMENT", document.pk,
                         {"assurance_id": str(locked.pk), "document_type": document_type})


def upload_assurance_documents(assurance, user, items):
    if not 1 <= len(items) <= 10:
        raise ValidationError("Upload 1-10 documents per batch.")
    require_mutation_access(assurance, user)
    require_editable(assurance)
    documents = []
    with vault_write_lock(scope=str(assurance.pk), shared=True):
        try:
            persist_documents_batch(assurance, user, items, documents)
        except Exception as exc:
            compensate(documents)
            if isinstance(exc, OSError):
                raise StorageUnavailable() from exc
            raise
    return documents


def remove_assurance_document(assurance, user, document_id):
    with vault_write_lock(scope=str(assurance.pk), shared=True), transaction.atomic(durable=True):
        locked = get_locked_assurance(assurance.pk)
        require_mutation_access(locked, user)
        require_editable(locked)
        document = locked.documents.get(pk=document_id)
        record_audit(user, "DELETE", "DOCUMENT", document.pk,
                     {"assurance_id": str(locked.pk), "document_type": document.document_type})
        delete_document_from_vault(document)
