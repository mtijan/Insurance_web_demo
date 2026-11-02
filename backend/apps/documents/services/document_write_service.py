
from django.db import transaction

from apps.assurances.models import VehicleAssurance
from apps.assurances.services.workflow_validation import require_editable, require_mutation_access
from apps.audit.services.audit_service import record_audit
from apps.documents.services.vault_service import (
    delete_document_from_vault, store_document_to_vault, cleanup_vault_file,
)


@transaction.atomic
def upload_assurance_document(assurance, user, document_type, uploaded_file):
    assurance = VehicleAssurance.objects.select_for_update().get(pk=assurance.pk)
    require_mutation_access(assurance, user)
    require_editable(assurance)
    document = store_document_to_vault(assurance, document_type, uploaded_file)
    try:
        record_audit(user, "CREATE", "DOCUMENT", document.pk,
                     {"assurance_id": str(assurance.pk), "document_type": document_type})
    except Exception:
        cleanup_vault_file(document.file_path)
        raise
    return document


@transaction.atomic
def remove_assurance_document(assurance, user, document_id):
    assurance = VehicleAssurance.objects.select_for_update().get(pk=assurance.pk)
    require_mutation_access(assurance, user)
    require_editable(assurance)
    document = assurance.documents.get(pk=document_id)
    record_audit(user, "DELETE", "DOCUMENT", document.pk,
                 {"assurance_id": str(assurance.pk), "document_type": document.document_type})
    delete_document_from_vault(document)
