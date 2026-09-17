from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest

from services.ai_trial_budget import AITrialBudget, TrialDenied, ACCOUNT_OPERATIONS_PER_DAY


class AITrialBudgetTests(unittest.TestCase):
    def setUp(self):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        self.path = Path(root.name) / 'spending.db'
        self.now = 1789516800  # UTC September 16, 2026.
        self.ledger = AITrialBudget(self.path, enabled=True, clock=lambda: self.now)
        self.ledger.initialize()
        for identity in ('a', 'b', 'c'):
            self.ledger.authorize_identity(identity)

    def reserve(self, identity='a', request='first', cost=600000):
        return self.ledger.reserve(identity, request, 'a' * 64, cost)

    def test_default_disabled_unknown_account_and_missing_storage_fail_closed(self):
        with self.assertRaises(TrialDenied):
            AITrialBudget(self.path).reserve('a', 'first', 'a' * 64, 1)
        with self.assertRaises(TrialDenied):
            self.reserve(identity='unverified')
        self.path.unlink()
        with self.assertRaises(TrialDenied):
            self.reserve()
        self.assertFalse(self.path.exists())

    def test_concurrency_reserves_before_spend_and_duplicate_ids_are_idempotent(self):
        def reserve(identity):
            try:
                return self.reserve(identity)['created']
            except TrialDenied:
                return False
        with ThreadPoolExecutor(max_workers=3) as pool:
            self.assertEqual(sum(pool.map(reserve, ('a', 'b', 'c'))), 1)
        # Use another ledger to check exact retries independently of the race.
        self.now += 86400
        with self.assertRaises(TrialDenied):
            self.reserve('c', 'new-day')  # Old pending spend still counts.

    def test_retries_and_conflicting_payloads_do_not_make_new_reservations(self):
        self.assertTrue(self.reserve()['created'])
        self.assertFalse(self.reserve()['created'])
        with self.assertRaises(TrialDenied):
            self.ledger.reserve('a', 'first', 'b' * 64, 600000)
        self.ledger.uncertain('a', 'first')
        restarted = AITrialBudget(self.path, enabled=True, clock=lambda: self.now)
        self.assertEqual(restarted.reserve('a', 'first', 'a' * 64, 600000)['state'], 'uncertain')
        with self.assertRaises(TrialDenied):
            self.reserve('b')

    def test_account_and_global_concurrency_limits_apply_even_to_cheap_calls(self):
        self.reserve('a', cost=1)
        with self.assertRaises(TrialDenied):
            self.reserve('a', 'second', cost=1)
        self.reserve('b', cost=1)
        with self.assertRaises(TrialDenied):
            self.reserve('c', cost=1)
        self.ledger.settle('b', 'first', 0)
        self.assertTrue(self.reserve('c', cost=1)['created'])

    def test_same_request_race_admits_work_once(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.reserve(cost=1), range(16)))
        self.assertEqual(sum(row['created'] for row in results), 1)

    def test_daily_spend_and_per_account_allowance(self):
        for i in range(3):
            self.reserve(request=str(i), cost=100000)
            self.ledger.settle('a', str(i), 100000)
        self.reserve('b', cost=700000)
        self.ledger.settle('b', 'first', 700000)
        with self.assertRaises(TrialDenied):
            self.reserve('c', cost=1)
        self.now += 86400
        self.assertTrue(self.reserve('c', cost=1)['created'])

    def test_provider_operation_cap_allows_workflows_but_stops_abuse(self):
        for index in range(ACCOUNT_OPERATIONS_PER_DAY):
            self.reserve(request=str(index), cost=1)
            self.ledger.settle('a', str(index), 1)
        with self.assertRaises(TrialDenied):
            self.reserve(request='one-more', cost=1)

    def test_unknown_usage_charges_reservation_without_locking_account(self):
        self.reserve(cost=10000)
        self.ledger.charge_reservation('a', 'first')
        self.assertTrue(self.reserve(request='next', cost=1)['created'])

    def test_voice_hold_allows_one_metered_delegate_but_no_second_voice(self):
        self.ledger.reserve('a', 'voice', 'b' * 64, 100000, lane='voice')
        self.assertTrue(self.reserve(request='delegate', cost=1000)['created'])
        with self.assertRaises(TrialDenied):
            self.reserve(request='parallel', cost=1)
        self.ledger.settle('a', 'delegate', 1000)
        with self.assertRaises(TrialDenied):
            self.ledger.reserve('a', 'voice2', 'b' * 64, 100000, lane='voice')
        self.assertTrue(self.reserve(request='next-delegate', cost=1000)['created'])

    def test_monthly_spend_survives_day_rollover_and_process_restart(self):
        # Start early enough for twenty days in one calendar month.
        self.now -= 15 * 86400
        for day in range(20):
            self.reserve(request=str(day), cost=1000000)
            self.ledger.settle('a', str(day), 1000000)
            self.now += 86400
        self.ledger = AITrialBudget(self.path, enabled=True, clock=lambda: self.now)
        with self.assertRaises(TrialDenied):
            self.reserve('b', cost=1)

    def test_underestimated_usage_halts_new_work_and_cannot_be_refunded_by_retry(self):
        self.reserve(cost=100000)
        self.ledger.settle('a', 'first', 100001)
        with self.assertRaises(TrialDenied):
            self.reserve('b', cost=1)
        with self.assertRaises(TrialDenied):
            self.ledger.settle('a', 'first', 0)
