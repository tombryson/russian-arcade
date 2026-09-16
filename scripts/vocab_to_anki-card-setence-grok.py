from pathlib import Path
import card_providers as providers
import os
import requests
from openai import OpenAI
import shutil
import logging
import json
import sqlite3
import random
from card_providers import OPENAI_API_KEY as openai_API_key

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# API keys


# Initialize OpenAI client
client = providers.provider().client
logger.info("OpenAI client initialized")

# Anki media directory
media_dir = str(Path.home() / 'Library/Application Support/Anki2/User 1/collection.media')
os.makedirs(media_dir, exist_ok=True)
logger.info(f"Anki media directory ensured: {media_dir}")

# Database connection
db_path = str(Path(__file__).resolve().parents[1] / 'vocab.db')
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    logger.info(f"Connected to database: {db_path}")
except sqlite3.Error as e:
    logger.error(f"Failed to connect to database: {str(e)}")
    exit(1)

# AnkiConnect wrapper
class AnkiConnect:
    def __init__(self):
        self.url = "http://localhost:8765"
        self.ensure_deck("Russian")

    def add_note(self, note):
        payload = {"action": "addNote", "version": 6, "params": {"note": note}}
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"AnkiConnect request failed: {str(e)}")
            return {"error": str(e)}

    def ensure_deck(self, deck_name):
        payload = {"action": "createDeck", "version": 6, "params": {"deck": deck_name}}
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            if response.json()['error'] is None:
                logger.info(f"Deck '{deck_name}' ensured")
            else:
                logger.error(f"Failed to create deck '{deck_name}': {response.json()['error']}")
        except requests.RequestException as e:
            logger.error(f"Failed to ensure deck '{deck_name}': {str(e)}")

anki = AnkiConnect()
logger.info("AnkiConnect initialized")

# Generate sentence
def generate_sentence(russian_word):
    return providers.sentence(russian_word)

# Format cloze with form validation
def format_cloze(sentence, word_id, lemma, sentence_count):
    logger.info(f"Formatting cloze for lemma: {lemma}, word_id: {word_id}, sentence count: {sentence_count}")
    words = sentence.split()
    exact_form = None
    form_tags = None

    # Find a form in the sentence that matches the lemma's forms
    cursor.execute("SELECT form, tags FROM forms WHERE word_id = ?", (word_id,))
    valid_forms = {row[0]: json.loads(row[1]) for row in cursor.fetchall()}
    
    for w in words:
        if w in valid_forms:
            exact_form = w
            form_tags = valid_forms[w]
            break
    
    if exact_form:
        # Create cloze with the exact form
        link = f'<a href="https://en.openrussian.org/ru/{lemma}" target="_blank">{{{{c1::{exact_form}}}}}</a>'
        cloze_sentence = sentence.replace(exact_form, link, 1)
        unique_suffix = f"<!-- cloze{sentence_count + 1} -->"
        cloze_sentence_with_unique = f"{cloze_sentence} {unique_suffix}"
        logger.debug(f"Cloze sentence: {cloze_sentence_with_unique}")
        return cloze_sentence_with_unique, exact_form, form_tags
    else:
        logger.warning(f"No valid form of '{lemma}' found in sentence '{sentence}'")
        return None, None, None

# Get single-word translation in context
def get_word_translation(russian_word, sentence):
    return providers.meaning(russian_word, sentence)

# Translate full sentence
def translate_sentence(text, target_lang="ru-en"):
    return providers.translation(text)

# Generate audio
def generate_audio(sentence, idx):
    return providers.audio(sentence, f"sentence_{idx}.mp3", media_dir)

# Generate image
def generate_image_url(sentence, word):
    return providers.image(sentence, word)

def download_image(image_url, filename):
    return providers.download(image_url, filename, media_dir)

# Format tags for display
def format_tags(tags):
    if not tags:
        return ""
    tag_list = [f"{key}: {value}" for key, value in tags.items()]
    return ", ".join(tag_list)

