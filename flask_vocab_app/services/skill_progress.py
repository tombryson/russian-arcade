"""A provisional, replayable practice rating; never a TORFL placement.

Only new, saved assessments receive a versioned difficulty/score snapshot. Reads
replay those receipts without consulting mutable content, awarding coins or
changing the historic users.elo_rating. Each assessed activity has its own scale;
Speaking grammar and fluency remain separate because either may lack evidence.

Pilot model: R starts at 1000; expected performance = 1/(1+10**((D-R)/400));
R += 24*(observed-expected). Task priors are 1000/1200/1400 for the existing
three difficulty choices, and 1000..1800 for Translation choices 1..5. Speaking
authored A1..B2 tasks use 1000..1600. These are explicit uncalibrated task priors,
not claims that a rating represents CEFR proficiency. Scores use the saved task
rubric (0..4 or 0..10; Speaking 1..5 becomes 0..1).

Only the first recorded written assessment per content and skill counts. Speaking
samples the first scored conversation per variant/skill/study day, allowing new
speech on later days. Retries with feedback cannot repeatedly increase ability.
Internal visual stages
are 200 points wide from 1000; a lower rating stays at the start of stage 1 with
the actual remaining gap displayed. Unobserved skills have rating=None, not a
fictional measured 1000. All observed ratings remain explicitly provisional.
"""
import json
import math

POLICY = 'practice-elo-v1'
PRIOR = 1000
STAGE_WIDTH = 200
K = 24
SKILLS = (
    ('reading', 'Reading', 'Чтение'),
    ('listening', 'Listening', 'Аудирование'),
    ('translation', 'Sentence practice', 'Перевод предложений'),
    ('word_jumble', 'Word Jumble', 'Составь предложение'),
    ('writing', 'Writing', 'Письмо'),
    ('speaking_grammar', 'Speaking · grammar', 'Речь · грамматика'),
    ('speaking_fluency', 'Speaking · fluency', 'Речь · беглость'),
)
# SQL identifiers come only from this private constant, never request input.
TASKS = {
    'reading': ('saved_stories', 'story:', 10),
    'translation': ('sentences', 'translation:', 4),
    'word_jumble': ('word_jumble_games', 'word-jumble:', 4),
    'writing': ('writing_exercises', 'writing:', 10),
}
ATTEMPTS = {
    'translation': ('translation_attempts', 'sentence_id', 'translation-attempt:'),
    'writing': ('writing_attempts', 'exercise_id', 'writing-attempt:'),
    'word_jumble': ('word_jumble_attempts', 'game_id', 'word-jumble-attempt:'),
}
THREE_LEVELS = {'beginner': 1000, 'intermediate': 1200, 'advanced': 1400,
                'easy': 1000, 'expert': 1400}
SPEAKING_LEVELS = {'A1': 1000, 'A2': 1200, 'B1': 1400, 'B2': 1600}


def _number(value, lower, upper):
    return type(value) in (int, float) and math.isfinite(value) and lower <= value <= upper


