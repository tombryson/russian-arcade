"""Question-specific reading observations; never listening or writing proficiency.

The source passage, question and bounded expected meaning are frozen together.
A written answer is a way to demonstrate comprehension, not a writing exam.
"""
from copy import deepcopy
import hashlib
import json

from contracts.curriculum import CONTRACT_VERSION, freeze_task_contract, validate_task_contract
from services.curriculum import normalize_level
from services.torfl_requirements import VERSION, reference_for_level
from services.vocabulary_topics import TOPICS
from utils.story_content import validate_reading_focus

CONTENT_VERSION = 'comprehension-reading-v1'
RUBRIC_VERSION = 'comprehension-reading-focus-v1'
QUESTION_INDEXES = ('0', '1', '2', '3')


def reading_candidates(difficulty):
    level = normalize_level(difficulty, legacy='reading')
    reference = reference_for_level(level)
    return {item['id']: item for item in reference['requirements']
            if item['domain'] == 'reading'} if reference else {}


def build_contracts(prepared, topic, difficulty):
    """Freeze the original four passage questions; reflection stays unmapped."""
    level = normalize_level(difficulty, legacy='reading')
    candidates = reading_candidates(level)
    if not candidates:
        return {}
    if topic != 'any' and topic not in TOPICS:
        raise ValueError('Use a canonical comprehension topic.')
    if not isinstance(prepared, dict):
        raise ValueError('Comprehension requires its saved passage and questions.')
    text, questions = prepared.get('text'), prepared.get('questions')
    if (not isinstance(text, str) or not text.strip() or len(text) > 100_000 or '\x00' in text
            or not isinstance(questions, list) or not 5 <= len(questions) <= 20
            or any(not isinstance(q, str) or not q.strip() or len(q) > 2000 or '\x00' in q for q in questions)
            or len(questions) != len(set(questions))):
        raise ValueError('Use a complete passage and five to twenty distinct questions.')
    validate_reading_focus(prepared, candidates, TOPICS if topic == 'any' else (topic,), text)
    contracts = {}
    for focus in sorted(prepared['reading_focus'], key=lambda item: item['question_index']):
        index, rid = focus['question_index'], focus['requirement_id']
        content = {'text': text, 'questions': deepcopy(questions), 'question_index': index,
                   'reading_focus': deepcopy(focus), 'requested_topic': topic, 'topic_id': prepared['topic_id']}
        identity = hashlib.sha256(json.dumps({'content': content, 'level': level, 'version': CONTENT_VERSION},
                                            ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        contracts[str(index)] = freeze_task_contract({
            'schema_version': 1, 'contract_version': CONTRACT_VERSION, 'reference_version': VERSION,
            'task_id': f'comprehension-reading-{identity}', 'activity': 'comprehension',
            'content_version': CONTENT_VERSION, 'level': level, 'topic_ids': [prepared['topic_id']],
            'purpose': 'diagnostic', 'content': content, 'rubric_version': RUBRIC_VERSION,
            'support': {'allowed': ['translation', 'model_answer'],
                        'independence_breakers': ['translation', 'model_answer']},
            'criteria': [{'id': 'reading-focus', 'target_id': f'comprehension-reading.{rid}',
                          'requirement_id': rid, 'response_mode': 'reading_response',
                          'evidence_scope': 'reading_comprehension', 'expectation': focus['expectation'],
                          'max_score': 2, 'source_refs': candidates[rid]['source_refs']}],
        })
    return contracts


def validate_contracts(task):
    """Bind each contract to the full saved task, including extra questions."""
    contracts = task.get('contracts')
    if not isinstance(contracts, dict) or set(contracts) != set(QUESTION_INDEXES):
        raise ValueError('A comprehension task needs its four original reading contracts.')
    for contract in contracts.values():
        validate_task_contract(contract)
    first = contracts['0']['content']
    prepared = {'text': task['text'], 'questions': task['questions'],
                'topic_id': first.get('topic_id'),
                'reading_focus': [contracts[key]['content'].get('reading_focus') for key in QUESTION_INDEXES]}
    expected = build_contracts(prepared, task['topic'], task['difficulty'])
    if not expected or contracts != expected:
        raise ValueError('Reading contracts do not match the saved passage, questions or focus.')
    return deepcopy(contracts)


def reissue_contracts(task, new_questions):
    """Additional questions get a new task identity without new criterion claims."""
    contracts = validate_contracts(task)
    if not isinstance(new_questions, list) or new_questions[:4] != task['questions'][:4]:
        raise ValueError('The four original comprehension questions cannot change their saved focus.')
    prepared = {'text': task['text'], 'questions': new_questions,
                'topic_id': contracts['0']['content']['topic_id'],
                'reading_focus': [contracts[key]['content']['reading_focus'] for key in QUESTION_INDEXES]}
    return build_contracts(prepared, task['topic'], task['difficulty'])
