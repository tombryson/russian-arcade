from pathlib import Path
import sqlite3
import json
import logging
import openai
from openai import OpenAI
import time
from typing import List, Optional, Dict
from config import OPENAI_API_KEY, YANDEX_API_KEY, ELEVENLABS_API_KEY, ANKI_CONNECT_URL

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/assign_topics.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# List of 51 topics, including "grammar"
TOPICS = [
    "greetings", "numbers", "family", "home", "food", "daily_activities", "colors", "clothing",
    "places", "weather", "shopping", "travel", "restaurant", "body", "school", "hobbies",
    "animals", "nature", "jobs", "holidays", "city", "technology", "environment", "sports",
    "music", "feelings", "news", "housekeeping", "social", "history", "work", "education",
    "health", "tourism", "cuisine", "fashion", "literature", "politics", "economy", "religion",
    "law", "science", "philosophy", "psychology", "sociology", "architecture", "cinema",
    "global_issues", "linguistics", "russian_culture", "grammar"
]

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def assign_topics_batch(words: List[Dict[str, str]]) -> Optional[Dict[str, List[str]]]:
    """
    Assign 1-3 topics to a batch of words using gpt-4o-mini.
    Returns a dict of word: topics or None on failure.
    """
    # Build prompt with all words
    word_list = "\n".join([f"- {word['lemma']} (part of speech: {word['pos']})" for word in words])
    prompt = (
        f"You are a Russian language expert. Assign 1-3 topics to each Russian word below "
        f"from this exact list only:\n```\n{', '.join(TOPICS)}\n```\n"
        "Use only the topics listed above, verbatim, without synonyms or related terms "
        "(e.g., do not use 'kitchen' for 'food', 'language' for 'linguistics', 'months' for 'time', 'art' for 'culture'). "
        "For pronouns, prepositions, conjunctions, and adverbs, prioritize 'grammar' unless a specific thematic topic applies "
        "(e.g., 'привет' to 'greetings'). For nouns, verbs, and adjectives, assign thematic topics based on natural contexts for language learning, "
        "e.g., 'гулять' (VERB) to 'daily_activities', 'красивый' (ADJ) to 'colors' or 'feelings'. "
        "Return only a JSON object with each word as a key and a topic array as the value, e.g:\n"
        "{\n"
        "  \"песок\": [\"places\"],\n"
        "  \"море\": [\"places\", \"nature\"],\n"
        "  \"что\": [\"grammar\"],\n"
        "  \"гулять\": [\"daily_activities\"],\n"
        "  \"красивый\": [\"colors\", \"feelings\"],\n"
        "  \"сестра\": [\"family\"],\n"
        "  \"итак\": [\"grammar\"]\n"
        "}\n"
        "Do not include any extra text or explanations outside the JSON object.\n\n"
        "Words:\n" + word_list
    )
    logger.debug(f"Prompt for batch of {len(words)} words")

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise topic classifier."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lowered for precision
                max_tokens=1000
            )
            raw_content = response.choices[0].message.content.strip()
            logger.debug(f"Raw API response: {raw_content}")
            result = json.loads(raw_content)
            if not isinstance(result, dict):
                logger.warning(f"Invalid response format, not a dict: {raw_content}")
                return None
            # Validate response includes all words
            if set(word['lemma'] for word in words) != set(result.keys()):
                logger.warning(f"Response missing lemmas: {raw_content}")
                return None
            # Filter valid topics
            valid_result = {}
            skipped_lemmas = []
            for lemma, topics in result.items():
                if isinstance(topics, list) and all(t in TOPICS for t in topics) and 1 <= len(topics) <= 3:
                    valid_result[lemma] = topics
                else:
                    skipped_lemmas.append(lemma)
                    logger.warning(f"Invalid topics for {lemma}: {topics}")
            if skipped_lemmas:
                with open(str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/skipped_lemmas.txt'), 'a') as f:
                    f.write(f"Batch at {time.ctime()}: {', '.join(skipped_lemmas)}\n")
            if valid_result:
                logger.debug(f"Valid topics for batch: {valid_result}")
                return valid_result
            # Fallback: Assign default topics
            logger.warning(f"No valid topics in batch, assigning defaults")
            default_result = {}
            for word in words:
                lemma, pos = word['lemma'], word['pos']
                if pos in ('PRON', 'PREP', 'CONJ', 'ADVB'):
                    default_result[lemma] = ["grammar"]
                elif pos in ('VERB', 'INFN'):
                    default_result[lemma] = ["daily_activities"]
                elif pos == 'ADJ':
                    default_result[lemma] = ["feelings"]
                else:
                    default_result[lemma] = ["daily_activities"]  # Fallback for nouns, etc.
                logger.info(f"Assigned default topic for {lemma}: {default_result[lemma]}")
            with open(str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/skipped_lemmas.txt'), 'a') as f:
                f.write(f"Default batch at {time.ctime()}: {', '.join(default_result.keys())}\n")
            return default_result
        except (openai.APIError, json.JSONDecodeError) as e:
            logger.error(f"Attempt {attempt + 1} failed for batch: {str(e)}, raw response: {raw_content if 'raw_content' in locals() else 'N/A'}")
            time.sleep(2 ** attempt)  # Exponential backoff
    logger.error(f"All attempts failed for batch, assigning defaults")
    default_result = {}
    for word in words:
        lemma, pos = word['lemma'], word['pos']
        if pos in ('PRON', 'PREP', 'CONJ', 'ADVB'):
            default_result[lemma] = ["grammar"]
        elif pos in ('VERB', 'INFN'):
            default_result[lemma] = ["daily_activities"]
        elif pos == 'ADJ':
            default_result[lemma] = ["feelings"]
        else:
            default_result[lemma] = ["daily_activities"]
        logger.info(f"Assigned default topic for {lemma}: {default_result[lemma]}")
    with open(str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/skipped_lemmas.txt'), 'a') as f:
        f.write(f"Default batch at {time.ctime()}: {', '.join(default_result.keys())}\n")
    return default_result

def main():
    """Process words table in batches and assign topics."""
    db_path = str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/vocab.db')
    batch_size = 25
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM words WHERE topic IS NULL")
        total_remaining = cursor.fetchone()[0]
        logger.info(f"Found {total_remaining} lemmas to process")

        while total_remaining > 0:
            cursor.execute("SELECT id, lemma, pos FROM words WHERE topic IS NULL LIMIT ?", (batch_size,))
            words = [{"id": row[0], "lemma": row[1], "pos": row[2]} for row in cursor.fetchall()]
            if not words:
                break

            logger.info(f"Processing batch of {len(words)} lemmas: {', '.join(w['lemma'] for w in words)}")
            topic_assignments = assign_topics_batch(words)
            if topic_assignments:
                for word in words:
                    lemma = word["lemma"]
                    if lemma in topic_assignments:
                        topic_json = json.dumps(topic_assignments[lemma])
                        cursor.execute(
                            "UPDATE words SET topic = ? WHERE id = ?",
                            (topic_json, word["id"])
                        )
                        logger.info(f"Updated {lemma} with topics: {topic_json}")
                    else:
                        logger.warning(f"No topics assigned for {lemma}")
                conn.commit()
                logger.info(f"Committed batch of {len(words)} updates")
            else:
                logger.warning(f"Batch failed, skipping lemmas: {', '.join(w['lemma'] for w in words)}")
                with open(str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/skipped_lemmas.txt'), 'a') as f:
                    f.write(f"Batch at {time.ctime()}: {', '.join(w['lemma'] for w in words)}\n")

            cursor.execute("SELECT COUNT(*) FROM words WHERE topic IS NULL")
            total_remaining = cursor.fetchone()[0]
            logger.info(f"Remaining lemmas to process: {total_remaining}")

    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main()