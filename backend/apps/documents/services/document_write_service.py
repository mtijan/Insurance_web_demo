
from django.db import transaction
import logging

from apps.assurances.models import VehicleAssurance
from apps.assurances.services.workflow_validation import require_editable, require_mutation_access
from apps.audit.services.audit_service import record_audit
from apps.documents.services.vault_service import (
    delete_document_from_vault, store_document_to_vault, cleanup_vault_file,
)
from apps.documents.services.vault_lock import vault_write_lock
from apps.documents.services.vault_paths import StorageUnavailable
from rest_framework.exceptions import ValidationError
from apps.documents.models import DocumentType


def upload_assurance_document(assurance, user, document_type, uploaded_file):
    return upload_assurance_documents(assurance, user, [(document_type, uploaded_file)])[0]


def compensate(documents):
    for document in documents:
        try:
            cleanup_vault_file(document.file_path)
        except (OSError, ValidationError, StorageUnavailable):
            logging.getLogger(__name__).error("Vault compensation deferred to explicit recovery.")


def upload_assurance_documents(assurance, user, items):
    documents = []
    if not 1 <= len(items) <= 10:
        raise ValidationError("Upload 1-10 documents per batch.")
    with vault_write_lock():
        try:
            with transaction.atomic(durable=True):
                assurance = VehicleAssurance.objects.select_for_update().get(pk=assurance.pk)
                require_mutation_access(assurance, user)
                require_editable(assurance)
                for document_type, uploaded_file in items:
                    if document_type not in DocumentType.values:
                        raise ValidationError({"document_type": "Invalid document type."})
                    document = store_document_to_vault(assurance, document_type, uploaded_file)
                    documents.append(document)
                    record_audit(user, "CREATE", "DOCUMENT", document.pk,
                                 {"assurance_id": str(assurance.pk), "document_type": document_type})
        except Exception as exc:
            compensate(documents)
            if isinstance(exc, OSError):
                raise StorageUnavailable() from exc
            raise
    return documents


def remove_assurance_document(assurance, user, document_id):
    with vault_write_lock(), transaction.atomic(durable=True):
        assurance = VehicleAssurance.objects.select_for_update().get(pk=assurance.pk)
        require_mutation_access(assurance, user)
        require_editable(assurance)
        document = assurance.documents.get(pk=document_id)
        record_audit(user, "DELETE", "DOCUMENT", document.pk,
                     {"assurance_id": str(assurance.pk), "document_type": document.document_type})
        delete_document_from_vault(document)
