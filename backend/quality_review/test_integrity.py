from apps.assurances.models import VehicleAssurance
from apps.assurances.services.workflow_service import review_assurance, submit_assurance_application
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.users.models import CustomUser


class IntegrityReviewTests(AssuranceFeatureTestCase):
    def active_assurance(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        return review_assurance(assurance, self.admin, {"decision": "APPROVE"})

    def api_payload(self, **overrides):
        data = self.payload(**overrides)
        data["dealer_id"] = str(data.pop("dealer").pk)
        data["period_start"] = data["period_start"].isoformat()
        return data

    def test_other_dealer_cannot_change_holder_on_existing_active_policy(self):
        active = self.active_assurance()
        original_name = active.policy_holder.full_name
        other_user = CustomUser.objects.create_user(
            username="review_other_dealer", role="DEALER", dealer=self.other_dealer,
        )
        self.client.force_authenticate(other_user)
        response = self.client.post("/api/v1/assurances/", self.api_payload(
            dealer=self.other_dealer, policy_holder_name="Unauthorized replacement",
        ), format="json")
        self.assertIn(response.status_code, (201, 400, 403, 409))
        active.refresh_from_db()
        self.assertEqual(active.policy_holder.full_name, original_name)

    def test_editing_shared_holder_draft_does_not_change_active_policy(self):
        draft = self.draft()
        active = self.active_assurance()
        original_name = active.policy_holder.full_name
        self.client.force_authenticate(self.owner)
        response = self.client.patch(f"/api/v1/assurances/{draft.pk}/", {
            "policy_holder_name": "Replaced via another draft",
        }, format="json")
        self.assertIn(response.status_code, (200, 400, 403, 409))
        active.refresh_from_db()
        self.assertEqual(active.policy_holder.full_name, original_name)

    def test_deleting_dealer_does_not_erase_active_policy(self):
        active = self.active_assurance()
        self.client.force_authenticate(self.superadmin)
        self.client.delete(f"/api/v1/dealers/{self.dealer.pk}/")
        self.assertTrue(VehicleAssurance.objects.filter(pk=active.pk).exists())

    def test_deleting_creator_does_not_erase_active_policy(self):
        active = self.active_assurance()
        self.client.force_authenticate(self.superadmin)
        self.client.delete(f"/api/v1/auth/manage/{self.owner.pk}/")
        self.assertTrue(VehicleAssurance.objects.filter(pk=active.pk).exists())

    def test_submit_rejects_metadata_without_physical_files(self):
        assurance = self.draft()
        self.attach_documents(assurance)
        response = self.post_action(assurance, "submit")
        self.assertIn(response.status_code, (400, 422, 503))

    def test_late_period_with_tenor_returns_validation_error(self):
        self.client.force_authenticate(self.owner)
        self.client.raise_request_exception = False
        data = self.api_payload(tenor_years=5)
        data["period_start"] = "9999-01-01"
        response = self.client.post("/api/v1/assurances/", data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_dealer_creation_records_critical_audit_event(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.post("/api/v1/dealers/", {
            "code": "REVIEW-NEW", "name": "Synthetic review dealer",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(AuditLog.objects.filter(
            entity_name="DEALER", entity_id=response.data["data"]["id"], action="CREATE",
        ).exists())

    def test_database_rejects_invalid_assurance_financial_state(self):
        from django.db import IntegrityError, transaction

        assurance = self.draft()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VehicleAssurance.objects.filter(pk=assurance.pk).update(
                    sum_insured=-1, tenor_years=9,
                )