# Process a batch of words
def process_batch(start_idx, batch_size, max_sentences_per_word):
    logger.info(f"Starting batch processing for words {start_idx} to {start_idx + batch_size - 1}")
    cursor.execute(
        "SELECT id, lemma FROM words WHERE count < ? LIMIT ?",
        (max_sentences_per_word, batch_size)
    )
    batch_words = cursor.fetchall()
    
    for idx, (word_id, lemma) in enumerate(batch_words, start=start_idx):
        logger.info(f"Processing lemma: {lemma} (word_id: {word_id}, index: {idx})")

        sentence = generate_sentence(lemma)
        if sentence is None:
            continue

        cloze_sentence, exact_form, form_tags = format_cloze(sentence, word_id, lemma, cursor.execute("SELECT count FROM words WHERE id = ?", (word_id,)).fetchone()[0])
        if cloze_sentence is None or exact_form is None:
            continue

        word_translation = get_word_translation(lemma, sentence)
        if word_translation is None:
            continue

        sentence_translation = translate_sentence(sentence)
        if sentence_translation is None:
            continue

        audio_file = generate_audio(sentence, idx)
        if audio_file is None:
            audio_file = ""

        image_url = generate_image_url(sentence, lemma)
        image_file = download_image(image_url, f"{idx}_{lemma}_{cursor.execute('SELECT count FROM words WHERE id = ?', (word_id,)).fetchone()[0]}.png") if image_url else ""

        image_tag = f'<img src="{image_file}">' if image_file else ""
        tags_display = format_tags(form_tags)
        note = {
            "deckName": "Russian",
            "modelName": "Cloze",
            "fields": {
                "Text": cloze_sentence,
                "Translation": word_translation,
                "Extra": f"{sentence_translation}<br>{tags_display}<br>{image_tag}<br>[sound:{audio_file}]" if audio_file else f"{sentence_translation}<br>{tags_display}<br>{image_tag}"
            },
            "options": {"allowDuplicate": True}
        }
        try:
            result = anki.add_note(note)
            if result['error'] is not None:
                raise Exception(f"AnkiConnect error: {result['error']}")
            logger.info(f"Successfully added flashcard for {lemma} with note ID: {result['result']}")
            
            # Update counts
            conn.execute("BEGIN")
            conn.execute("UPDATE words SET count = count + 1 WHERE id = ?", (word_id,))
            if exact_form:
                conn.execute("UPDATE forms SET count = count + 1 WHERE word_id = ? AND form = ?", (word_id, exact_form))
            conn.commit()
            logger.debug(f"Updated counts for lemma: {lemma}, form: {exact_form}")
        except Exception as e:
            logger.error(f"Failed to add flashcard for {lemma}: {str(e)}")
            conn.rollback()
    
    return len(batch_words)

# Main loop with batching
logger.info("Starting flashcard generation process")
max_sentences_per_word = 1
batch_size = 5
start_idx = 0

try:
    while True:
        words_processed = process_batch(start_idx, batch_size, max_sentences_per_word)
        if words_processed == 0:
            logger.info("No more words to process.")
            break
        
        start_idx += words_processed
        cursor.execute("SELECT COUNT(*) FROM words WHERE count < ?", (max_sentences_per_word,))
        remaining_words = cursor.fetchone()[0]
        
        if remaining_words > 0:
            user_input = input(f"Queue 5 more cards? ({remaining_words} words remaining) [y/n]: ").strip().lower()
            if user_input == 'y':
                continue
            elif user_input == 'n':
                logger.info("User chose to stop.")
                break
            else:
                logger.warning(f"Invalid input '{user_input}'. Stopping.")
                break
        else:
            logger.info("Processed all words.")
            break
except KeyboardInterrupt:
    logger.info("Process interrupted by user.")
finally:
    conn.close()
    logger.info("Database connection closed.")

logger.info("Flashcard generation process completed")