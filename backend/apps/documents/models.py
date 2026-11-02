import uuid
from django.db import models


class DocumentType(models.TextChoices):
    KTP = "KTP", "KTP Tertanggung"
    SURAT_JALAN = "SURAT_JALAN", "Surat Jalan"
    STNK = "STNK", "STNK Tertanggung"
    FOTO_DEPAN = "FOTO_DEPAN", "Foto Motor Tampak Depan"
    FOTO_BELAKANG = "FOTO_BELAKANG", "Foto Motor Tampak Belakang"
    FOTO_KANAN = "FOTO_KANAN", "Foto Motor Tampak Kanan"
    FOTO_KIRI = "FOTO_KIRI", "Foto Motor Tampak Kiri"
    FOTO_RANGKA = "FOTO_RANGKA", "Foto Nomor Rangka"
    FOTO_MESIN = "FOTO_MESIN", "Foto Nomor Mesin"


class AssuranceDocument(models.Model):
    """
    Physical verification documents uploaded for vehicle assurance.
    Stored in protected vault with UUID obfuscated file names.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assurance = models.ForeignKey(
        "assurances.VehicleAssurance",
        on_delete=models.CASCADE,
        related_name="documents"
    )
    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices
    )
    file_path = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assurance_document"
        ordering = ["uploaded_at"]
        verbose_name = "Assurance Document"
        verbose_name_plural = "Assurance Documents"

    def __str__(self):
        return f"{self.document_type} - {self.original_filename} ({self.assurance_id})"
