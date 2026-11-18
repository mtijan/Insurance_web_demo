from unittest.mock import patch

from rest_framework.test import APIClient

from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.dealers.models import Dealer
from apps.notifications.models import Notification, NotificationEventType
from apps.users.models import CustomUser, UserRole


class NotificationWorkflowTests(AssuranceFeatureTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.outside_dealer_user = CustomUser.objects.create_user(
            username="notif_other_dealer", role=UserRole.DEALER, dealer=cls.other_dealer,
        )
        cls.outside_agent = CustomUser.objects.create_user(
            username="notif_other_agent", role=UserRole.AGENT,
        )
        cls.inactive_admin = CustomUser.objects.create_user(
            username="notif_inactive_admin", role=UserRole.ADMIN, is_active=False,
        )
        cls.must_change_user = CustomUser.objects.create_user(
            username="notif_pw_reset",
            role=UserRole.AGENT,
            password="TempPass!234",
            must_change_password=True,
        )

    def _recipients_for(self, assurance, event_type):
        return set(
            Notification.objects.filter(assurance=assurance, event_type=event_type).values_list("recipient_id", flat=True)
        )

    def test_submit_inspection_revision_and_approve_dispatch_scoped_notifications(self):
        assurance = self.draft(
            policy_holder_nik="3201123456789012",
            policy_holder_name="Rahasia Tertanggung",
            policy_holder_phone="081234567890",
        )
        self.attach_uploaded_documents(assurance)

        self.assertEqual(self.post_action(assurance, "submit", user=self.owner).status_code, 200)
        self.assertEqual(
            self._recipients_for(assurance, NotificationEventType.ASSURANCE_SUBMITTED),
            {self.agent.id, self.admin.id, self.superadmin.id},
        )
        self.assertEqual(
            self.post_action(
                assurance, "inspection",
                {"action": "NOTE", "section": "DOCUMENTS", "review_notes": "Perlu dicek"},
                user=self.agent,
            ).status_code,
            200,
        )
        note_recipients = self._recipients_for(assurance, NotificationEventType.ASSURANCE_NOTE)
        self.assertEqual(note_recipients, {self.owner.id, self.peer.id, self.admin.id, self.superadmin.id})

        self.assertEqual(
            self.post_action(
                assurance, "inspection",
                {"action": "REQUEST_REVISION", "section": "DATA", "review_notes": "Perbaiki alamat"},
                user=self.agent,
            ).status_code,
            200,
        )
        self.assertEqual(
            self._recipients_for(assurance, NotificationEventType.REVISION_REQUESTED),
            {self.owner.id, self.peer.id, self.admin.id, self.superadmin.id},
        )

    def test_approve_reject_final_and_notes_omit_pii(self):
        approved_app = self.draft(
            policy_holder_nik="3201123456789012",
            policy_holder_name="Rahasia Tertanggung",
            policy_holder_phone="081234567890",
        )
        self.attach_uploaded_documents(approved_app)
        self.assertEqual(self.post_action(approved_app, "submit", user=self.owner).status_code, 200)
        self.assertEqual(
            self.post_action(approved_app, "review", {"decision": "APPROVE", "review_notes": "Disetujui"}, user=self.admin).status_code,
            200,
        )
        self.assertEqual(
            self._recipients_for(approved_app, NotificationEventType.ASSURANCE_APPROVED),
            {self.owner.id, self.peer.id, self.agent.id, self.superadmin.id},
        )

        rejected_app = self.draft()
        self.attach_uploaded_documents(rejected_app)
        self.assertEqual(self.post_action(rejected_app, "submit", user=self.owner).status_code, 200)
        self.assertEqual(
            self.post_action(
                rejected_app, "review",
                {"decision": "REJECT_FINAL", "review_notes": "Tidak memenuhi syarat"},
                user=self.admin,
            ).status_code,
            200,
        )
        self.assertEqual(
            self._recipients_for(rejected_app, NotificationEventType.ASSURANCE_REJECTED),
            {self.owner.id, self.peer.id, self.agent.id, self.superadmin.id},
        )
        for msg in Notification.objects.values_list("message", flat=True):
            self.assertNotIn("3201123456789012", msg)
            self.assertNotIn("081234567890", msg)
            self.assertNotIn("Rahasia Tertanggung", msg)

    def test_transaction_rollback_creates_zero_notifications(self):
        assurance = self.draft()
        self.assertEqual(self.post_action(assurance, "submit", user=self.owner).status_code, 422)
        self.assertEqual(Notification.objects.filter(assurance=assurance).count(), 0)

        self.client.force_authenticate(user=self.owner)
        with patch("apps.assurances.services.note_service.dispatch_assurance_notifications", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.client.post(f"/api/v1/assurances/{assurance.pk}/notes/", {"message": "Rollback test"}, format="json")
        self.assertEqual(Notification.objects.filter(assurance=assurance).count(), 0)

    def test_must_change_password_blocks_notifications_and_notes(self):
        assurance = self.draft()
        restricted_client = APIClient()
        login_res = restricted_client.post(
            "/api/v1/auth/token/",
            {"username": self.must_change_user.username, "password": "TempPass!234"},
            format="json",
        )
        self.assertEqual(login_res.status_code, 200, login_res.data)
        access = login_res.data["data"]["access_token"]
        pw_res = restricted_client.get("/api/v1/notifications/", HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(pw_res.status_code, 403)
        note_res = restricted_client.post(
            f"/api/v1/assurances/{assurance.pk}/notes/",
            {"message": "Restricted"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(note_res.status_code, 403)

    def test_notification_endpoints_read_ownership_and_read_all(self):
        assurance = self.draft()
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(
            self.client.post(f"/api/v1/assurances/{assurance.pk}/notes/", {"message": "Halo admin"}, format="json").status_code,
            201,
        )
        admin_notif = Notification.objects.get(recipient=self.admin, assurance=assurance)

        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.post(f"/api/v1/notifications/{admin_notif.pk}/read/", {}, format="json").status_code, 404)

        self.client.force_authenticate(user=self.admin)
        list_res = self.client.get("/api/v1/notifications/?unread_only=true&limit=10")
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(list_res.data["data"]["unread_count"], 1)
        self.assertEqual(list_res.data["data"]["items"][0]["target_path"], f"/assurances/{assurance.pk}")

        read_res = self.client.post(f"/api/v1/notifications/{admin_notif.pk}/read/", {}, format="json")
        self.assertEqual(read_res.status_code, 200)
        self.assertEqual(read_res.data["data"]["unread_count"], 0)
        self.assertTrue(read_res.data["data"]["item"]["is_read"])

        self.client.force_authenticate(user=self.superadmin)
        all_res = self.client.post("/api/v1/notifications/read-all/", {}, format="json")
        self.assertEqual(all_res.status_code, 200)
        self.assertEqual(all_res.data["data"]["marked_count"], 1)
        self.assertEqual(all_res.data["data"]["unread_count"], 0)
        self.assertEqual(Notification.objects.filter(recipient=self.admin).count(), 1)

    def test_inactive_dealer_excludes_dealer_staff_notifications(self):
        assurance = self.draft()
        Dealer.objects.filter(pk=self.dealer.pk).update(is_active=False)
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(f"/api/v1/assurances/{assurance.pk}/notes/", {"message": "Catatan dealer nonaktif"}, format="json")
        self.assertEqual(res.status_code, 201)
        recipients = self._recipients_for(assurance, NotificationEventType.ASSURANCE_NOTE)
        self.assertNotIn(self.owner.id, recipients)
        self.assertNotIn(self.peer.id, recipients)
        self.assertIn(self.agent.id, recipients)
        self.assertIn(self.superadmin.id, recipients)
