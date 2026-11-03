"""DOC-OPEN-11 and user-approved DOC-OPEN-01 boundary/rollback evidence."""
from rest_framework.exceptions import ValidationError

from apps.assurances.models import PolicyHolder, VehicleAssurance
from apps.assurances.services.assurance_service import create_assurance_draft, update_assurance_draft
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog


class DraftInputBoundaryTests(AssuranceFeatureTestCase):
    def api_payload(self, **overrides):
        payload = self.payload(**overrides)
        payload["dealer_id"] = str(payload.pop("dealer").pk)
        payload["period_start"] = str(payload["period_start"])
        return payload

    def counts(self):
        return (PolicyHolder.objects.count(), VehicleAssurance.objects.count(), AuditLog.objects.count())

    def test_post_vehicle_object_below_at_above_limit(self):
        self.client.force_authenticate(self.owner)
        for length, status in ((49, 201), (50, 201), (51, 400)):
            before = self.counts()
            response = self.client.post("/api/v1/assurances/", self.api_payload(vehicle_object="A" * length), format="json")
            self.assertEqual(response.status_code, status)
            if status == 400:
                self.assertEqual(response.data["error_code"], "VALIDATION_ERROR")
                self.assertIn("vehicle_object", response.data["errors"])
                self.assertEqual(self.counts(), before)

    def test_patch_limits_and_no_partial_holder_or_audit(self):
        assurance = self.draft()
        self.client.force_authenticate(self.owner)
        for length, status in ((49, 200), (50, 200), (51, 400)):
            before = self.counts()
            response = self.client.patch(f"/api/v1/assurances/{assurance.pk}/", {
                "vehicle_object": "A" * length, "policy_holder_name": "New Holder",
            }, format="json")
            self.assertEqual(response.status_code, status)
            if status == 400:
                self.assertEqual(self.counts(), before)
                assurance.refresh_from_db()
                self.assertEqual(len(assurance.vehicle_object), 50)

    def test_direct_service_limits_and_trim(self):
        for length in (49, 50):
            assurance = self.draft(vehicle_object="A" * length)
            update_assurance_draft(assurance, self.owner, {"vehicle_object": " B "})
            assurance.refresh_from_db()
            self.assertEqual(assurance.vehicle_object, "B")
        for invalid in ("A" * 51, "   ", None):
            before = self.counts()
            with self.assertRaises(ValidationError):
                create_assurance_draft(self.owner, self.payload(vehicle_object=invalid))
            with self.assertRaises(ValidationError):
                update_assurance_draft(assurance, self.owner, {"vehicle_object": invalid, "policy_holder_name": "Other Name"})
            self.assertEqual(self.counts(), before)

    def test_approved_name_characters_and_boundaries(self):
        for name in ("Ana", "A" * 100, "Élodie O’Neil-Santoso.", "李 小明", "José D'Angelo"):
            self.assertEqual(self.draft(policy_holder_name=name).policy_holder.full_name, name)
        for name in ("Ab", "A" * 101, "123", "Name_One", "Name\nOne", "!!!"):
            with self.subTest(name=name):
                before = self.counts()
                with self.assertRaises(ValidationError):
                    self.draft(policy_holder_name=name)
                self.assertEqual(self.counts(), before)

    def test_legacy_name_preserved_until_explicit_edit(self):
        assurance = self.draft()
        PolicyHolder.objects.filter(pk=assurance.policy_holder_id).update(full_name="A1")
        update_assurance_draft(assurance, self.owner, {"vehicle_object": "Motor"})
        assurance.refresh_from_db()
        self.assertEqual(assurance.policy_holder.full_name, "A1")
        with self.assertRaises(ValidationError):
            update_assurance_draft(assurance, self.owner, {"policy_holder_name": "A1"})

    def test_api_name_rejection_preserves_business_and_audit(self):
        assurance = self.draft()
        self.client.force_authenticate(self.owner)
        for name in ("Ab", "A" * 101, "Test_One", "123"):
            before = self.counts()
            response = self.client.post("/api/v1/assurances/", self.api_payload(policy_holder_name=name), format="json")
            self.assertEqual(response.status_code, 400)
            response = self.client.patch(f"/api/v1/assurances/{assurance.pk}/", {"policy_holder_name": name}, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(self.counts(), before)
