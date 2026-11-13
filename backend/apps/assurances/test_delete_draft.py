from unittest.mock import patch

from django.db import DatabaseError
from rest_framework.exceptions import ValidationError

from apps.assurances.models import AssuranceStatus, PolicyHolder, VehicleAssurance
from apps.assurances.services.assurance_service import create_assurance_draft, delete_assurance_draft
from apps.assurances.services.workflow_service import review_assurance, submit_assurance_application
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.dealers.models import AgentDealerAssignment
from apps.documents.models import AssuranceDocument


class DraftDeletionTests(AssuranceFeatureTestCase):
    def delete_draft(self, assurance, user):
        self.client.force_authenticate(user=user)
        return self.client.delete(f"/api/v1/assurances/{assurance.pk}/")

    def test_authorized_roles_can_delete_draft_and_cleanup_vault_and_orphan_holder(self):
        for role_user in (self.agent, self.admin, self.superadmin):
            assurance = self.draft()
            self.attach_uploaded_documents(assurance)
            doc_paths = [self.media / doc.file_path for doc in assurance.documents.all()]
            holder_id = assurance.policy_holder_id
            with self.captureOnCommitCallbacks(execute=True):
                response = self.delete_draft(assurance, role_user)
            self.assertEqual(response.status_code, 200, response.data)
            self.assertTrue(response.data["success"])
            self.assertFalse(VehicleAssurance.objects.filter(pk=assurance.pk).exists())
            self.assertFalse(AssuranceDocument.objects.filter(assurance_id=assurance.pk).exists())
            self.assertFalse(PolicyHolder.objects.filter(pk=holder_id).exists())
            for file_path in doc_paths:
                self.assertFalse(file_path.exists())
            audit = AuditLog.objects.filter(action="DELETE", entity_name="VEHICLE_ASSURANCE", entity_id=str(assurance.pk)).first()
            self.assertIsNotNone(audit)
            self.assertNotIn("nik", str(audit.changes).lower())

    def test_shared_policy_holder_survives_when_another_assurance_references_it(self):
        first = self.draft()
        second = VehicleAssurance.objects.create(
            policy_holder=first.policy_holder, dealer=first.dealer,
            vehicle_category=first.vehicle_category, coverage_type=first.coverage_type,
            sum_insured=first.sum_insured, tenor_years=first.tenor_years,
            base_premium=first.base_premium, admin_fee=first.admin_fee,
            total_premium=first.total_premium, period_start=first.period_start,
            period_end=first.period_end, issuance_year=first.issuance_year,
            status=AssuranceStatus.DRAFT, created_by=self.owner,
        )
        response = self.delete_draft(first, self.admin)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PolicyHolder.objects.filter(pk=second.policy_holder_id).exists())

    def test_dealer_cannot_delete_own_draft_but_can_delete_editable_document(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        document = assurance.documents.first()
        self.assertEqual(self.delete_draft(assurance, self.owner).status_code, 403)
        self.assertTrue(VehicleAssurance.objects.filter(pk=assurance.pk).exists())
        self.client.force_authenticate(user=self.owner)
        doc_res = self.client.delete(f"/api/v1/assurances/{assurance.pk}/documents/{document.pk}/")
        self.assertEqual(doc_res.status_code, 200)

    def test_agent_scope_and_revocation_enforced_for_read_create_and_delete(self):
        other_draft = create_assurance_draft(self.admin, self.payload(dealer=self.other_dealer))
        self.assertEqual(self.delete_draft(other_draft, self.agent).status_code, 404)
        assigned_draft = self.draft()
        AgentDealerAssignment.objects.filter(agent=self.agent, dealer=self.dealer).delete()
        self.assertEqual(self.delete_draft(assigned_draft, self.agent).status_code, 404)
        self.client.force_authenticate(user=self.agent)
        create_res = self.client.post("/api/v1/assurances/", {
            "policy_holder_name": "Revoked Agent", "policy_holder_nik": "0000000000000099",
            "dealer_id": str(self.dealer.pk), "vehicle_category": "MOTOR_BARU",
            "coverage_type": "TLO", "sum_insured": "20000000.00", "tenor_years": 1,
            "period_start": "2026-11-02", "issuance_year": 2026,
        }, format="json")
        self.assertEqual(create_res.status_code, 400)

    def test_non_draft_statuses_cannot_be_deleted_by_any_role(self):
        submitted = self.draft()
        self.attach_uploaded_documents(submitted)
        submit_assurance_application(submitted, self.owner)
        revision = self.draft()
        self.attach_uploaded_documents(revision)
        submit_assurance_application(revision, self.owner)
        review_assurance(revision, self.admin, {"decision": "REQUEST_REVISION", "review_notes": "Fix photo"})
        active = self.draft()
        self.attach_uploaded_documents(active)
        submit_assurance_application(active, self.owner)
        review_assurance(active, self.admin, {"decision": "APPROVE"})
        rejected = self.draft()
        self.attach_uploaded_documents(rejected)
        submit_assurance_application(rejected, self.owner)
        review_assurance(rejected, self.admin, {"decision": "REJECT_FINAL", "review_notes": "Final reject"})
        legacy = self.draft()
        VehicleAssurance.objects.filter(pk=legacy.pk).update(status=AssuranceStatus.APPROVED)
        for target in (submitted, revision, active, rejected, legacy):
            for role_user in (self.agent, self.admin, self.superadmin):
                self.assertEqual(self.delete_draft(target, role_user).status_code, 400)
                self.assertTrue(VehicleAssurance.objects.filter(pk=target.pk).exists())

    def test_audit_failure_and_stale_submit_race_preserve_draft_and_files(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        doc_paths = [self.media / doc.file_path for doc in assurance.documents.all()]
        with patch("apps.audit.services.audit_service.AuditLog.objects.create", side_effect=DatabaseError("audit down")):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.delete_draft(assurance, self.admin)
        self.assertEqual(response.status_code, 503)
        self.assertTrue(VehicleAssurance.objects.filter(pk=assurance.pk).exists())
        for file_path in doc_paths:
            self.assertTrue(file_path.exists())
        stale = VehicleAssurance.objects.get(pk=assurance.pk)
        submit_assurance_application(assurance, self.owner)
        with self.assertRaises(ValidationError):
            delete_assurance_draft(stale, self.admin)
        self.assertTrue(VehicleAssurance.objects.filter(pk=assurance.pk, status=AssuranceStatus.SUBMITTED).exists())

    def test_can_delete_draft_flag_in_list_and_detail(self):
        draft = self.draft()
        for role_user, expected in ((self.owner, False), (self.agent, True), (self.admin, True), (self.superadmin, True)):
            self.client.force_authenticate(user=role_user)
            list_res = self.client.get("/api/v1/assurances/")
            detail_res = self.client.get(f"/api/v1/assurances/{draft.pk}/")
            self.assertEqual(list_res.data["data"][0]["can_delete_draft"], expected)
            self.assertEqual(detail_res.data["data"]["can_delete_draft"], expected)
