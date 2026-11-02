from typing import List, Tuple, Set
from apps.documents.models import DocumentType


REQUIRED_MOTOR_BARU = [
    DocumentType.KTP,
    DocumentType.SURAT_JALAN,
    DocumentType.FOTO_RANGKA,
    DocumentType.FOTO_MESIN,
]

REQUIRED_MOTOR_LAMA_BASE = [
    DocumentType.KTP,
    DocumentType.STNK,
    DocumentType.FOTO_DEPAN,
    DocumentType.FOTO_BELAKANG,
    DocumentType.FOTO_KANAN,
    DocumentType.FOTO_KIRI,
]


def get_required_document_types(vehicle_category: str) -> List[str]:
    """
    Returns the list of required document types based on vehicle category.
    """
    if vehicle_category == "MOTOR_BARU":
        return [dt.value for dt in REQUIRED_MOTOR_BARU]
    elif vehicle_category == "MOTOR_LAMA":
        return [
            dt.value for dt in REQUIRED_MOTOR_LAMA_BASE
        ] + [f"{DocumentType.FOTO_RANGKA.value} OR {DocumentType.FOTO_MESIN.value}"]
    return []


def validate_document_completeness(
    vehicle_category: str,
    uploaded_doc_types: Set[str]
) -> Tuple[bool, List[str]]:
    """
    Validates uploaded documents against business rules:
    - MOTOR_BARU: KTP, SURAT_JALAN, FOTO_RANGKA, FOTO_MESIN
    - MOTOR_LAMA: KTP, STNK, 4 sides, and at least one of (FOTO_RANGKA, FOTO_MESIN)
    Returns: (is_complete: bool, missing_documents: List[str])
    """
    missing: List[str] = []

    if vehicle_category == "MOTOR_BARU":
        for req in REQUIRED_MOTOR_BARU:
            if req.value not in uploaded_doc_types:
                missing.append(req.value)

    elif vehicle_category == "MOTOR_LAMA":
        for req in REQUIRED_MOTOR_LAMA_BASE:
            if req.value not in uploaded_doc_types:
                missing.append(req.value)

        has_rangka = DocumentType.FOTO_RANGKA.value in uploaded_doc_types
        has_mesin = DocumentType.FOTO_MESIN.value in uploaded_doc_types
        if not (has_rangka or has_mesin):
            missing.append(f"{DocumentType.FOTO_RANGKA.value} or {DocumentType.FOTO_MESIN.value}")

    return len(missing) == 0, missing
