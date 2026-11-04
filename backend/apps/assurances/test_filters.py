from datetime import datetime
from io import BytesIO
from uuid import uuid4
from openpyxl import load_workbook

from apps.assurances.models import VehicleAssurance
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.assurances.services.assurance_service import create_assurance_draft


class AssuranceFilterTests(AssuranceFeatureTestCase):
    def setUp(self):
        self.a = self.draft()
        self.b = create_assurance_draft(self.admin, self.payload(dealer=self.other_dealer))
        self.c = self.draft()
        for obj, timestamp in [(self.a, "2026-11-02T17:00:00+00:00"),
                               (self.b, "2026-11-03T16:59:59+00:00"),
                               (self.c, "2026-11-03T17:00:00+00:00")]:
            VehicleAssurance.objects.filter(pk=obj.pk).update(created_at=datetime.fromisoformat(timestamp))
        self.client.force_authenticate(self.superadmin)

    def listing(self, **params):
        return self.client.get('/api/v1/assurances/', params)

    def test_wib_date_boundaries_and_combination(self):
        response = self.listing(date_from='2026-11-03', date_to='2026-11-03')
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row['id'] for row in response.data['data']}, {str(self.a.pk), str(self.b.pk)})
        response = self.listing(date_from='2026-11-03', date_to='2026-11-03', dealer_id=self.dealer.pk, status='DRAFT')
        self.assertEqual([row['id'] for row in response.data['data']], [str(self.a.pk)])

    def test_dealer_and_agent_scope_cannot_be_widened(self):
        for user in [self.owner, self.agent]:
            self.client.force_authenticate(user)
            self.assertEqual(self.listing(dealer_id=self.other_dealer.pk).data['data'], [])
            self.assertEqual(len(self.listing().data['data']), 2)
            self.assertEqual(self.client.get('/api/v1/assurances/export-excel/').status_code, 403)

    def test_invalid_and_unknown_filters(self):
        for params in [{'dealer_id': 'bad'}, {'date_from': '2026-02-30'}, {'date_to': '9999-12-31'},
                       {'date_from': '2026-11-04', 'date_to': '2026-11-03'}, {'status': 'invented'},
                       {'date_from': '20261103'}]:
            with self.subTest(params=params):
                self.assertEqual(self.listing(**params).status_code, 400)
                self.assertEqual(self.client.get('/api/v1/assurances/export-excel/', params).status_code, 400)
        self.assertEqual(self.listing(dealer_id=uuid4()).data['data'], [])

    def test_export_uses_same_filter_and_keeps_twelve_columns(self):
        response = self.client.get('/api/v1/assurances/export-excel/',
                                   {'dealer_id': self.dealer.pk, 'date_to': '2026-11-03'})
        self.assertEqual(response.status_code, 200)
        rows = list(load_workbook(BytesIO(response.content)).active.values)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0]), 12)
        self.assertEqual(rows[1][3], '0000000000000001')

    def test_scope_changes_apply_to_next_request(self):
        self.client.force_authenticate(self.agent)
        self.assertEqual(len(self.listing(dealer_id=self.dealer.pk).data['data']), 2)
        self.agent.dealer_assignments.all().delete()
        self.assertEqual(self.listing(dealer_id=self.dealer.pk).data['data'], [])
