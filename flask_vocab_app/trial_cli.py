"""Explicit administration of the shared, persistent demo spending ledger."""
import argparse
import json
import os
from pathlib import Path

from services.ai_trial_budget import AITrialBudget


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('init', 'status', 'pause'))
    parser.add_argument('--root', default=os.environ.get('HOSTED_TRIAL_ROOT'))
    args = parser.parse_args()
    if not args.root:
        parser.error('Set HOSTED_TRIAL_ROOT or pass --root for the persistent workspace.')
    budget = AITrialBudget(Path(args.root) / 'ai-budget.sqlite3')
    if args.command == 'init':
        budget.initialize()
        print('Ledger initialized or upgraded. Existing spending is preserved; AI activation is unchanged.')
        return
    with budget._transaction() as conn:
        if args.command == 'pause':
            conn.execute('UPDATE trial_control SET halted=1 WHERE id=1')
        counts = dict(conn.execute('SELECT state,COUNT(*) FROM trial_requests GROUP BY state').fetchall())
        print(json.dumps({'paused': bool(conn.execute('SELECT halted FROM trial_control WHERE id=1').fetchone()[0]),
            'operations': counts,
            'reserved_usd': conn.execute("SELECT COALESCE(SUM(reserved),0)/1000000.0 FROM trial_requests WHERE state!='settled'").fetchone()[0],
            'accounted_usd': conn.execute('SELECT COALESCE(SUM(actual),0)/1000000.0 FROM trial_requests').fetchone()[0]}))


if __name__ == '__main__':
    main()
