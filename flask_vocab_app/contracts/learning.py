"""Small, strict content schema for the first deck and deterministic test activity.

Card text is plain text, never trusted HTML. Publishing is a separate operation.
"""
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from repositories.learning_repository import LearningError


def reject(message):
    raise LearningError('invalid_input', message)


def text(value, label, maximum=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or '\x00' in value:
        reject(f'{label} must contain 1–{maximum} characters.')
    return value.strip()


def key(value, label='ID'):
    cleaned = text(value, label, 100)
    if cleaned != value:
        reject(f'{label} cannot have surrounding whitespace.')
    value = cleaned
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]*', value):
        reject(f'{label} has an invalid format.')
    return value


def fields(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        reject('The submitted fields do not match this operation.')
    return value


def revision(value):
    if type(value) is not int or value < 0:
        reject('A non-negative integer revision is required.')
    return value


def timezone(value):
    value = text(value, 'Study timezone', 80)
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        reject('Choose a valid IANA study timezone, such as Australia/Melbourne.')
    return value


def validate_pack(pack):
    if isinstance(pack, dict) and type(pack.get('schema_version')) is int and pack['schema_version'] == 2:
        from contracts.flashcards import validate_deck
        return validate_deck(pack)
    fields(pack, {'schema_version','id','kind','title','source','items'})
    if type(pack['schema_version']) is not int or pack['schema_version'] != 1:
        reject('Unsupported content schema version.')
    key(pack['id'], 'Content ID')
    text(pack['title'], 'Title', 120)
    text(pack['source'], 'Source', 500)
    if pack['kind'] not in ('deck','activity'):
        reject('Content must be a deck or activity.')
    if not isinstance(pack['items'], list) or not 1 <= len(pack['items']) <= 100:
        reject('A pack needs between 1 and 100 items.')
    seen = set()
    for item in pack['items']:
        fields(item, {'id','type','prompt','answer'}, {'word_id','hint','asset_ids','direction','choices'})
        item_id = key(item['id'], 'Item ID')
        if item_id in seen:
            reject('Item IDs must be unique within a pack.')
        seen.add(item_id)
        text(item['prompt'], 'Prompt')
        if 'hint' in item:
            text(item['hint'], 'Hint')
        if 'word_id' in item and (type(item['word_id']) is not int or item['word_id'] < 1):
            reject('Vocabulary links must be positive integer IDs.')
        assets = item.get('asset_ids', [])
        if not isinstance(assets, list) or len(assets) > 4 or len(set(map(str, assets))) != len(assets):
            reject('Use at most four distinct asset IDs.')
        for asset in assets:
            key(asset, 'Asset ID')
        if pack['kind'] == 'deck':
            if item['type'] not in ('basic','cloze') or 'choices' in item:
                reject('Decks support basic and single-target cloze cards.')
            if item.get('direction') not in ('ru-en','en-ru'):
                reject('Cards require an explicit ru-en or en-ru direction.')
            text(item['answer'], 'Answer')
            if item['type'] == 'cloze' and item['prompt'].count('[[blank]]') != 1:
                reject('A cloze prompt needs exactly one [[blank]] marker.')
        else:
            if item['type'] != 'choice' or 'direction' in item:
                reject('Stage 1 activities support reviewed choice questions.')
            choices = item.get('choices')
            if not isinstance(choices, list) or not 2 <= len(choices) <= 6:
                reject('A choice question needs 2–6 choices.')
            ids, labels = set(), set()
            for choice in choices:
                fields(choice, {'id','text'})
                cid, label = key(choice['id']), text(choice['text'], 'Choice', 200)
                if cid in ids or label in labels:
                    reject('Choice IDs and labels must be distinct.')
                ids.add(cid)
                labels.add(label)
            if not isinstance(item['answer'], str) or item['answer'] not in ids:
                reject('The answer must reference an offered choice ID.')
    return pack
