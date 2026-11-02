from datetime import date
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase, APIClient

from apps.assurances.services.assurance_service import create_assurance_draft
from apps.dealers.models import AgentDealerAssignment, Dealer
from apps.documents.models import AssuranceDocument
from apps.documents.services.document_validator import get_required_document_types
from apps.users.models import CustomUser, UserRole


class AssuranceFeatureTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dealer = Dealer.objects.create(code="FEATURE-A", name="Feature Dealer")
        cls.other_dealer = Dealer.objects.create(code="FEATURE-B", name="Other Dealer")
        cls.users = {}
        for role in UserRole.values:
            cls.users[role] = CustomUser.objects.create_user(
                username=f"feature_{role}", email=f"{role}@example.test", role=role,
                dealer=cls.dealer if role == UserRole.DEALER else None,
            )
        cls.owner = cls.users[UserRole.DEALER]
        cls.admin = cls.users[UserRole.ADMIN]
        cls.superadmin = cls.users[UserRole.SUPER_ADMIN]
        cls.agent = cls.users[UserRole.AGENT]
        AgentDealerAssignment.objects.create(agent=cls.agent, dealer=cls.dealer)
        cls.peer = CustomUser.objects.create_user(
            username="feature_peer", role=UserRole.DEALER, dealer=cls.dealer,
        )

    def payload(self, **overrides):
        data = {
            "policy_holder_nik": "0000000000000001", "policy_holder_name": "Test Holder",
            "dealer": self.dealer, "vehicle_category": "MOTOR_BARU",
            "coverage_type": "TLO", "sum_insured": "20000000.00", "tenor_years": 1,
            "period_start": date(2026, 11, 2), "issuance_year": 2026,
        }
        data.update(overrides)
        return data

    def draft(self, **overrides):
        return create_assurance_draft(self.owner, self.payload(**overrides))

    def attach_documents(self, assurance, missing=()):
        types = get_required_document_types(assurance.vehicle_category)
        types = [item.replace("FOTO_RANGKA OR FOTO_MESIN", "FOTO_RANGKA") for item in types]
        for document_type in types:
            if document_type not in missing:
                AssuranceDocument.objects.create(
                    assurance=assurance, document_type=document_type,
                    file_path="synthetic-test-only.jpg", original_filename="synthetic.jpg",
                    file_size=3, mime_type="image/jpeg",
                )

    def post_action(self, assurance, action, data=None, user=None, **extra):
        self.client.force_authenticate(user=user or self.owner)
        return self.client.post(
            f"/api/v1/assurances/{assurance.pk}/{action}/", data or {},
            format="json", **extra,
        )

    def attach_uploaded_documents(self, assurance, missing=()):
        if not hasattr(self, "media"):
            directory = self.enterContext(TemporaryDirectory())
            self.media = Path(directory)
            self.enterContext(override_settings(MEDIA_ROOT=directory))
        client = APIClient()
        client.force_authenticate(self.superadmin)
        types = get_required_document_types(assurance.vehicle_category)
        for item in types:
            document_type = item.replace("FOTO_RANGKA OR FOTO_MESIN", "FOTO_RANGKA")
            if document_type in missing:
                continue
            content = BytesIO()
            Image.new("RGB", (2, 2), "white").save(content, format="PNG")
            response = client.post(f"/api/v1/assurances/{assurance.pk}/documents/", {
                "document_type": document_type,
                "file": SimpleUploadedFile("synthetic.png", content.getvalue(), content_type="image/png"),
            }, format="multipart")
            self.assertEqual(response.status_code, 201, response.data)
