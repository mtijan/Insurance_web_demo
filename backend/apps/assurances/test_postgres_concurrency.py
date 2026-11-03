"""Real PostgreSQL overlap, independent connections and bounded lock waits."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, Lock
from time import monotonic, sleep
from unittest import skipUnless
from unittest.mock import patch

from django.db import DatabaseError, connection, connections
from django.test import TransactionTestCase
from rest_framework.exceptions import APIException

from apps.assurances.models import AssuranceNumberSequence, VehicleAssurance
from apps.assurances.services.workflow_service import review_assurance, submit_assurance_application
from apps.assurances.test_support import AssuranceFeatureTestCase
from apps.audit.models import AuditLog
from apps.users.models import CustomUser


@skipUnless(connection.vendor == "postgresql", "PostgreSQL row locking requires PostgreSQL")
class PostgreSQLApprovalConcurrencyTests(TransactionTestCase):
    payload = AssuranceFeatureTestCase.payload
    draft = AssuranceFeatureTestCase.draft
    attach_uploaded_documents = AssuranceFeatureTestCase.attach_uploaded_documents

    def setUp(self):
        AssuranceFeatureTestCase.setUpTestData.__func__(type(self))

    def submitted(self):
        assurance = self.draft()
        self.attach_uploaded_documents(assurance)
        return submit_assurance_application(assurance, self.owner)

    def worker(self, identifier, barrier, hook):
        database = connections["default"]
        database.close()
        try:
            with database.cursor() as cursor:
                cursor.execute("SET lock_timeout = '8s'")
                cursor.execute("SET statement_timeout = '12s'")
                cursor.execute("SELECT pg_backend_pid()")
                pid = cursor.fetchone()[0]
            user = CustomUser.objects.get(pk=self.admin.pk)
            assurance = VehicleAssurance.objects.get(pk=identifier)
            barrier.wait(timeout=8)
            with database.execute_wrapper(hook):
                try:
                    result = review_assurance(assurance, user, {"decision": "APPROVE"})
                    return (pid, 200, result.assurance_number)
                except APIException as exc:
                    return (pid, exc.status_code, None)
        finally:
            database.close()

    def parallel(self, identifiers, hook=None, observer=None):
        barrier = Barrier(2)
        hook = hook or (lambda execute, sql, params, many, context: execute(sql, params, many, context))
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self.worker, pk, barrier, hook) for pk in identifiers]
            if observer:
                observer()
            results = [future.result(timeout=20) for future in futures]
        self.assertEqual(len({row[0] for row in results}), 2)
        print("PG independent connection outcomes:", results)
        return results

    def wait_for_lock(self, release):
        deadline = monotonic() + 7
        blocked = False
        try:
            while monotonic() < deadline:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() "
                                   "AND pid<>pg_backend_pid() AND cardinality(pg_blocking_pids(pid))>0")
                    blocked = cursor.fetchone()[0] > 0
                if blocked:
                    break
                sleep(0.02)
            self.assertTrue(blocked, "Second independent PostgreSQL connection must be observed waiting on a lock")
        finally:
            release.set()

    def held_row_hook(self, release, table):
        guard, held = Lock(), Event()

        def hook(execute, sql, params, many, context):
            value = execute(sql, params, many, context)
            if f'FROM "{table}"' in sql and "FOR UPDATE" in sql:
                with guard:
                    first = not held.is_set()
                    held.set()
                if first and not release.wait(timeout=9):
                    raise TimeoutError("Lock observation timed out")
            return value

        return hook

    def test_same_assurance_overlaps_and_only_one_approval_commits(self):
        assurance = self.submitted()
        release = Event()
        results = self.parallel([assurance.pk, assurance.pk], self.held_row_hook(release, "vehicle_assurance"),
                                lambda: self.wait_for_lock(release))
        self.assertEqual(sorted(row[1] for row in results), [200, 400])
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "ACTIVE")
        self.assertEqual(assurance.assurance_number, "KAS-2026-00001")
        self.assertEqual(AssuranceNumberSequence.objects.get(year=2026).last_value, 1)
        self.assertEqual(AuditLog.objects.filter(action="APPROVE", entity_id=str(assurance.pk)).count(), 1)

    def first_counter_hook(self):
        barrier = Barrier(2)
        seen, guard = set(), Lock()

        def hook(execute, sql, params, many, context):
            value = execute(sql, params, many, context)
            if 'FROM "assurance_number_sequence"' in sql and "FOR UPDATE" in sql:
                identity = id(context["connection"])
                with guard:
                    first = identity not in seen
                    seen.add(identity)
                if first:
                    barrier.wait(timeout=8)
            return value

        return hook

    def assert_distinct_commits(self, results, start):
        self.assertEqual([row[1] for row in results], [200, 200])
        self.assertEqual({row[2] for row in results}, {f"KAS-2026-{start+1:05d}", f"KAS-2026-{start+2:05d}"})
        self.assertEqual(VehicleAssurance.objects.filter(status="ACTIVE").count(), 2)
        self.assertEqual(AuditLog.objects.filter(action="APPROVE").count(), 2)
        self.assertEqual(AssuranceNumberSequence.objects.get(year=2026).last_value, start + 2)

    def test_different_assurances_race_to_initialize_first_counter(self):
        assurances = [self.submitted(), self.submitted()]
        self.assertFalse(AssuranceNumberSequence.objects.exists())
        results = self.parallel([item.pk for item in assurances], self.first_counter_hook())
        self.assert_distinct_commits(results, 0)

    def test_different_assurances_serialize_existing_annual_counter(self):
        assurances = [self.submitted(), self.submitted()]
        AssuranceNumberSequence.objects.create(year=2026, last_value=41)
        release = Event()
        results = self.parallel([item.pk for item in assurances],
                                self.held_row_hook(release, "assurance_number_sequence"),
                                lambda: self.wait_for_lock(release))
        self.assert_distinct_commits(results, 41)

    def test_concurrent_audit_failure_rolls_back_then_other_approval_commits(self):
        assurance = self.submitted()
        original = AuditLog.objects.create
        guard, attempted = Lock(), Event()

        def fail_first(**kwargs):
            with guard:
                fail = kwargs.get("action") == "APPROVE" and not attempted.is_set()
                if fail:
                    attempted.set()
            if fail:
                raise DatabaseError("synthetic concurrent audit failure")
            return original(**kwargs)

        with patch("apps.audit.services.audit_service.AuditLog.objects.create", side_effect=fail_first):
            results = self.parallel([assurance.pk, assurance.pk])
        self.assertEqual(sorted(row[1] for row in results), [200, 503])
        assurance.refresh_from_db()
        self.assertEqual(assurance.status, "ACTIVE")
        self.assertEqual(assurance.assurance_number, "KAS-2026-00001")
        self.assertEqual(AssuranceNumberSequence.objects.get(year=2026).last_value, 1)
        self.assertEqual(AuditLog.objects.filter(action="APPROVE").count(), 1)
