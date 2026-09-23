"""Build a private account import artifact from two offline SQLite snapshots.

This is intentionally not a web endpoint or an in-place migration. Unsupported
conflicts stop the import. The caller must separately copy media, stop writers,
verify the hosted snapshot is still current, and install the checked artifact.
"""
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import tempfile

from migrations import upgrade_database


class ImportConflict(ValueError):
    """An import needs an explicit policy before it can proceed."""


AUTH_TABLES = {'household_access', 'household_settings'}
CATALOGUE_TABLES = {
    'schema_migrations', 'learning_activity_types', 'speaking_scenarios',
    'speaking_scenario_levels', 'speaking_scenario_variants', 'journey_worlds',
    'progression_settings',
}
ACTIVITY_TABLES = {'saved_stories', 'writing_exercises', 'sentences'}
JSON_REFERENCES = {
    'word_id': 'words', 'form_id': 'forms', 'exercise_id': 'writing_exercises',
    'story_id': 'saved_stories', 'sentence_id': 'sentences',
}
ACTIVITY_NAMES = {'reading': 'saved_stories', 'writing': 'writing_exercises',
                  'translation': 'sentences', 'sentence': 'sentences'}
ARCHIVE_TABLE = 'account_import_archive'
HOSTED_OVERLAY_TABLES = CATALOGUE_TABLES | AUTH_TABLES | {
    'words', 'forms', 'learning_profiles', 'profile_onboarding', 'users',
    'card_definitions', 'card_versions', 'learning_content',
    'learning_content_versions', 'learning_content_words', 'learning_assets',
    'learning_content_assets', 'live_conversation_events',
    'live_conversation_recordings', 'live_conversation_sessions',
    'speaking_reviews', 'step_conversation_answers', 'step_conversation_sessions',
    'writing_details', 'writing_exercises', 'writing_drafts',
    # Only unused schema-044 default enrolments pass the explicit check below.
    # Course attempts, evidence, passes and continuation rights remain guarded.
    'course_enrolments',
}


def quoted(name):
    return '"' + name.replace('"', '""') + '"'


