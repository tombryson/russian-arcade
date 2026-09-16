"""Persistent admission ledger for a future authenticated AI trial.

No public route calls this yet. The caller must verify identity and constrain
the complete provider workflow before requesting its maximum cost. Amounts are
integer millionths of a US dollar; there is no floating-point money arithmetic.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import time

DAILY_LIMIT = 1_000_000
MONTHLY_LIMIT = 20_000_000


class TrialDenied(ValueError):
    pass


class AITrialBudget:
    def __init__(self, path, *, enabled=False, clock=time.time):
        self.path, self.enabled, self.clock = Path(path), enabled, clock

    def initialize(self):
        """Explicit administration step; never silently recreate a lost ledger."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS trial_accounts (
                    identity TEXT PRIMARY KEY, enabled INTEGER NOT NULL CHECK(enabled IN (0,1)));
                CREATE TABLE IF NOT EXISTS trial_control (
                    id INTEGER PRIMARY KEY CHECK(id=1), halted INTEGER NOT NULL DEFAULT 0);
                INSERT OR IGNORE INTO trial_control(id) VALUES (1);
                CREATE TABLE IF NOT EXISTS trial_requests (
                    identity TEXT NOT NULL REFERENCES trial_accounts(identity),
                    request_id TEXT NOT NULL, payload_hash TEXT NOT NULL,
                    reserved INTEGER NOT NULL CHECK(reserved>0),
                    actual INTEGER CHECK(actual>=0), created_at INTEGER NOT NULL,
                    settled_at INTEGER, state TEXT NOT NULL CHECK(state IN ('reserved','uncertain','settled')),
                    PRIMARY KEY(identity,request_id));
            ''')

    @contextmanager
    def _transaction(self):
        # mode=rw fails if a volume or file disappeared. It does not reset spend.
        conn = None
        try:
            conn = sqlite3.connect(self.path.resolve().as_uri() + '?mode=rw', uri=True, timeout=5)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('BEGIN IMMEDIATE')
            yield conn
            conn.commit()
        except sqlite3.Error as error:
            raise TrialDenied('The trial ledger is unavailable; AI is paused.') from error
        finally:
            if conn:
                conn.close()

    def authorize_identity(self, verified_identity):
        """For a trusted auth callback/admin only, never a browser-supplied ID."""
        if not verified_identity or len(verified_identity) > 200:
            raise TrialDenied('A verified identity is required.')
        with self._transaction() as conn:
            conn.execute('INSERT OR IGNORE INTO trial_accounts(identity,enabled) VALUES (?,1)', (verified_identity,))

    def reserve(self, identity, request_id, payload_hash, maximum_cost):
        if not self.enabled:
            raise TrialDenied('The AI trial is disabled.')
        if type(maximum_cost) is not int or not 0 < maximum_cost <= DAILY_LIMIT:
            raise TrialDenied('A bounded maximum cost is required.')
        if not isinstance(request_id, str) or not 1 <= len(request_id) <= 128:
            raise TrialDenied('A request ID is required.')
        if not isinstance(payload_hash, str) or len(payload_hash) != 64 or any(c not in '0123456789abcdef' for c in payload_hash):
            raise TrialDenied('A SHA-256 input digest is required.')
        now = int(self.clock())
        date = datetime.fromtimestamp(now, timezone.utc)
        day = int(date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        month = int(date.replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp())
        with self._transaction() as conn:
            account = conn.execute('SELECT enabled FROM trial_accounts WHERE identity=?', (identity,)).fetchone()
            if not account or not account['enabled']:
                raise TrialDenied('A verified trial account is required.')
            previous = conn.execute('SELECT * FROM trial_requests WHERE identity=? AND request_id=?', (identity, request_id)).fetchone()
            if previous:
                if previous['payload_hash'] != payload_hash or previous['reserved'] != maximum_cost:
                    raise TrialDenied('That request ID already belongs to another request.')
                return dict(previous) | {'created': False}
            if conn.execute('SELECT halted FROM trial_control WHERE id=1').fetchone()['halted']:
                raise TrialDenied('AI spending is paused pending review.')
            pending = conn.execute("SELECT identity,reserved FROM trial_requests WHERE state!='settled'").fetchall()
            if len(pending) >= 2 or any(row['identity'] == identity for row in pending):
                raise TrialDenied('Please wait for the current AI request to finish.')
            if conn.execute('SELECT COUNT(*) FROM trial_requests WHERE identity=? AND created_at>=?', (identity, day)).fetchone()[0] >= 3:
                raise TrialDenied('Your daily trial allowance is used.')
            # Reservations from earlier periods still count until reconciled.
            held = sum(row['reserved'] for row in pending)
            for start, limit in ((day, DAILY_LIMIT), (month, MONTHLY_LIMIT)):
                spent = conn.execute("SELECT COALESCE(SUM(actual),0) FROM trial_requests WHERE state='settled' AND settled_at>=?", (start,)).fetchone()[0]
                if spent + held + maximum_cost > limit:
                    raise TrialDenied('The shared AI budget is used. Sample practice is still available.')
            conn.execute("INSERT INTO trial_requests(identity,request_id,payload_hash,reserved,created_at,state) VALUES (?,?,?,?,?,'reserved')",
                         (identity, request_id, payload_hash, maximum_cost, now))
            return {'identity': identity, 'request_id': request_id, 'reserved': maximum_cost, 'state': 'reserved', 'created': True}

    def uncertain(self, identity, request_id):
        """A timeout/crash is not proof of zero provider charges."""
        with self._transaction() as conn:
            conn.execute("UPDATE trial_requests SET state='uncertain' WHERE identity=? AND request_id=? AND state='reserved'", (identity, request_id))

    def settle(self, identity, request_id, actual_cost):
        """Only trusted provider usage/reconciliation may settle a reservation."""
        if type(actual_cost) is not int or actual_cost < 0:
            raise TrialDenied('Verified usage is required.')
        with self._transaction() as conn:
            row = conn.execute('SELECT * FROM trial_requests WHERE identity=? AND request_id=?', (identity, request_id)).fetchone()
            if not row:
                raise TrialDenied('No reservation was found.')
            if row['state'] == 'settled':
                if row['actual'] != actual_cost:
                    raise TrialDenied('This request already has different recorded usage.')
                return
            conn.execute("UPDATE trial_requests SET actual=?,settled_at=?,state='settled' WHERE identity=? AND request_id=?",
                         (actual_cost, int(self.clock()), identity, request_id))
            if actual_cost > row['reserved']:
                # Preserve the real bill, then stop all new admissions. Do not
                # hide an underestimated workflow cost by rolling back usage.
                conn.execute('UPDATE trial_control SET halted=1 WHERE id=1')
