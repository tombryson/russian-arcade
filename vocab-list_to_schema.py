from pathlib import Path
import pymorphy2
import sqlite3
import json
import math
from wordfreq import word_frequency
import logging

# Set up logging
logging.basicConfig(filename='vocab-list_to_schema.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the morphological analyzer
morph = pymorphy2.MorphAnalyzer()

# Load vocab list from file
try:
    with open("vocab-list.txt", "r", encoding="utf-8") as f:
        words = [line.strip().lower() for line in f if line.strip()]
except FileNotFoundError:
    logging.error("vocab-list.txt not found")
    print("Error: vocab-list.txt not found")
    exit(1)

# Connect to SQLite database
try:
    conn = sqlite3.connect(str(Path(__file__).resolve().parent / 'vocab.db'))
    cursor = conn.cursor()
except sqlite3.Error as e:
    logging.error(f"Failed to connect to database: {str(e)}")
    print(f"Error: Failed to connect to database: {str(e)}")
    exit(1)

# Create tables with unique constraint
cursor.executescript("""
    DROP TABLE IF EXISTS forms;
    DROP TABLE IF EXISTS words;
    CREATE TABLE words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lemma TEXT NOT NULL,
        pos TEXT NOT NULL,
        count INTEGER DEFAULT 0,
        difficulty INTEGER NOT NULL,
        UNIQUE(lemma, pos)
    );
    CREATE TABLE forms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        form TEXT NOT NULL,
        count INTEGER DEFAULT 0,
        tags JSON NOT NULL,
        FOREIGN KEY (word_id) REFERENCES words(id),
        UNIQUE(word_id, form, tags)
    );
""")

# POS mapping (English labels, complete)
pos_map = {
    'NOUN': 'NOUN',
    'VERB': 'VERB',
    'INFN': 'VERB',
    'ADJF': 'ADJ',
    'ADJS': 'ADJ',
    'PRTF': 'PART',
    'PRTS': 'PART',
    'ADVB': 'ADVB',
    'NUMR': 'NUMR',
    'NPRO': 'NPRO',
    'CONJ': 'CONJ',
    'COMP': 'COMP',
    'PRCL': 'PART',
    'PRED': 'PRED',
    'PREP': 'PREP',
    'UNKN': 'PRED'  # Handle надо
}

# Valid noun cases (exclude vocative)
valid_noun_cases = {'nomn', 'gent', 'datv', 'accs', 'ablt', 'loct'}
max_noun_forms = 12
freq_threshold = 6e-7
participle_freq_threshold = 2e-6

# Process words and insert into database
for word in set(words):
    try:
        parses = morph.parse(word)
        parsed = next(
            (p for p in parses if p.normal_form == word and p.tag.POS == 'NOUN'),
            next((p for p in parses if p.normal_form == word), parses[0])
        )
        lemma = parsed.normal_form
        pos = pos_map.get(parsed.tag.POS, 'OTHER')
        if lemma == 'надо':
            pos = 'PRED'

        cursor.execute(
            "SELECT id FROM words WHERE lemma = ? AND pos = ?",
            (lemma, pos)
        )
        existing = cursor.fetchone()
        if existing:
            logging.info(f"Skipping duplicate lemma '{lemma}' with POS '{pos}'")
            print(f"Skipping duplicate lemma '{lemma}' with POS '{pos}'")
            continue

        forms = set()
        form_count = 0
        for form in parsed.lexeme:
            if not form.word:
                continue
            tags = {}
            try:
                freq = word_frequency(form.word, 'ru')
                # Frequency filters
                if form.tag.POS in ('PRTF', 'PRTS') and freq < participle_freq_threshold:
                    logging.info(f"Skipping low-frequency participle '{form.word}' (POS: {form.tag.POS}, lemma: {lemma}, freq={freq})")
                    print(f"Skipping low-frequency participle '{form.word}' (POS: {form.tag.POS}, lemma: {lemma}, freq={freq})")
                    continue
                if form.tag.POS in ('VERB', 'INFN') and freq == 0:
                    logging.info(f"Skipping zero-frequency verb '{form.word}' (POS: {form.tag.POS}, lemma: {lemma}, freq={freq})")
                    print(f"Skipping zero-frequency verb '{form.word}' (POS: {form.tag.POS}, lemma: {lemma}, freq={freq})")
                    continue
                if form.tag.POS in ('ADJF', 'ADJS', 'COMP'):
                    if freq == 0:
                        logging.info(f"Skipping zero-frequency adjective/comparative '{form.word}' (POS: {form.tag.POS}, lemma: {lemma}, freq={freq})")
                        print(f"Skipping zero-frequency adjective/comparative '{form.word}' (POS: {form.tag.POS}, lemma: {lemma}, freq={freq})")
                        continue
                if form.tag.POS in ('ADJF', 'ADJS') and hasattr(form.tag, 'degree') and form.tag.degree == 'Supr' and freq < 1e-7:
                    logging.info(f"Skipping low-frequency superlative '{form.word}' (POS: {form.tag.POS}, lemma: {lemma}, freq={freq})")
                    print(f"Skipping low-frequency superlative '{form.word}' (POS: {form.tag.POS}, lemma: {lemma}, freq={freq})")
                    continue

                if form.tag.POS == "NOUN":
                    if form.tag.case not in valid_noun_cases:
                        logging.info(f"Skipping invalid case for '{form.word}': {form.tag.case}")
                        print(f"Skipping invalid case for '{form.word}': {form.tag.case}")
                        continue
                    if form.tag.number not in {'sing', 'plur'}:
                        logging.info(f"Skipping invalid number for '{form.word}': {form.tag.number}")
                        print(f"Skipping invalid number for '{form.word}': {form.tag.number}")
                        continue
                    if freq < freq_threshold:
                        logging.info(f"Skipping low-frequency form '{form.word}' (lemma: {lemma}, freq={freq})")
                        print(f"Skipping low-frequency form '{form.word}' (lemma: {lemma}, freq={freq})")
                        continue
                    if form.tag.gender == 'neut' and form.word.endswith('ь') and form.word != lemma:
                        logging.info(f"Skipping invalid neuter form '{form.word}': unexpected soft sign")
                        print(f"Skipping invalid neuter form '{form.word}': unexpected soft sign")
                        continue
                    if form.tag.case:
                        tags["case"] = form.tag.case
                    if form.tag.number:
                        tags["number"] = form.tag.number
                    if form.tag.gender:
                        tags["gender"] = form.tag.gender
                    if form.tag.animacy:
                        tags["animacy"] = form.tag.animacy
                elif form.tag.POS in ("ADJF", "ADJS"):
                    if form.tag.number:
                        tags["number"] = form.tag.number
                    if form.tag.gender and form.tag.number == 'sing':  # Only include gender for singular
                        tags["gender"] = form.tag.gender
                    if hasattr(form.tag, "degree") and form.tag.degree:
                        tags["degree"] = form.tag.degree
                elif form.tag.POS in ("PRTF", "PRTS"):
                    if form.tag.number:
                        tags["number"] = form.tag.number
                    if form.tag.gender and form.tag.number == 'sing':
                        tags["gender"] = form.tag.gender
                    if form.tag.tense:
                        tags["tense"] = form.tag.tense
                    if form.tag.voice:
                        tags["voice"] = form.tag.voice
                    tags["pos"] = "participle"
                elif form.tag.POS in ("VERB", "INFN", "GRND"):
                    if form.tag.tense:
                        tags["tense"] = form.tag.tense
                    if form.tag.aspect:
                        tags["aspect"] = form.tag.aspect
                    if form.tag.mood:
                        tags["mood"] = form.tag.mood
                    if form.tag.person:
                        tags["person"] = form.tag.person
                    if form.tag.number:
                        tags["number"] = form.tag.number
                elif form.tag.POS == "COMP":
                    tags["degree"] = "comp"
                elif form.tag.POS == "ADVB":
                    tags["pos"] = "adverb"
                    if hasattr(form.tag, "degree") and form.tag.degree:
                        tags["degree"] = form.tag.degree
                elif form.tag.POS == "PREP":
                    tags["pos"] = "preposition"
                elif form.tag.POS == "CONJ":
                    tags["pos"] = "conjunction"
                elif form.tag.POS in ("PRCL", "PRED"):
                    tags["pos"] = "particle" if form.tag.POS == "PRCL" else "predicative"
                else:
                    tags["pos"] = pos_map.get(form.tag.POS, "other")
                # Normalize tags for deduplication
                dedup_tags = {k: v for k, v in tags.items() if k not in ('animacy', 'case') or form.tag.POS not in ('ADJF', 'ADJS', 'PRTF', 'PRTS')}
                if form.tag.POS in ('ADJF', 'ADJS', 'PRTF', 'PRTS') and 'gender' in dedup_tags and dedup_tags.get('number') == 'plur':
                    del dedup_tags['gender']  # Remove gender for plural forms
                forms.add((form.word, json.dumps(dedup_tags, sort_keys=True)))
                form_count += 1
                if form.tag.POS == "NOUN" and form_count >= max_noun_forms:
                    logging.info(f"Reached max noun forms ({max_noun_forms}) for '{word}', skipping remaining")
                    print(f"Reached max noun forms ({max_noun_forms}) for '{word}', skipping remaining")
                    break
            except AttributeError as e:
                logging.warning(f"Tag error for '{form.word}' in '{word}': {str(e)}")
                print(f"Warning: Tag error for '{form.word}' in '{word}': {str(e)}")
                tags["error"] = "tag_extraction_failed"
                dedup_tags = {k: v for k, v in tags.items() if k not in ('animacy', 'case') or form.tag.POS not in ('ADJF', 'ADJS', 'PRTF', 'PRTS')}
                if form.tag.POS in ('ADJF', 'ADJS', 'PRTF', 'PRTS') and 'gender' in dedup_tags and dedup_tags.get('number') == 'plur':
                    del dedup_tags['gender']
                forms.add((form.word, json.dumps(dedup_tags, sort_keys=True)))

        freq = word_frequency(lemma, 'ru')
        rarity = 5 if freq == 0 else max(1, min(5, round(5 - math.log10(freq * 1e6))))
        rarity_component = (rarity / 5) * 2.5
        length_component = min(2.5, len(lemma) / 4)
        difficulty = round(rarity_component + length_component)
        difficulty = max(1, min(5, difficulty))

        cursor.execute(
            "INSERT OR IGNORE INTO words (lemma, pos, count, difficulty) VALUES (?, ?, ?, ?)",
            (lemma, pos, 0, difficulty)
        )
        cursor.execute("SELECT id FROM words WHERE lemma = ? AND pos = ?", (lemma, pos))
        word_id = cursor.fetchone()[0]

        for form, tags in forms:
            try:
                cursor.execute(
                    "INSERT INTO forms (word_id, form, count, tags) VALUES (?, ?, ?, ?)",
                    (word_id, form, 0, tags)
                )
            except sqlite3.IntegrityError:
                logging.warning(f"Duplicate form '{form}' with tags '{tags}' for lemma '{lemma}'")
                continue
    except Exception as e:
        logging.error(f"Skipping '{word}': {str(e)}")
        print(f"Skipping '{word}': {str(e)}")
        continue

# Commit and close
try:
    conn.commit()
    logging.info("Data written to vocab.db")
    print("Done. Data written to vocab.db")
except sqlite3.Error as e:
    logging.error(f"Failed to save database: {str(e)}")
    print(f"Error: Failed to save database: {str(e)}")
finally:
    conn.close()