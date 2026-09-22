"""Freeze curriculum practice coverage from saved, learner-owned assessments.

This is preparation evidence, not a proficiency score. Corrections can count,
but repeating one task cannot replace practice across a chapter's topics.
No metadata supplied by the browser, imported words or self-rated cards can
declare a chapter learned.
"""
import json
import math

from services.curriculum import get_topic, normalize_level

WRITTEN = {
    'translation': ('sentences', 'translation:', 'translation_attempts', 'sentence_id', 'translation-attempt:', 4),
    'writing': ('writing_exercises', 'writing:', 'writing_attempts', 'exercise_id', 'writing-attempt:', 10),
    'word_jumble': ('word_jumble_games', 'word-jumble:', 'word_jumble_attempts', 'game_id', 'word-jumble-attempt:', 4),
}


def _json(raw, fallback=None):
    try:
        return json.loads(raw) if raw else fallback
    except (ValueError, TypeError):
        return fallback


def _coverage(topic, level, score, maximum, activity, assisted=False):
    if (not isinstance(topic, str) or not get_topic(topic)
            or type(score) not in (int, float) or not math.isfinite(score)
            or not 0 <= score <= maximum):
        return None
    try:
        level = normalize_level(level, legacy=activity)
    except ValueError:
        return None
    return {'topic_id': topic, 'level': level, 'score': score / maximum,
            'assisted': bool(assisted), 'basis': 'saved_task_assessment'}


def freeze_course_evidence(conn, profile_id, activity, content_key, source_key, evidence):
    result = dict(evidence or {})
    result.pop('_course', None)
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='course_evidence'").fetchone():
        return result
    coverage = None
    if activity in WRITTEN:
        table, prefix, attempts, foreign_key, attempt_prefix, maximum = WRITTEN[activity]
        if not str(content_key).startswith(prefix) or not str(source_key).startswith(attempt_prefix):
            return result
        task_id, attempt_id = str(content_key)[len(prefix):], str(source_key)[len(attempt_prefix):]
        # Identifiers are private constants; all user/content values are bound.
        row = conn.execute(f'''SELECT t.topic,t.difficulty,a.score FROM {table} t
            JOIN {attempts} a ON a.{foreign_key}=t.id WHERE t.id=? AND a.id=?
            AND COALESCE(t.owner_profile_id,'personal-learning')=?''',
            (task_id, attempt_id, profile_id)).fetchone()
        if row:
            coverage = _coverage(row[0], row[1], row[2], maximum, activity,
                                 result.get('assisted') or result.get('hint_used'))
    elif activity == 'reading' and str(content_key).startswith('story:'):
        row = conn.execute('''SELECT topic,difficulty,score,questions,answers FROM saved_stories
            WHERE id=? AND COALESCE(owner_profile_id,'personal-learning')=?''',
            (str(content_key)[6:], profile_id)).fetchone()
        if (row and result.get('course_task_context_matches') is True
                and str(source_key).startswith('story-check:')):
            questions, answers = _json(row[3], []), _json(row[4], [])
            if questions and answers and len(answers) == len(questions):
                from repositories.learning_repository import payload_hash
                # Tie the event to exactly the checked passage questions/answers.
                digest = payload_hash({'story_id': int(str(content_key)[6:]),
                                       'questions': questions, 'answers': answers})
                if str(source_key).startswith('story-check:' + digest + ':'):
                    coverage = _coverage(row[0], row[1], row[2], 10, 'reading',
                                         result.get('assisted') or result.get('hint_used'))
    elif activity == 'speaking':
        row = conn.execute('''SELECT s.scenario_json,s.target_level,r.report_json
            FROM live_conversation_sessions s JOIN speaking_reviews r ON r.session_id=s.id
            WHERE s.id=? AND s.profile_id=? AND r.state='ready' ''', (source_key, profile_id)).fetchone()
        if row:
            scenario, report = _json(row[0], {}), _json(row[2], {})
            grammar = report.get('grammar') or {}
            goals = report.get('goals') or []
            if (report.get('rubric_version') == 'speaking-audio-v1'
                    and report.get('speech_status') in ('russian', 'mixed')
                    and grammar.get('evidence') and goals
                    and all(g.get('status') == 'completed' and g.get('evidence') for g in goals)):
                score = grammar.get('score')
                if type(score) is int and 1 <= score <= 5:
                    coverage = _coverage((scenario.get('curriculum_context') or {}).get('topic_id'),
                                         row[1], score - 1, 4, 'speaking')
    elif activity == 'speaking_step':
        row = conn.execute('''SELECT scenario_json,target_level,dialogue_json,progress_json,state
            FROM step_conversation_sessions WHERE id=? AND profile_id=?''', (source_key, profile_id)).fetchone()
        if row and row[4] == 'completed':
            scenario, dialogue, progress = _json(row[0], {}), _json(row[2], {}), _json(row[3], {})
            turns = dialogue.get('turns') or []
            if turns and all(progress.get(t['id'], {}).get('answered') for t in turns):
                coverage = _coverage((scenario.get('curriculum_context') or {}).get('topic_id'),
                                     row[1], 1, 1, 'speaking', True)
    if coverage:
        result['_course'] = coverage
    return result
