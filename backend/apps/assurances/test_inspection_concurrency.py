"""Observe a real PostgreSQL lock between Agent correction and final decision."""
from threading import Event
from unittest import skipUnless

from django.db import connection, connections
from django.test import TransactionTestCase
from rest_framework.exceptions import APIException

from apps.assurances.models import VehicleAssurance
from apps.assurances.services.inspection_service import inspect_assurance
from apps.assurances.services.workflow_service import review_assurance
from apps.assurances import test_postgres_concurrency as support
from apps.users.models import CustomUser


@skipUnless(connection.vendor == "postgresql", "PostgreSQL row locking requires PostgreSQL")
class PostgreSQLInspectionConcurrencyTests(TransactionTestCase):
    payload = support.PostgreSQLApprovalConcurrencyTests.payload
    draft = support.PostgreSQLApprovalConcurrencyTests.draft
    attach_uploaded_documents = support.PostgreSQLApprovalConcurrencyTests.attach_uploaded_documents
    setUp = support.PostgreSQLApprovalConcurrencyTests.setUp
    submitted = support.PostgreSQLApprovalConcurrencyTests.submitted
    parallel = support.PostgreSQLApprovalConcurrencyTests.parallel
    held_row_hook = support.PostgreSQLApprovalConcurrencyTests.held_row_hook
    wait_for_lock = support.PostgreSQLApprovalConcurrencyTests.wait_for_lock

    def worker(self, item, barrier, hook):
        identity, action = item
        database = connections["default"]
        database.close()
        try:
            with database.cursor() as cursor:
                cursor.execute("SET lock_timeout = '8s'")
                cursor.execute("SET statement_timeout = '12s'")
                cursor.execute("SELECT pg_backend_pid()")
                pid = cursor.fetchone()[0]
            actor = self.agent if action == "REQUEST_REVISION" else self.admin
            user = CustomUser.objects.get(pk=actor.pk)
            assurance = VehicleAssurance.objects.get(pk=identity)
            barrier.wait(timeout=8)
            with database.execute_wrapper(hook):
                try:
                    result = self.mutate(assurance, user, action)
                    return (pid, 200, result.status)
                except APIException as exc:
                    return (pid, exc.status_code, None)
        finally:
            database.close()

    def mutate(self, assurance, user, action):
        if action == "REQUEST_REVISION":
            return inspect_assurance(assurance, user, {
                "action": action, "section": "DOCUMENTS", "review_notes": "Replace synthetic photo",
            })
        return review_assurance(assurance, user, {"decision": action, "review_notes": "Synthetic decision"})

    def assert_race(self, final):
        assurance = self.submitted()
        release = Event()
        results = self.parallel([(assurance.pk, "REQUEST_REVISION"), (assurance.pk, final)],
                                self.held_row_hook(release, "vehicle_assurance"),
                                lambda: self.wait_for_lock(release))
        self.assertEqual(sorted(row[1] for row in results), [200, 400])
        assurance.refresh_from_db()
        self.assertIn(assurance.status, ("REVISION", "ACTIVE" if final == "APPROVE" else "REJECTED"))
        self.assertEqual(assurance.review_history.count(), 2)
        self.assertEqual(bool(assurance.assurance_number), assurance.status == "ACTIVE")

    def test_agent_revision_racing_admin_approval_commits_only_one(self):
        self.assert_race("APPROVE")

    def test_agent_revision_racing_final_rejection_commits_only_one(self):
        self.assert_race("REJECT_FINAL")
