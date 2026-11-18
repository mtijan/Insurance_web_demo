from django.urls import reverse

from apps.assurances.models import AssuranceNote, AssuranceStatus
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.dealers.models import Dealer
from apps.users.models import CustomUser, UserRole


class AssuranceNotesTests(AssuranceFeatureTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.outside_dealer_user = CustomUser.objects.create_user(
            username="notes_other_dealer", role=UserRole.DEALER, dealer=cls.other_dealer,
        )
        cls.outside_agent = CustomUser.objects.create_user(
            username="notes_other_agent", role=UserRole.AGENT,
        )

    def _notes_url(self, assurance):
        return f"/api/v1/assurances/{assurance.pk}/notes/"

    def test_shared_two_way_notes_for_scoped_participants_and_super_admin(self):
        assurance = self.draft()
        for actor, text in (
            (self.owner, "Mohon cek ulang foto STNK."),
            (self.agent, "Sudah dibantu teruskan ke underwriting."),
            (self.admin, "Data sesuai, silakan lanjut unggah."),
            (self.superadmin, "Dipantau Super Admin, silakan lanjut."),
        ):
            self.client.force_authenticate(user=actor)
            res = self.client.post(self._notes_url(assurance), {"message": text}, format="json")
            self.assertEqual(res.status_code, 201, res.data)
            self.assertTrue(res.data["success"])
            self.assertEqual(res.data["data"]["author_role"], actor.role)

        for reader in (self.peer, self.agent, self.admin, self.superadmin):
            self.client.force_authenticate(user=reader)
            res = self.client.get(self._notes_url(assurance))
            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(res.data["data"]), 4)
            self.assertEqual(res.data["data"][0]["author_username"], self.owner.username)
        self.assertTrue(AuditLog.objects.filter(action="NOTE_CREATE", entity_name="ASSURANCE_NOTE").exists())

    def test_notes_enforce_tenant_isolation_validation_and_inactive_dealer_guard(self):
        assurance = self.draft()
        for outsider in (self.outside_dealer_user, self.outside_agent):
            self.client.force_authenticate(user=outsider)
            self.assertEqual(self.client.get(self._notes_url(assurance)).status_code, 404)
            self.assertEqual(
                self.client.post(self._notes_url(assurance), {"message": "Bypass"}, format="json").status_code,
                404,
            )

        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.post(self._notes_url(assurance), {"message": "   "}, format="json").status_code, 400)
        self.assertEqual(
            self.client.post(self._notes_url(assurance), {"message": "x" * 1001}, format="json").status_code,
            400,
        )

        Dealer.objects.filter(pk=self.dealer.pk).update(is_active=False)
        for blocked in (self.owner, self.agent):
            self.client.force_authenticate(user=blocked)
            self.assertEqual(
                self.client.post(self._notes_url(assurance), {"message": "Dealer off"}, format="json").status_code,
                403,
            )
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(self._notes_url(assurance), {"message": "Catatan internal saat dealer off"}, format="json")
        self.assertEqual(res.status_code, 201)

    def test_notes_allowed_across_active_and_rejected_statuses(self):
        for target_status in (AssuranceStatus.SUBMITTED, AssuranceStatus.REVISION, AssuranceStatus.ACTIVE, AssuranceStatus.REJECTED):
            assurance = self.draft()
            assurance.status = target_status
            assurance.save(update_fields=["status"])
            self.client.force_authenticate(user=self.owner)
            res = self.client.post(self._notes_url(assurance), {"message": f"Diskusi {target_status}"}, format="json")
            self.assertEqual(res.status_code, 201)
            self.assertEqual(AssuranceNote.objects.filter(assurance=assurance).count(), 1)
