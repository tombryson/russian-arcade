"""Read-only course inventory and optional migration rehearsal on a DB copy.

Reports counts, never learner names, answers or credentials. The original
database is opened read-only and is never upgraded by this command.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'flask_vocab_app'))
KNOWN = {'a1-v1': {'a1-post-office', 'a1-home', 'a1-market', 'a1-delivery'},
         'a1-journey-v2': {'home', 'postoffice', 'market', 'leavingtown'}}
PRESERVE = ('course_checkpoint_attempts', 'course_checkpoint_requests', 'course_checkpoint_submissions',
            'course_chapter_passes', 'course_evidence', 'course_continuation_entitlements')


def inventory(conn):
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    result = {'schema': conn.execute('SELECT MAX(version) FROM schema_migrations').fetchone()[0],
              'counts': {name: conn.execute('SELECT COUNT(*) FROM ' + name).fetchone()[0] for name in PRESERVE if name in tables},
              'foreign_key_errors': len(conn.execute('PRAGMA foreign_key_check').fetchall()), 'unknown_sections': 0}
    if 'course_checkpoint_attempts' in tables:
        columns = {row[1] for row in conn.execute('PRAGMA table_info(course_checkpoint_attempts)')}
        release = 'release_id' if 'release_id' in columns else "'a1-v1'"
        result['active_attempts'] = conn.execute("SELECT COUNT(*) FROM course_checkpoint_attempts WHERE status='active'").fetchone()[0]
        for edition, section in conn.execute('SELECT ' + release + ',chapter_id FROM course_checkpoint_attempts'):
            if section not in KNOWN.get(edition, set()):
                result['unknown_sections'] += 1
    return result


def digest(conn, table, columns):
    rows = conn.execute('SELECT ' + ','.join('"' + c + '"' for c in columns) + ' FROM ' + table).fetchall()
    return hashlib.sha256(json.dumps(sorted([list(r) for r in rows], key=repr), ensure_ascii=False, default=str).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('--rehearse', action='store_true')
    args = parser.parse_args()
    if not args.db.is_file():
        raise SystemExit('Database not found.')
    with sqlite3.connect(args.db.resolve().as_uri() + '?mode=ro', uri=True) as source:
        report = inventory(source)
        if report['foreign_key_errors'] or report['unknown_sections']:
            print(json.dumps(report, indent=2))
            raise SystemExit('Resolve course integrity findings before release.')
        if args.rehearse:
            snapshots = {}
            for table in report['counts']:
                columns = [row[1] for row in source.execute('PRAGMA table_info(' + table + ')')]
                snapshots[table] = columns, digest(source, table, columns)
            with tempfile.TemporaryDirectory(prefix='arcade-course-rehearsal-') as directory:
                copy = Path(directory) / 'copy.db'
                with sqlite3.connect(copy) as destination:
                    source.backup(destination)
                from migrations import upgrade_database
                version, _ = upgrade_database(str(copy), backup=False)
                with sqlite3.connect(copy) as migrated:
                    retained = all(digest(migrated, table, columns) == expected for table, (columns, expected) in snapshots.items())
                    report['rehearsal'] = {'schema': version, 'existing_course_rows_unchanged': retained,
                                           'foreign_key_errors': len(migrated.execute('PRAGMA foreign_key_check').fetchall())}
                    if not retained or report['rehearsal']['foreign_key_errors']:
                        raise SystemExit('Migration rehearsal failed; original database is unchanged.')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
