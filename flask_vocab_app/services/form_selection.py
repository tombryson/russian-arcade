"""Coverage-aware selection from the existing lexical tables.

Frequency preferences match the importer, but never delete a stored form or
override an explicitly selected lesson occurrence. Count means export history,
not learner mastery; native selection history is kept separately.
"""
from collections import Counter
from functools import lru_cache
import json

from wordfreq import word_frequency


@lru_cache(maxsize=10000)
def frequency(surface):
    return word_frequency(surface, 'ru')


def coverage(conn, owner=None):
    words, forms, grammar = Counter(), Counter(), Counter()
    sql = "SELECT selection FROM native_card_generation_items i JOIN native_card_batches b ON b.id=i.batch_id WHERE i.status != 'failed'"
    for row in conn.execute(sql + (' AND b.owner_id=?' if owner else ''), (owner,) if owner else ()):
        item = json.loads(row[0])
        words[item.get('word_id')] += 1
        forms[item.get('form_id')] += 1
        grammar[bucket(item.get('tags', {}))] += 1
    return words, forms, grammar


def bucket(tags):
    return tuple((key, tags[key]) for key in ('case', 'tense', 'person', 'number') if tags.get(key))


def choose_form(forms, lemma, used, grammar):
    def rank(form):
        tags = json.loads(form['tags'] or '{}')
        freq = frequency(form['form'])
        participle = tags.get('pos') in ('PRTF', 'PRTS', 'PART', 'participle', 'short participle')
        uncommon = freq < (2e-6 if participle else 6e-7)
        return (uncommon, used[form['id']], grammar[bucket(tags)],
                form['form'].casefold() == lemma.casefold(), -freq, form['id'])
    valid = []
    for form in forms:
        try:
            if isinstance(json.loads(form['tags'] or '{}'), dict):
                valid.append(form)
        except (ValueError, TypeError):
            continue
    return min(valid, key=rank) if valid else None
