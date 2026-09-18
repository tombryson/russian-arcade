"""Provider-free sample vocabulary using the application's lexical pipeline.

These reviewed topics describe the words. Lesson titles remain source metadata.
No personal vocabulary is copied into the public demo or trial workspaces.
"""
import json
from functools import lru_cache

from services.vocabulary_topics import TOPICS

SAMPLE_TOPICS = {
    ('привет', 'INTJ'): ('greetings',),
    ('спасибо', 'INTJ'): ('greetings',),
    ('письмо', 'NOUN'): ('daily_activities', 'social'),
    ('сумка', 'NOUN'): ('clothing', 'travel'),
    ('карта', 'NOUN'): ('travel', 'places'),
    ('прямо', 'ADVB'): ('places', 'travel'),
    ('налево', 'ADVB'): ('places', 'travel'),
    ('направо', 'ADVB'): ('places', 'travel'),
    ('рынок', 'NOUN'): ('shopping', 'places'),
    ('показать', 'VERB'): ('daily_activities', 'social'),
    ('пожалуйста', 'PRCL'): ('greetings',),
    ('потом', 'ADVB'): ('grammar', 'daily_activities'),
    ('там', 'ADVB'): ('grammar', 'places'),
}


def sample_topics(lemma, pos):
    topics = SAMPLE_TOPICS.get((lemma, pos), ())
    if any(topic not in TOPICS for topic in topics):
        raise ValueError('Sample vocabulary uses an unsupported topic.')
    return list(topics)


def _topics(value):
    try:
        result = json.loads(value or '[]')
    except (ValueError, TypeError):
        return []
    return result if isinstance(result, list) else []


@lru_cache(maxsize=1)
def _pipeline():
    from services.sync_service import SyncService
    return SyncService(':memory:', drive_service=object(), api_key='', config={})


def seed_sample_items(conn, prefix):
    from services.first_steps import HELLO, chapter_content
    from services.lesson_cards import LessonCards, normal
    from utils.story_processing import get_morph
    items = []
    for lesson in [HELLO, *chapter_content()['lessons']]:
        for word in lesson['vocabulary']:
            topics = sample_topics(word['lemma'], word['pos'])
            if not topics:
                raise ValueError('Classify new sample vocabulary before publishing it.')
            resolved = LessonCards.resolve(conn, {**word, 'surface': word['form']})
            row = conn.execute('SELECT * FROM words WHERE id=?', (resolved['word_id'],)).fetchone()
            previous = _topics(row['topic'])
            # Only repair the known seed marker. Preserve user categories,
            # counts, mnemonics and the relational IDs referenced by cards.
            if 'First steps' in previous:
                previous = [topic for topic in previous if topic != 'First steps']
                parsed = next(p for p in get_morph().parse(normal(word['form']))
                              if p.is_known and p.normal_form == word['lemma'] and p.tag.POS == word['pos']
                              and all(getattr(p.tag, key, None) == value for key, value in word['grammar'].items()))
                # The old seed hard-coded 1 rather than computing difficulty.
                conn.execute('UPDATE words SET lemma_difficulty=0 WHERE id=? AND lemma_difficulty=1', (row['id'],))
                if not _pipeline().process_word(word['lemma'], conn, conn.cursor(), parsed=parsed, word_id=row['id']):
                    raise ValueError('Could not repair sample word forms.')
            conn.execute('UPDATE words SET topic=? WHERE id=?',
                         (json.dumps(previous or topics, ensure_ascii=False), row['id']))
            context, answer = word['sentence'], word['form']
            if answer not in context:
                raise ValueError('Sample sentence is missing its target form.')
            identifier = f'{prefix}-{len(items) + 1}'
            items.append(dict(id=identifier, card_id=identifier, word_id=resolved['word_id'], form_id=resolved['form_id'],
                type='cloze', direction='ru-cloze', sense_key=identifier, sense_label=lesson['title'],
                context=context, prompt=context.replace(answer, '[[blank]]', 1), answer=answer,
                cue_en=word['target_meaning'], context_meaning=word['translation']))
    return items
