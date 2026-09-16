import os
import json
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, YANDEX_API_KEY, ELEVENLABS_API_KEY, ANKI_CONNECT_URL, OPENAI_MODEL_FAST

# Setup logging to file and console
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("./openai_topic_test.log"),  # Changed to current directory
        logging.StreamHandler()  # Print to console
    ]
)
logger = logging.getLogger("OpenAITest")

# Load OpenAI API key
api_key = OPENAI_API_KEY
if not api_key:
    logger.error("OPENAI_API_KEY not set in environment")
    raise ValueError("OPENAI_API_KEY not set")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Define topics
TOPICS = [
    "greetings", "numbers", "family", "home", "food", "daily_activities", "colors",
    "clothing", "places", "weather", "shopping", "travel", "restaurant", "body",
    "school", "hobbies", "animals", "nature", "jobs", "review", "offer", "review",
    "office", "future", "work", "history", "education", "health", "tourism",
    "cuisine", "fashion", "development", "literature", "politics", "government",
    "religion", "law", "science", "philosophy"
]

# Test words
words = [
    {"lemm": "остановить", "pos": "VERB"},
    {"lemm": "подкова", "pos": "NOUN"},
    {"lemm": "сквозь", "pos": "PREP"}
]

def test_topic_assignment(words):
    logger.debug(f"Testing topic assignment for {len(words)} words")
    word_list = "\n".join([f"{word['lemm']} ({word['pos']})" for word in words])
    # Simplified prompt
    prompt = (
        f"Assign 1-2 topics to each Russian word below from this list: "
        f"{', '.join(TOPICS)}. "
        f"Return a JSON object, e.g., {{'word': ['topic1', 'topic2']}}. "
        f"Words: {word_list}"
    )

    try:
        logger.debug(f"Sending request with prompt: {prompt}")
        response = client.chat.completions.create(
            model=OPENAI_MODEL_FAST,
            messages=[
                {"role": "system", "content": "You are a topic classifier."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=500
        )

        # Log full response
        logger.debug(f"Full response: {response.to_dict()}")

        # Raw response content
        raw_content = response.choices[0].message.content
        logger.debug(f"Raw response content: {raw_content}")

        # Parse JSON
        result = json.loads(raw_content.strip())
        logger.debug(f"Parsed JSON: {result}")

        # Validate topics
        valid_result = {}
        for lemma, topics in result.items():
            if isinstance(topics, list) and all(t in TOPICS for t in topics) and 1 <= len(topics) <= 2:
                valid_result[lemma] = topics
            else:
                logger.warning(f"Invalid topics for '{lemma}': {topics}")

        logger.info(f"Assigned topics: {valid_result}")
        return valid_result

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        logger.error(f"Raw content: {raw_content}")
        return None
    except Exception as e:
        logger.error(f"OpenAI error: {str(e)}")
        return None

if __name__ == "__main__":
    result = test_topic_assignment(words)
    print("Test result:", result)