def digest(path):
    with open(path, 'rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def readonly(path):
    path = Path(path).resolve(strict=True)
    conn = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA query_only=ON')
    return conn


def inspect(conn):
    if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise ImportConflict('An input database failed its integrity check.')
    if conn.execute('PRAGMA foreign_key_check').fetchone():
        raise ImportConflict('An input database has broken foreign keys.')
    tables = {}
    for row in conn.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        name = row['name']
        if name == ARCHIVE_TABLE:
            raise ImportConflict('This snapshot was already imported; review its provenance before another merge.')
        info = [dict(item) for item in conn.execute('PRAGMA table_info(' + quoted(name) + ')')]
        pk = [item['name'] for item in sorted(info, key=lambda item: item['pk']) if item['pk']]
        if not pk:
            raise ImportConflict(f'{name} has no primary key; a merge policy is required.')
        tables[name] = {'sql': row['sql'], 'columns': [item['name'] for item in info],
                        'pk': pk, 'info': info,
                        'foreign': [dict(item) for item in conn.execute('PRAGMA foreign_key_list(' + quoted(name) + ')')],
                        'rows': [dict(item) for item in conn.execute('SELECT * FROM ' + quoted(name))]}
    return tables


def row_key(table, row):
    return tuple(row[column] for column in table['pk'])


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _mapped(maps, table, value):
    return maps.get(table, {}).get(value, value)


def _json_refs(value, maps):
    if isinstance(value, list):
        return [_json_refs(item, maps) for item in value]
    if isinstance(value, dict):
        return {key: _mapped(maps, JSON_REFERENCES[key], item)
                if key in JSON_REFERENCES and isinstance(item, int) and not isinstance(item, bool)
                else _json_refs(item, maps) for key, item in value.items()}
    return value


def transform(name, table, row, maps, schemas):
    result = dict(row)
    if len(table['pk']) == 1:
        key = table['pk'][0]
        result[key] = _mapped(maps, name, result[key])
    for fk in table['foreign']:
        parent = schemas[fk['table']]
        if len(parent['pk']) == 1 and (fk['to'] or parent['pk'][0]) == parent['pk'][0]:
            result[fk['from']] = _mapped(maps, fk['table'], row[fk['from']])
    # IDs embedded in typed JSON are references. Do not replace arbitrary
    # numbers, Russian text, dates, answers or model output with matching digits.
    for column, value in row.items():
        if isinstance(value, str) and value.lstrip().startswith(('{', '[')):
            try:
                parsed = json.loads(value)
            except ValueError:
                continue
            changed = _json_refs(parsed, maps)
            if changed != parsed:
                result[column] = encode(changed)
    if name == 'progression_events' and row['activity'] in ACTIVITY_NAMES:
        target = ACTIVITY_NAMES[row['activity']]
        value = row['content_key']
        if value.isdigit():
            result['content_key'] = str(_mapped(maps, target, int(value)))
    if name in ('progression_claims', 'reward_events'):
        column = 'content_key' if name == 'progression_claims' else 'reward_key'
        match = re.fullmatch(r'(reading|writing|translation|sentence):(\d+)', row[column])
        if match:
            result[column] = match[1] + ':' + str(_mapped(maps, ACTIVITY_NAMES[match[1]], int(match[2])))
    return result


def _allocate(existing, incoming, table, *, field='id', natural=None):
    """Keep matching natural keys; otherwise allocate IDs clear of both inputs."""
    used = {row[field] for row in existing} | {row[field] for row in incoming}
    next_id = max(used, default=0) + 1
    by_id = {row[field]: row for row in existing}
    by_natural = {}
    if natural:
        for row in existing:
            by_natural.setdefault(tuple(row[key] for key in natural), []).append(row[field])
    mapping = {}
    for row in incoming:
        old = row[field]
        candidates = by_natural.get(tuple(row[key] for key in natural), []) if natural else []
        if len(candidates) > 1:
            raise ImportConflict(f'Ambiguous {table} natural key; choose the intended lexical record explicitly.')
        match = candidates[0] if candidates else None
        if match is not None:
            mapping[old] = match
        elif old in by_id:
            mapping[old] = next_id
            next_id += 1
        else:
            mapping[old] = old
    return mapping


def _merge_duplicate(name, local, hosted):
    if name in CATALOGUE_TABLES:
        return local, 'Keep the upgraded local catalogue and activation history.'
    if name == 'learning_profiles':
        if local['id'] != 'personal-learning' or local['legacy_user_id'] != hosted['legacy_user_id']:
            raise ImportConflict('Conflicting profile identities require a specific mapping.')
        merged = dict(local, display_name=hosted['display_name'])
        return merged, 'Keep the hosted account name and local study timezone/history.'
    if name == 'profile_onboarding':
        merged = dict(local)
        for field in ('coins_introduced_at', 'progress_introduced_at'):
            values = [value for value in (local[field], hosted[field]) if value is not None]
            merged[field] = min(values) if values else None
        return merged, 'Keep completed introductions from either workspace.'
    if name == 'course_enrolments':
        if (not _baseline_course_enrolment(hosted)
                or any(local[field] != hosted[field] for field in ('profile_id', 'band', 'release_id'))):
            raise ImportConflict('Conflicting course_enrolments record; course release choices require a specific mapping.')
        return local, 'Keep the local course enrolment; archive the hosted automatic schema-044 default.'
    if name == 'users' and hosted['lingocoins'] == 0 and hosted['elo_rating'] == 1000:
        return local, 'Keep the existing local legacy balance; hosted legacy user is unused.'
    if name in ('words', 'forms'):
        merged = dict(local)
        # These counts represent legacy generation activity, not a live card
        # total. The present hosted seed has zero; do not guess at additive use.
        if hosted.get('count', 0) not in (0, local.get('count', 0)):
            raise ImportConflict(f'{name} has independent usage counts requiring reconciliation.')
        for field in ('mnemonic', 'topic'):
            if field in merged and not merged[field] and hosted.get(field):
                merged[field] = hosted[field]
        return merged, 'Keep enriched local vocabulary; retain alternate metadata in import archive.'
    raise ImportConflict(f'Conflicting {name} record; no automatic merge policy exists.')


def _baseline_course_enrolment(row):
    """Recognise migration metadata, never an explicit course choice or pass."""
    return (row['band'] == 'A1' and row['release_id'] == 'a1-v1'
            and row['migration_source'] == 'schema-044')


def _assert_baseline_course_enrolments(tables):
    # Migration045 creates these rows even for an entirely unused workspace.
    # Timestamps differ between snapshots, so preserve the local enrolment and
    # archive that metadata difference. Unsupported hosted history is still
    # rejected by the ordinary table gate, including earned continuation rights.
    profiles = {row['id'] for row in tables.get('learning_profiles', {}).get('rows', [])}
    for row in tables.get('course_enrolments', {}).get('rows', []):
        if not _baseline_course_enrolment(row) or row['profile_id'] not in profiles:
            raise ImportConflict('Hosted history needs an additional merge policy: course_enrolments')


def _repair_card_projections(merged):
    """Rebuild ID-dependent indexes without changing card IDs or objectives."""
    from contracts.flashcards import card_item, objective
    definitions = {row['id']: row for row in merged['card_definitions']}
    indexed = {}
    for row in merged['learning_content_versions']:
        pack = json.loads(row['payload'])
        if pack.get('kind') != 'deck':
            continue
        for item in pack['items']:
            card = card_item(pack, item)
            signature = objective(card)
            previous = indexed.setdefault(card['card_id'], signature)
            if previous != signature:
                raise ImportConflict('A card has conflicting retrieval objectives across versions.')
            definition = definitions[card['card_id']]
            if definition['word_id'] != card.get('word_id') or definition['form_id'] != card.get('form_id'):
                raise ImportConflict('A card index does not match its content references.')
            definition['objective_hash'] = signature
            definition['sibling_key'] = 'word:' + str(card['word_id']) if card.get('word_id') else 'sense:' + card['sense_key']


def _assert_inactive_jobs(tables):
    import time
    now = int(time.time())
    for name, schema in tables.items():
        if name in AUTH_TABLES:
            continue
        for row in schema['rows']:
            if row.get('lease_until', 0) and row['lease_until'] > now:
                raise ImportConflict(f'{name} contains a running provider operation. Finish it before taking snapshots.')
            if name == 'live_conversation_sessions' and row['state'] in ('connecting', 'live', 'ending'):
                raise ImportConflict('End live conversations before taking snapshots.')


def build_account_import(local_path, hosted_path, output_path):
    """Create an integrity-checked output file; never modify either input.

    Inputs must be offline snapshots. The returned report contains counts and
    ID mappings, not lesson content or credentials. Metadata alternatives are
    archived inside the private output database.
    """
    local_path, hosted_path = Path(local_path).resolve(strict=True), Path(hosted_path).resolve(strict=True)
    output_path = Path(output_path).resolve()
    if output_path.exists() or output_path in (local_path, hosted_path):
        raise ImportConflict('Output must be a new file; inputs and existing databases cannot be overwritten.')
    hashes = {'local': digest(local_path), 'hosted': digest(hosted_path)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='account-import-', dir=output_path.parent) as temporary:
        upgraded = Path(temporary) / 'local-upgraded.db'
        with closing(readonly(local_path)) as source, closing(sqlite3.connect(upgraded)) as target:
            source.backup(target)
        upgrade_database(upgraded, backup=False)
        with closing(readonly(upgraded)) as left, closing(readonly(hosted_path)) as right:
            local, hosted = inspect(left), inspect(right)
            _assert_inactive_jobs(local)
            _assert_inactive_jobs(hosted)
            _assert_baseline_course_enrolments(hosted)
            unsupported = [name for name, table in hosted.items() if table['rows'] and name not in HOSTED_OVERLAY_TABLES]
            if unsupported:
                raise ImportConflict('Hosted history needs an additional merge policy: ' + ', '.join(sorted(unsupported)))
            if set(local) != set(hosted):
                raise ImportConflict('Both snapshots must use the current application schema.')
            for name in local:
                shape = lambda t: [(c['name'], c['type'], c['pk']) for c in t['info']]
                if shape(local[name]) != shape(hosted[name]):
                    raise ImportConflict(f'Schema mismatch in {name}.')
            supplementary = [dict(row) for row in left.execute("SELECT type,name,sql FROM sqlite_master WHERE type IN ('index','trigger') AND sql IS NOT NULL")]
            sequences = {row['name']: row['seq'] for row in left.execute('SELECT * FROM sqlite_sequence')}

        local_maps, hosted_maps = {}, {}
        for name in ACTIVITY_TABLES:
            local_maps[name] = _allocate(hosted[name]['rows'], local[name]['rows'], name)
        hosted_maps['words'] = _allocate(local['words']['rows'], hosted['words']['rows'], 'words', natural=('lemma', 'pos'))
        rewritten_forms = [dict(row, word_id=_mapped(hosted_maps, 'words', row['word_id'])) for row in hosted['forms']['rows']]
        hosted_maps['forms'] = _allocate(local['forms']['rows'], rewritten_forms, 'forms', natural=('word_id', 'form', 'tags'))
        hosted_maps['live_conversation_events'] = _allocate(local['live_conversation_events']['rows'], hosted['live_conversation_events']['rows'], 'live_conversation_events')

        archive, merged, decisions = [], {}, Counter()
        for name, schema in local.items():
            if name in AUTH_TABLES:
                merged[name] = []
                continue
            values = {row_key(schema, value): value for row in schema['rows']
                      for value in [transform(name, schema, row, local_maps, local)]}
            if len(values) != len(schema['rows']):
                raise ImportConflict(f'Local ID mapping would collapse rows in {name}.')
            for row in hosted[name]['rows']:
                value = transform(name, hosted[name], row, hosted_maps, hosted)
                key = row_key(schema, value)
                if key not in values:
                    values[key] = value
                elif values[key] != value:
                    previous = values[key]
                    resolved, policy = _merge_duplicate(name, previous, value)
                    archive.append((name, encode(key), policy, encode(previous), encode(value)))
                    decisions[name] += 1
                    values[key] = resolved
            merged[name] = list(values.values())

        _repair_card_projections(merged)

        artifact = Path(temporary) / 'merged.db'
        with closing(sqlite3.connect(artifact)) as conn:
            conn.execute('PRAGMA foreign_keys=OFF')
            conn.execute('BEGIN IMMEDIATE')
            for schema in local.values():
                conn.execute(schema['sql'])
            for name, schema in local.items():
                columns = schema['columns']
                sql = 'INSERT INTO ' + quoted(name) + '(' + ','.join(map(quoted, columns)) + ') VALUES (' + ','.join('?' for _ in columns) + ')'
                try:
                    conn.executemany(sql, [tuple(row[column] for column in columns) for row in merged[name]])
                except sqlite3.IntegrityError as error:
                    raise ImportConflict(f'Conflicting unique records in {name}: {error}') from error
            for item in supplementary:
                conn.execute(item['sql'])
            conn.execute(f'CREATE TABLE {ARCHIVE_TABLE}(id INTEGER PRIMARY KEY, table_name TEXT NOT NULL, row_key TEXT NOT NULL, policy TEXT NOT NULL, local_row_json TEXT NOT NULL, hosted_row_json TEXT NOT NULL)')
            conn.executemany(f'INSERT INTO {ARCHIVE_TABLE}(table_name,row_key,policy,local_row_json,hosted_row_json) VALUES (?,?,?,?,?)', archive)
            for name, sequence in sequences.items():
                conn.execute('UPDATE sqlite_sequence SET seq=MAX(seq,?) WHERE name=?', (sequence, name))
            if conn.execute('PRAGMA foreign_key_check').fetchone():
                raise ImportConflict('Merged data has broken foreign keys; artifact was not produced.')
            if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ImportConflict('Merged database failed integrity validation.')
            conn.commit()
            conn.execute('PRAGMA journal_mode=DELETE')
        if hashes != {'local': digest(local_path), 'hosted': digest(hosted_path)}:
            raise ImportConflict('An input snapshot changed during the import; retry from offline snapshots.')
        # Exclusive creation prevents an existing destination being replaced if
        # a second importer runs while the first one is assembling its output.
        with output_path.open('xb') as output, artifact.open('rb') as source:
            while data := source.read(1024 * 1024):
                output.write(data)
        output_path.chmod(0o600)
    return {'input_sha256': hashes, 'output_sha256': digest(output_path),
            'counts': {name: {'local': len(local[name]['rows']), 'hosted': len(hosted[name]['rows']), 'merged': len(rows)} for name, rows in merged.items()},
            'local_id_mappings': {name: {str(k): v for k, v in values.items() if k != v} for name, values in local_maps.items()},
            'hosted_id_mappings': {name: {str(k): v for k, v in values.items() if k != v} for name, values in hosted_maps.items()},
            'metadata_conflicts_archived': dict(decisions),
            'excluded_credentials': sorted(AUTH_TABLES),
            'media_copied': False}