def freeze_evidence(conn, activity, content_key, source_key, target_level, evidence):
    """Attach rating evidence inside the same transaction that saves a check.

    The public award endpoint does not accept these fields from a browser. Ignore
    a caller-supplied _skill snapshot and derive it here from saved task metadata.
    Unsupported or uncertain assessments still earn participation as before.
    """
    result = dict(evidence) if isinstance(evidence, dict) else {}
    result.pop('_skill', None)
    if result.get('assisted') is True or result.get('hint_used') is True:
        return result
    scores = {}
    if activity == 'speaking':
        if (result.get('basis') != 'independent_audio_review'
                or result.get('rubric_version') != 'speaking-audio-v1'
                or result.get('speech_status') not in ('russian', 'mixed')
                or not _number(result.get('russian_word_count'), 8, 100000)):
            return result
        difficulty = SPEAKING_LEVELS.get(target_level)
        raw_difficulty = target_level
        for dimension in ('grammar', 'fluency'):
            value = result.get(dimension)
            if not isinstance(value, dict):
                continue
            score, quotes = value.get('score'), value.get('evidence')
            if (type(score) is int and 1 <= score <= 5 and isinstance(quotes, list)
                    and quotes and all(isinstance(q, str) and q.strip() for q in quotes)):
                scores['speaking_' + dimension] = (score - 1) / 4
    elif activity == 'first_steps':
        # Chapter evidence comes from its frozen server-authored attempt, never
        # caller-provided scores or answer correctness flags.
        row = conn.execute('SELECT chapter_id,lesson_id,version,content_json,answers_json,acknowledged_json,completed_at FROM first_steps_attempts WHERE id=?',
                           (source_key,)).fetchone()
        if not row or row[6] is None or str(content_key) != f'{row[0]}:{row[1]}:{row[2]}':
            return result
        lesson, answers, acknowledged = json.loads(row[3]), json.loads(row[4]), json.loads(row[5])
        questions = lesson['questions']
        if acknowledged != [question['id'] for question in questions] or any(question['id'] not in answers for question in questions):
            return result
        unassisted = [question for question in questions if not answers[question['id']]['hint_used']]
        result.update({'basis': 'first_unassisted_answers', 'lesson_id': row[1], 'version': row[2],
                       'question_count': len(questions), 'unassisted_count': len(unassisted)})
        if not unassisted:
            return result
        difficulty, raw_difficulty = PRIOR, 'first-steps-beginner'
        scores['reading'] = sum(answers[question['id']]['answer'] == question['answer'] for question in unassisted) / len(unassisted)
    elif activity == 'journey_game':
        row = conn.execute('SELECT game_id,content_json,answers_json,acknowledged_json,completed_at,profile_id FROM journey_game_sessions WHERE id=?',
                           (source_key,)).fetchone()
        if not row or row[4] is None:
            return result
        content, answers, acknowledged = json.loads(row[1]), json.loads(row[2]), json.loads(row[3])
        if str(content_key) != f'journey-game:{row[0]}:{content["lesson_version"]}':
            return result
        first = conn.execute("SELECT id FROM journey_game_sessions WHERE profile_id=? AND game_id=? "
                             "AND json_extract(content_json,'$.lesson_version')=? AND completed_at IS NOT NULL "
                             "ORDER BY created_at,rowid LIMIT 1", (row[5], row[0], content['lesson_version'])).fetchone()
        if not first or first[0] != source_key:
            return result
        rounds = content['rounds']
        if acknowledged != [item['id'] for item in rounds] or any(item['id'] not in answers for item in rounds):
            return result
        listening = row[0] == 'radio' or (row[0] == 'letter-back' and content.get('version') == 'journey-vocabulary-v1')
        unassisted = [item for item in rounds if not answers[item['id']].get('hint_used')
                      and not answers[item['id']].get('transcript_used')]
        if listening:
            # A saved play receipt means the browser started the prepared clip;
            # it is not proof of attention, pronunciation or spoken fluency.
            unassisted = [item for item in unassisted if item.get('clues') and
                          {clue['audio_key'] for clue in item['clues']}.issubset(
                              set(answers[item['id']].get('listened_audio_keys', [])))]
        result.update({'basis': 'audio_recognition' if listening else 'contextual_reading_with_optional_audio', 'game_id': row[0],
                       'round_count': len(rounds), 'unassisted_count': len(unassisted)})
        if not unassisted:
            return result
        # Picture choices, classification and supported phrase assembly are
        # comprehension evidence; they do not establish independent writing.
        from services.journey_games import assess_answer
        difficulty, raw_difficulty = PRIOR, 'first-steps-game-beginner'
        if row[0] == 'directions' and content.get('version') in ('journey-vocabulary-v1', 'journey-routes-v1'):
            # Following the route can succeed without identifying the picture's
            # vocabulary. Credit the direction language actually required.
            difficulty, raw_difficulty = PRIOR, {'basis': 'direction-route'}
        elif content.get('version') in ('journey-vocabulary-v1', 'radio-broadcast-v1'):
            word_difficulty = content.get('word_difficulty')
            # Vocabulary bands are local task priors, not a TORFL placement.
            difficulty = 1000 + ((word_difficulty - 1) // 2) * 200 if type(word_difficulty) is int and 1 <= word_difficulty <= 8 else PRIOR
            raw_difficulty = {'basis': 'broadcast-comprehension' if content.get('broadcast') else 'vocabulary-word-difficulty', 'value': word_difficulty}
        scores['listening' if listening else 'reading'] = sum(
            assess_answer(item, answers[item['id']]['answer'])['score'] for item in unassisted
        ) / len(unassisted)
    elif activity in TASKS:
        table, prefix, maximum = TASKS[activity]
        score = result.get('score')
        if (result.get('score_max') != maximum or not _number(score, 0, maximum)
                or not str(content_key).startswith(prefix)):
            return result
        if activity == 'reading' and (not _number(result.get('answered_questions'), 1, 1000)
                or result.get('first_fresh_assessment') is not True):
            return result
        task_id = str(content_key)[len(prefix):]
        if activity in ATTEMPTS:
            attempts, foreign_key, source_prefix = ATTEMPTS[activity]
            first = conn.execute('SELECT id FROM ' + attempts + ' WHERE ' + foreign_key + '=? ORDER BY id LIMIT 1', (task_id,)).fetchone()
            if not first or str(source_key) != source_prefix + str(first[0]):
                return result
        row = conn.execute('SELECT difficulty FROM ' + table + ' WHERE id=?', (task_id,)).fetchone()
        if not row:
            return result
        raw_difficulty = row[0]
        if activity == 'translation':
            # Translation checks before migration 007 left no attempt rows.
            # A nonzero legacy score is still positive evidence of prior use;
            # modern save_check deliberately leaves that old column untouched.
            legacy_score = conn.execute('SELECT score FROM sentences WHERE id=?', (task_id,)).fetchone()[0]
            if legacy_score != 0:
                return result
            difficulty = 800 + 200 * raw_difficulty if type(raw_difficulty) is int and 1 <= raw_difficulty <= 5 else None
        else:
            difficulty = THREE_LEVELS.get(raw_difficulty)
        scores[activity] = score / maximum
    else:
        return result
    if difficulty is not None and scores:
        result['_skill'] = {'policy_version': POLICY, 'task_rating': difficulty,
                            'task_difficulty': raw_difficulty, 'scores': scores}
        if activity == 'speaking':
            result['_skill']['study_day'] = result.get('study_day')
    return result


def snapshot(conn, profile_id):
    """Pure projection: repeated GETs cannot create evidence or alter ratings."""
    state = {key: {'rating': float(PRIOR), 'observations': 0, 'last_updated': None}
             for key, _, _ in SKILLS}
    active = 'reading'
    seen = set()
    cursor = conn.execute('''SELECT activity,content_key,evidence_json,created_at
        FROM progression_events WHERE profile_id=? AND reversed_at IS NULL
        AND activity IN ('reading','translation','word_jumble','writing','speaking','first_delivery','first_steps','journey_game')
        ORDER BY created_at,rowid''', (profile_id,))
    for activity, content_key, evidence_json, created_at in cursor:
        try:
            receipt = json.loads(evidence_json).get('_skill')
        except (ValueError, TypeError, AttributeError):
            continue
        if not isinstance(receipt, dict) or receipt.get('policy_version') != POLICY:
            continue
        difficulty, scores = receipt.get('task_rating'), receipt.get('scores')
        if difficulty not in (1000, 1200, 1400, 1600, 1800) or not isinstance(scores, dict):
            continue
        allowed = ('reading', 'listening') if activity == 'journey_game' else ('reading',) if activity in ('first_delivery', 'first_steps') else ('speaking_grammar', 'speaking_fluency') if activity == 'speaking' else (activity,) if activity in TASKS else ()
        for key in allowed:
            observed = scores.get(key)
            sample_day = receipt.get('study_day') if activity == 'speaking' else None
            if activity == 'speaking' and (not isinstance(sample_day, str) or len(sample_day) != 10):
                continue
            identity = (key, content_key, sample_day)
            if identity in seen or not _number(observed, 0, 1):
                continue
            seen.add(identity)
            item = state[key]
            expected = 1 / (1 + 10 ** ((difficulty - item['rating']) / 400))
            item['rating'] += K * (observed - expected)
            item['observations'] += 1
            item['last_updated'] = created_at
            active = key
    skills = []
    for key, label, label_ru in SKILLS:
        item = state[key]
        rating = round(item['rating']) if item['observations'] else None
        stage = max(1, int(((rating if rating is not None else PRIOR) - PRIOR) // STAGE_WIDTH) + 1)
        start = PRIOR + (stage - 1) * STAGE_WIDTH
        end = start + STAGE_WIDTH
        skills.append({'id': key, 'label': label, 'label_ru': label_ru,
                       'status': 'provisional' if item['observations'] else 'not_calibrated',
                       'rating': rating, 'prior': PRIOR, 'stage': stage,
                       'stage_start': start, 'stage_end': end,
                       'progress': max(0, min(1, ((rating if rating is not None else PRIOR) - start) / STAGE_WIDTH)),
                       'points_to_next': end - (rating if rating is not None else PRIOR),
                       'observations': item['observations'], 'last_updated': item['last_updated']})
    return {'status': 'provisional' if seen else 'not_calibrated',
            'policy_version': POLICY, 'active_skill': active, 'skills': skills}
