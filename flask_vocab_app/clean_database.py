from pathlib import Path
import sqlite3
import logging
import json
import pymorphy3
from wordfreq import word_frequency

logging.basicConfig(filename='/tmp/flask_vocab_app.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

def clean_database(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        morph = pymorphy3.MorphAnalyzer()

        # Find duplicates
        cursor.execute("""
            SELECT lemma, COUNT(*) as cnt
            FROM words
            GROUP BY lemma
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()
        logger.info(f"Found {len(duplicates)} lemmas with duplicates")

        for lemma, count in duplicates:
            cursor.execute("SELECT id, pos FROM words WHERE lemma = ? ORDER BY id", (lemma,))
            rows = cursor.fetchall()
            keep_id = rows[0][0]
            delete_ids = [row[0] for row in rows[1:]]
            keep_pos = rows[0][1]

            # Update forms
            cursor.execute("""
                UPDATE forms
                SET word_id = ?
                WHERE word_id IN (""" + ",".join("?" * len(delete_ids)) + """)
            """, [keep_id] + delete_ids)

            # Delete duplicates
            cursor.execute("""
                DELETE FROM words
                WHERE id IN (""" + ",".join("?" * len(delete_ids)) + """)
            """, delete_ids)
            logger.info(f"Deduplicated '{lemma}': kept id={keep_id}, pos={keep_pos}, deleted ids={delete_ids}")

        # Reprocess adjectives
        cursor.execute("SELECT id, lemma, pos FROM words WHERE pos IN ('ADJ', 'PART')")
        words = cursor.fetchall()
        for word_id, lemma, pos in words:
            parses = morph.parse(lemma)
            scored_parses = []
            for parse in parses:
                if parse.normal_form != lemma:
                    continue
                pos_tag = parse.tag.POS
                if not pos_tag:
                    continue
                freq = word_frequency(parse.word, 'ru')
                score = parse.score + (freq * 1e6 if freq > 0 else 0)
                if pos_tag in ('ADJF', 'ADJS') and lemma.endswith(('ый', 'ий', 'ая', 'ое', 'ие')):
                    score += 0.5
                if pos_tag in ('PRTF', 'PRTS') and not lemma.endswith(('вший', 'щий')):
                    score -= 0.3
                scored_parses.append((parse, pos_tag, score))

            if not scored_parses:
                continue

            scored_parses.sort(key=lambda x: x[2], reverse=True)
            parsed, pos_tag, _ = scored_parses[0]
            new_pos = {'ADJF': 'ADJ', 'ADJS': 'ADJ', 'PRTF': 'PART', 'PRTS': 'PART'}.get(pos_tag, pos)

            if new_pos != pos:
                cursor.execute("UPDATE words SET pos = ? WHERE id = ?", (new_pos, word_id))
                cursor.execute("DELETE FROM forms WHERE word_id = ?", (word_id))
                logger.info(f"Corrected POS for '{lemma}' from {pos} to {new_pos}")

                forms = set()
                valid_adj_cases = {'nomn', 'gent', 'datv', 'accs', 'ablt', 'loct'}
                for form in parsed.lexeme:
                    if not form.word or form.tag.POS not in ('ADJF', 'ADJS'):
                        continue
                    tags = {}
                    if form.tag.case in valid_adj_cases:
                        tags["case"] = form.tag.case
                    if form.tag.number:
                        tags["number"] = form.tag.number
                    if form.tag.gender and form.tag.number == 'sing':
                        tags["gender"] = form.tag.gender
                    if hasattr(form.tag, "degree") and form.tag.degree:
                        tags["degree"] = form.tag.degree
                    forms.add((form.word, json.dumps(tags, sort_keys=True)))

                for form, tags in forms:
                    cursor.execute("""
                        INSERT INTO forms (word_id, form, count, tags)
                        VALUES (?, ?, ?, ?)
                    """, (word_id, form, 0, tags))
                logger.info(f"Added {len(forms)} forms for '{lemma}'")

        conn.commit()
        logger.info("Database cleanup completed")
    except sqlite3.Error as e:
        logger.error(f"Cleanup error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = str(Path(__file__).resolve().parents[1] / 'flask_vocab_app/vocab.db')
    clean_database(db_path)