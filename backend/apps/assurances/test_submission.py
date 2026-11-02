from unittest.mock import patch

from django.db import DatabaseError, IntegrityError, transaction

from apps.assurances.models import VehicleAssurance
from apps.assurances.services.workflow_service import submit_assurance_application
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog


class SubmissionTests(AssuranceFeatureTestCase):
    def test_complete_new_motor_submits_with_audit_and_ip(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        response = self.post_action(assurance, "submit", REMOTE_ADDR="192.0.2.10")
        self.assertEqual(response.status_code, 200)
        self.assertIn("submitted_at", response.data["data"])
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "SUBMITTED")
        audit = AuditLog.objects.get(action="SUBMIT")
        self.assertEqual(audit.user, self.owner)
        self.assertEqual(audit.ip_address, "192.0.2.10")
        self.assertEqual(audit.changes["status"], {"old": "DRAFT", "new": "SUBMITTED"})

    def test_incomplete_new_motor_returns_422_without_status_change(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance, missing=["FOTO_MESIN"])
        response = self.post_action(assurance, "submit")
        self.assertEqual(response.status_code, 422)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error_code"], "INCOMPLETE_DOCUMENTS")
        self.assertEqual(response.data["missing_documents"], ["FOTO_MESIN"])
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "DRAFT")
        self.assertFalse(AuditLog.objects.filter(action="SUBMIT").exists())

    def test_old_motor_accepts_either_engine_or_frame(self):
        for document_type in ("FOTO_RANGKA", "FOTO_MESIN"):
            with self.subTest(document_type=document_type):
                assurance = self.draft(vehicle_category="MOTOR_LAMA")
                self.attach_uploaded_documents(assurance)
                assurance.documents.filter(document_type="FOTO_RANGKA").update(
                    document_type=document_type,
                )
                self.assertEqual(self.post_action(assurance, "submit").status_code, 200)

    def test_old_motor_missing_frame_and_engine_returns_422(self):
        assurance = self.draft(vehicle_category="MOTOR_LAMA")
        self.attach_uploaded_documents(assurance, missing=["FOTO_RANGKA"])
        response = self.post_action(assurance, "submit")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["missing_documents"], ["FOTO_RANGKA or FOTO_MESIN"])

    def test_invalid_required_form_data_cannot_submit(self):
        for field, value in (("tenor_years", 6), ("total_premium", "1.00"),
                             ("vehicle_category", "UNKNOWN"), ("sum_insured", 0)):
            with self.subTest(field=field):
                assurance = self.draft()
                self.attach_uploaded_documents(assurance)
                if field == "vehicle_category":
                    VehicleAssurance.objects.filter(pk=assurance.pk).update(**{field: value})
                    self.assertEqual(self.post_action(assurance, "submit").status_code, 400)
                else:
                    # DB constraints now reject corruption before submission (KA-Q11).
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        VehicleAssurance.objects.filter(pk=assurance.pk).update(**{field: value})

    def test_invalid_holder_nik_cannot_submit(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        assurance.policy_holder.nik = "invalid"
        assurance.policy_holder.save()
        self.assertEqual(self.post_action(assurance, "submit").status_code, 400)

    def test_peer_cannot_submit_other_creators_application(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        self.assertEqual(self.post_action(assurance, "submit", user=self.peer).status_code, 403)

    def test_agent_creator_and_admin_can_submit(self):
        for user in (self.agent, self.admin, self.superadmin):
            with self.subTest(role=user.role):
                assurance = self.draft()
                if user == self.agent:
                    VehicleAssurance.objects.filter(pk=assurance.pk).update(created_by=user)
                self.attach_uploaded_documents(assurance)
                self.assertEqual(self.post_action(assurance, "submit", user=user).status_code, 200)

    def test_cross_dealer_application_is_hidden(self):
        assurance = self.draft()
        VehicleAssurance.objects.filter(pk=assurance.pk).update(dealer=self.other_dealer)
        self.assertEqual(self.post_action(assurance, "submit").status_code, 404)

    def test_anonymous_submit_is_unauthorized(self):
        assurance = self.draft()
        response = self.client.post(f"/api/v1/assurances/{assurance.pk}/submit/")
        self.assertEqual(response.status_code, 401)

    def test_repeat_submit_does_not_change_status_or_duplicate_audit(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        response = self.post_action(assurance, "submit", user=self.admin)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(AuditLog.objects.filter(action="SUBMIT").count(), 1)

    def test_submit_audit_failure_rolls_back_status(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        with patch("apps.audit.services.audit_service.AuditLog.objects.create",
                   side_effect=DatabaseError("synthetic failure")):
            response = self.post_action(assurance, "submit")
        self.assertEqual(response.status_code, 503)
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "DRAFT")

    def test_submitted_data_and_documents_are_locked_for_admin(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        self.client.force_authenticate(self.admin)
        url = f"/api/v1/assurances/{assurance.pk}/"
        response = self.client.patch(url, {"sum_insured": "30000000.00"}, format="json")
        self.assertEqual(response.status_code, 400)
        document = assurance.documents.first()
        self.assertEqual(self.client.delete(f"{url}documents/{document.pk}/").status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 405)

    def test_stale_draft_instance_cannot_bypass_submitted_state(self):
        from apps.assurances.services.assurance_service import update_assurance_draft
        from rest_framework.exceptions import ValidationError

        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        submit_assurance_application(assurance, self.owner)
        with self.assertRaises(ValidationError):
            update_assurance_draft(assurance, self.admin, {"sum_insured": "30000000.00"})
