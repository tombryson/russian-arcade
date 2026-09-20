"""Vocabulary capture from an owned story through the shared lexical pipeline."""
from hashlib import sha256
import logging

from flask import current_app, session

from repositories import StoryRepository
from repositories.learning_repository import LearningError, transaction
from services.ai_trial_budget import TrialDenied
from services.game_vocabulary_discovery import POSITIONS, read_word, save_word
from services.sync_service import SyncService

logger = logging.getLogger(__name__)


def story_key(text):
    return sha256(text.encode('utf-8')).hexdigest()


def _validate_word(word):
    if not isinstance(word, str) or not 1 <= len(word) <= 100:
        raise LearningError('invalid_word', 'Choose one Russian word from this story.', 422)


def _source(db_path, source):
    story_id = source.get('story_id')
    if story_id not in (None, ''):
        if len(str(story_id)) > 20 or not str(story_id).isdigit():
            raise LearningError('invalid_story', 'Reopen this story before choosing a word.', 422)
        story = StoryRepository(db_path).load(story_id)
    else:
        story = session.get('current_story_data')
    if not isinstance(story, dict) or not story.get('text'):
        raise LearningError('story_not_found', 'Reopen this story before choosing a word.', 404)
    if source.get('story_key') != story_key(story['text']):
        raise LearningError('story_changed', 'This story has changed. Reopen it before choosing a word.', 409)
    # No browser-supplied sentence, meaning or morphology is trusted here.
    return {'vocabulary_refs': [{'sentence': story['text']}]}


def _with_mnemonic(conn, result):
    for reading in [result, *result.get('choices', [])]:
        if reading.get('word_id'):
            row = conn.execute('SELECT lemma,topic,mnemonic FROM words WHERE id=?', (reading['word_id'],)).fetchone()
            if row:
                missing_hint = SyncService._missing_mnemonic(row['mnemonic'], row['lemma'])
                reading['mnemonic'] = '' if missing_hint else row['mnemonic']
                reading['enrichment_pending'] = missing_hint or SyncService._missing_topics(row['topic'])
    return result


def lookup_story_word(db_path, word, source):
    _validate_word(word)
    content = _source(db_path, source)
    with transaction(db_path) as conn:
        return _with_mnemonic(conn, read_word(conn, content, word))


def capture_story_word(db_path, word, lemma, pos, source):
    _validate_word(word)
    _validate_word(lemma)
    if not isinstance(pos, str) or pos not in POSITIONS:
        raise LearningError('invalid_reading', 'Choose the word that fits this sentence.', 422)
    content = _source(db_path, source)
    with transaction(db_path, write=True) as conn:
        result = save_word(conn, content, word, lemma, pos)
    # The configured service meters hosted provider calls and keeps retries
    # idempotent. Commit morphology first; AI must never hold a write lock.
    try:
        enrichment = current_app.extensions['services']['SyncService'].enrich_words([result['word_id']])
    except TrialDenied as error:
        raise LearningError('vocabulary_enrichment_pending',
                            'The word is saved. ' + str(error), 429,
                            {'saved': True, 'word_id': result['word_id'], 'enrichment_pending': True}) from None
    except Exception as error:
        logger.warning('Story vocabulary enrichment failed (%s)', type(error).__name__)
        enrichment = {'pending': [result['word_id']]}
    if enrichment['pending']:
        raise LearningError('vocabulary_enrichment_pending',
                            'The word is saved. Its topics and memory hint could not be prepared yet. Retry to finish adding it.',
                            503, {'saved': True, 'word_id': result['word_id'], 'enrichment_pending': True})
    with transaction(db_path) as conn:
        return _with_mnemonic(conn, result)
