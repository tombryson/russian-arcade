from pathlib import Path
import sqlite3
import json
import logging
import openai
from openai import OpenAI
import time
from typing import List, Optional, Dict
from config import OPENAI_API_KEY, YANDEX_API_KEY, ELEVENLABS_API_KEY, ANKI_CONNECT_URL, OPENAI_MODEL_HIGH

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/assign_mnemonic.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def assign_mnemonics_batch(words: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Assign a mnemonic to a batch of words using the configured high-capability model.
    Returns a dict of word: mnemonic or None on failure.
    """
    # Build prompt with all words
    word_list = "\n".join([f"- {word['lemma']} (part of speech: {word['pos']})" for word in words])
    prompt = (
        f"You are a Russian language learning expert. Create a short, memorable English mnemonic for each Russian word below "
        f"to help learners recall the word by linking its pronunciation to its meaning. "
        f"The mnemonic must be a concise phrase (max 12 words) that: "
        f"1. Includes the Russian word or a close phonetic approximation (e.g., 'Go-lad' for 'голод'). "
        f"2. Uses vivid, concrete imagery tied to a real-world or cultural scenario (e.g., a shopping card for 'карточка'). "
        f"3. Matches the part of speech (verbs for actions, nouns for objects, adjectives for descriptions). "
        f"4. Avoids generic or abstract phrases. "
        f"Return only a JSON object with each word as a key and a mnemonic string as the value, e.g:\n"
        "{\n"
        "  \"голод\": \"Go-lad - you're hungry!\",\n"
        "  \"карточка\": \"Kart-och-ka, a tiny shopping cart card - карточка gives me 10% off!\"\n"
        "}\n"
        "Do not include extra text or markdown outside the JSON object.\n\n"
        "Words:\n" + word_list
    )
    logger.debug(f"Prompt for batch of {len(words)} words: {prompt}")

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL_HIGH,
                messages=[
                    {"role": "system", "content": "You are a precise mnemonic generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            raw_content = response.choices[0].message.content.strip()
            # Strip markdown code blocks
            if raw_content.startswith('```json'):
                raw_content = raw_content[7:].rstrip('```').strip()
            elif raw_content.startswith('```'):
                raw_content = raw_content[3:].rstrip('```').strip()
            logger.debug(f"Cleaned API response: {raw_content}")
            result = json.loads(raw_content)
            if not isinstance(result, dict):
                logger.warning(f"Invalid response format, not a dict: {raw_content}")
                return None
            # Validate response includes all words
            if set(word['lemma'] for word in words) != set(result.keys()):
                logger.warning(f"Response missing lemmas: {raw_content}")
                return None
            valid_result = {}
            skipped_lemmas = []
            for lemma, mnemonic in result.items():
                if isinstance(mnemonic, str) and mnemonic.strip() and len(mnemonic.split()) <= 7:
                    valid_result[lemma] = mnemonic
                else:
                    skipped_lemmas.append(lemma)
                    logger.warning(f"Invalid mnemonic for {lemma}: {mnemonic} (length: {len(mnemonic.split()) if isinstance(mnemonic, str) else 'N/A'})")
            if skipped_lemmas:
                with open(str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/skipped_mnemonic.txt'), 'a') as f:
                    f.write(f"Batch at {time.ctime()}: {', '.join(skipped_lemmas)}\n")
            if valid_result:
                logger.debug(f"Valid mnemonics for batch: {valid_result}")
                return valid_result
            # Fallback: Assign default mnemonic
            logger.warning(f"No valid mnemonics in batch, assigning defaults")
            default_result = {}
            for word in words:
                lemma = word['lemma']
                default_result[lemma] = f"Recall {lemma} phonetically."
                logger.info(f"Assigned default mnemonic for {lemma}: {default_result[lemma]}")
            with open(str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/skipped_mnemonic.txt'), 'a') as f:
                f.write(f"Default batch at {time.ctime()}: {', '.join(default_result.keys())}\n")
            return default_result
        except (openai.APIError, json.JSONDecodeError) as e:
            logger.error(f"Attempt {attempt + 1} failed for batch: {str(e)}, raw response: {raw_content if 'raw_content' in locals() else 'N/A'}")
            time.sleep(2 ** attempt)  # Exponential backoff
    logger.error(f"All attempts failed for batch, assigning defaults")
    default_result = {}
    for word in words:
        lemma = word['lemma']
        default_result[lemma] = f"Recall {lemma} phonetically."
        logger.info(f"Assigned default mnemonic for {lemma}: {default_result[lemma]}")
    with open(str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/skipped_mnemonic.txt'), 'a') as f:
        f.write(f"Default batch at {time.ctime()}: {', '.join(default_result.keys())}\n")
    return default_result

def main():
    """Process words table in batches and assign mnemonics."""
    db_path = str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/vocab.db')
    batch_size = 25
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM words WHERE mnemonic IS NULL")
        total_remaining = cursor.fetchone()[0]
        logger.info(f"Found {total_remaining} lemmas to process")

        while total_remaining > 0:
            cursor.execute("SELECT id, lemma, pos FROM words WHERE mnemonic IS NULL LIMIT ?", (batch_size,))
            words = [{"id": word[0], "lemma": word[1], "pos": word[2]} for word in cursor.fetchall()]
            if not words:
                break

            logger.info(f"Processing batch of {len(words)} lemmas: {', '.join(w['lemma'] for w in words)}")
            mnemonic_assignments = assign_mnemonics_batch(words)
            if mnemonic_assignments:
                for word in words:
                    lemma = word["lemma"]
                    if lemma in mnemonic_assignments:
                        mnemonic = mnemonic_assignments[lemma]
                        cursor.execute(
                            "UPDATE words SET mnemonic = ? WHERE id = ?",
                            (mnemonic, word["id"])
                        )
                        logger.info(f"Updated {lemma} with mnemonic: {mnemonic}")
                    else:
                        logger.warning(f"No mnemonic assigned for {lemma}")
                conn.commit()
                logger.info(f"Committed batch of {len(words)} updates")
            else:
                logger.warning(f"Batch failed, skipping lemmas: {', '.join(w['lemma'] for w in words)}")
                with open(str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/skipped_mnemonic.txt'), 'a') as f:
                    f.write(f"Batch at {time.ctime()}: {', '.join(w['lemma'] for w in words)}")
                # Continue to next batch even if failed

            cursor.execute("SELECT COUNT(*) FROM words WHERE mnemonic IS NULL")
            total_remaining = cursor.fetchone()[0]
            logger.info(f"Remaining lemmas to process: {total_remaining}")

    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main()
