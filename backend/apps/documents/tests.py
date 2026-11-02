import datetime
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from apps.assurances.models import (
    PolicyHolder,
    VehicleAssurance,
    VehicleCategory,
    CoverageType,
)
from apps.dealers.models import Dealer
from apps.documents.models import DocumentType, AssuranceDocument
from apps.documents.services.document_validator import (
    validate_document_completeness,
    get_required_document_types,
)
from apps.documents.services.vault_service import verify_image_magic_bytes
from apps.documents.test_images import jpeg_bytes
from apps.users.models import CustomUser, UserRole


class DocumentValidatorUnitTests(APITestCase):
    def test_motor_baru_rules(self):
        """Motor Baru requires 4 docs: KTP, Surat Jalan, No Rangka, No Mesin."""
        complete_set = {
            DocumentType.KTP.value,
            DocumentType.SURAT_JALAN.value,
            DocumentType.FOTO_RANGKA.value,
            DocumentType.FOTO_MESIN.value,
        }
        is_complete, missing = validate_document_completeness("MOTOR_BARU", complete_set)
        self.assertTrue(is_complete)
        self.assertEqual(len(missing), 0)

        # Missing FOTO_MESIN
        partial_set = {DocumentType.KTP.value, DocumentType.SURAT_JALAN.value, DocumentType.FOTO_RANGKA.value}
        is_complete2, missing2 = validate_document_completeness("MOTOR_BARU", partial_set)
        self.assertFalse(is_complete2)
        self.assertIn("FOTO_MESIN", missing2)

    def test_motor_lama_conditional_rules(self):
        """Motor Lama requires KTP, STNK, 4 sides, and at least ONE of (Rangka, Mesin)."""
        base_set = {
            DocumentType.KTP.value,
            DocumentType.STNK.value,
            DocumentType.FOTO_DEPAN.value,
            DocumentType.FOTO_BELAKANG.value,
            DocumentType.FOTO_KANAN.value,
            DocumentType.FOTO_KIRI.value,
        }

        # 1. With Rangka only -> valid
        with_rangka = base_set | {DocumentType.FOTO_RANGKA.value}
        is_valid, _ = validate_document_completeness("MOTOR_LAMA", with_rangka)
        self.assertTrue(is_valid)

        # 2. With Mesin only -> valid
        with_mesin = base_set | {DocumentType.FOTO_MESIN.value}
        is_valid2, _ = validate_document_completeness("MOTOR_LAMA", with_mesin)
        self.assertTrue(is_valid2)

        # 3. Neither Rangka nor Mesin -> invalid
        is_valid3, missing3 = validate_document_completeness("MOTOR_LAMA", base_set)
        self.assertFalse(is_valid3)
        self.assertTrue(any("FOTO_RANGKA" in m for m in missing3))


class MagicBytesUnitTests(APITestCase):
    def test_valid_image_headers(self):
        """JPEG, PNG, and WebP valid binary headers must be detected correctly."""
        jpeg_file = SimpleUploadedFile("test.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 32)
        self.assertEqual(verify_image_magic_bytes(jpeg_file), "image/jpeg")

        png_file = SimpleUploadedFile("test.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
        self.assertEqual(verify_image_magic_bytes(png_file), "image/png")

        webp_header = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 20
        webp_file = SimpleUploadedFile("test.webp", webp_header)
        self.assertEqual(verify_image_magic_bytes(webp_file), "image/webp")

    def test_invalid_header_raises_validation_error(self):
        """Executable or text binary must be rejected."""
        fake_file = SimpleUploadedFile("malicious.jpg", b"MZ\x90\x00\x03\x00\x00\x00")
        with self.assertRaises(ValidationError):
            verify_image_magic_bytes(fake_file)


class DocumentUploadAPITests(APITestCase):
    def setUp(self):
        self.dealer = Dealer.objects.create(code="DLR-01", name="Dealer Honda")
        self.dealer_user = CustomUser.objects.create_user(
            username="staff_dealer",
            email="staff@test.com",
            password="Password123!",
            role=UserRole.DEALER,
            dealer=self.dealer
        )
        self.holder = PolicyHolder.objects.create(nik="3201111111111111", full_name="Nasabah Test")
        today = datetime.date.today()
        self.assurance = VehicleAssurance.objects.create(
            policy_holder=self.holder,
            dealer=self.dealer,
            vehicle_category=VehicleCategory.MOTOR_BARU,
            coverage_type=CoverageType.TLO,
            sum_insured=Decimal("20000000.00"),
            tenor_years=1,
            base_premium=Decimal("400000.00"),
            admin_fee=Decimal("35000.00"),
            total_premium=Decimal("435000.00"),
            period_start=today,
            period_end=today.replace(year=today.year + 1),
            issuance_year=2026,
            created_by=self.dealer_user
        )

    def test_upload_and_stream_and_delete_document(self):
        """Verifies full lifecycle: multipart upload, authenticated streaming, and deletion."""
        self.client.force_authenticate(user=self.dealer_user)

        # 1. Upload valid JPEG
        upload_url = reverse("assurance-upload-document", kwargs={"pk": self.assurance.id})
        image_content = jpeg_bytes()
        uploaded_file = SimpleUploadedFile("ktp.jpg", image_content, content_type="image/jpeg")

        payload = {
            "document_type": DocumentType.KTP.value,
            "file": uploaded_file
        }
        res_upload = self.client.post(upload_url, payload, format="multipart")
        self.assertEqual(res_upload.status_code, status.HTTP_201_CREATED)
        doc_id = res_upload.data["data"]["document_id"]
        self.assertEqual(res_upload.data["data"]["document_type"], "KTP")

        # 2. Authenticated View Stream
        view_url = reverse("assurance-view-document-stream", kwargs={"pk": self.assurance.id, "doc_id": doc_id})
        res_view = self.client.get(view_url)
        self.assertEqual(res_view.status_code, status.HTTP_200_OK)
        self.assertEqual(res_view.headers["Content-Type"], "image/jpeg")

        # 3. Unauthenticated access blocked
        anon_client = self.client_class()
        res_anon = anon_client.get(view_url)
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        # 4. Delete Document
        del_url = reverse("assurance-delete-document", kwargs={"pk": self.assurance.id, "doc_id": doc_id})
        res_del = self.client.delete(del_url)
        self.assertEqual(res_del.status_code, status.HTTP_200_OK)
        self.assertFalse(AssuranceDocument.objects.filter(id=doc_id).exists())
