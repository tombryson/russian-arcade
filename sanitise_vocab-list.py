from pathlib import Path
import pymorphy2
import re
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize pymorphy2
morph = pymorphy2.MorphAnalyzer()

def is_valid_russian_word(word):
    """
    Check if a word is a valid Russian word using pymorphy2 and basic heuristics.
    
    Args:
        word (str): Word to validate.
    
    Returns:
        bool: True if valid, False if nonsense or invalid.
    """
    # Basic checks
    if not word or len(word) < 2:  # Too short
        return False
    if not re.match(r'^[А-Яа-яЁё-]+$', word):  # Non-Russian characters
        return False
    
    try:
        parsed = morph.parse(word)[0]
        # Check if it has a valid part of speech and reasonable score
        if parsed.tag.POS and parsed.score > 0.1:  # Arbitrary threshold for confidence
            return True
        return False
    except Exception:
        return False

def sanitize_vocab_list(input_file, output_file):
    """
    Read vocab_list.txt, remove nonsense words, and save the cleaned list.
    
    Args:
        input_file (str): Path to vocab_list.txt.
        output_file (str): Path to save cleaned list.
    """
    try:
        # Read vocab list
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return
        
        with open(input_file, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(words)} words from {input_file}")
        
        # sanitise words
        valid_words = []
        nonsense_words = []
        for word in words:
            if is_valid_russian_word(word):
                valid_words.append(word)
            else:
                nonsense_words.append(word)
        
        # Log results
        logger.info(f"Found {len(valid_words)} valid words")
        if nonsense_words:
            logger.warning(f"Removed {len(nonsense_words)} nonsense words: {', '.join(nonsense_words)}")
        else:
            logger.info("No nonsense words found")
        
        # Save cleaned list
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(valid_words) + '\n')
        logger.info(f"Saved {len(valid_words)} words to {output_file}")
        
    except Exception as e:
        logger.error(f"Failed to sanitize vocab list: {e}")

if __name__ == "__main__":
    input_file = str(Path(__file__).resolve().parent / 'vocab-list.txt')
    output_file = str(Path(__file__).resolve().parent / 'vocab-list_clean.txt')
    sanitize_vocab_list(input_file, output_file)