from pathlib import Path
import pymorphy2
import sqlite3
from wordfreq import word_frequency

# Initialize pymorphy2
morph = pymorphy2.MorphAnalyzer()

# Connect to database
try:
    conn = sqlite3.connect(str(Path(__file__).resolve().parent / 'vocab.db'))
    cursor = conn.cursor()
except sqlite3.Error as e:
    print(f"Error: Failed to connect to database: {str(e)}")
    exit(1)

# Test forms (expanded list)
test_forms = [
    # Rare participles
    'присаживавшаяся',  # Reflexive, likely < 1e-9
    'улыбавшийся',     # Reflexive, rare
    'спрашивавшийся',  # Reflexive, rare
    # Common participles
    'читающий',        # Active, common
    'пройдёмте',
    'прочитанный',     # Passive, common
    'работающий',      # Active, common
    # Common verbs
    'говорил',         # Past, frequent
    'бежал',           # Past, frequent
    'читал',           # Past, frequent
    'писал',           # Past, frequent
    # Common nouns
    'папа',            # Frequent
    'книга',           # Frequent
    'стол',            # Frequent
    'дом',             # Frequent
    # Other forms
    'быстро',          # Adverb, frequent
    'нельзя',          # Particle, common
    'в',               # Preposition, very frequent
    'надо',            # Predicative, common
    'красивый',        # Adjective, frequent
    'два'             # Numeral, frequent
]

# Frequency and POS tag test
print("\n=== Frequency and POS Tag Test ===")
print(f"{'Form':<20} {'Frequency':<15} {'POS Tag':<30}")
print("-" * 65)
for form in test_forms:
    freq = word_frequency(form, 'ru')
    parse = morph.parse(form)[0]
    pos_tag = str(parse.tag)  # Full tag for clarity
    print(f"{form:<20} {freq:<15.2e} {pos_tag:<30}")

# Participle-specific test
print("\n=== Participle-Specific Test ===")
participle_forms = [
    'присаживавшаяся', 'улыбавшийся', 'спрашивавшийся',  # Rare
    'читающий', 'прочитанный', 'работающий',          # Common
    'идущий', 'написанный', 'смеющийся'               # Mixed
]
print(f"{'Form':<20} {'Frequency':<15} {'Is Participle':<15} {'Tags':<30}")
print("-" * 80)
for form in participle_forms:
    freq = word_frequency(form, 'ru')
    parse = morph.parse(form)[0]
    is_participle = parse.tag.POS in ('PRTF', 'PRTS')
    tags = str(parse.tag)
    print(f"{form:<20} {freq:<15.2e} {str(is_participle):<15} {tags:<30}")

# Database participle stats
print("\n=== Database Participle Stats ===")
try:
    # Count PRTF/PRTS forms
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM forms f
        WHERE f.tags LIKE '%"PRTF"%' OR f.tags LIKE '%"PRTS"%'
    """)
    total_participles = cursor.fetchone()[0]
    print(f"Total participle forms (PRTF/PRTS): {total_participles}")

    # Sample participle forms
    cursor.execute("""
        SELECT f.form, f.tags, w.lemma
        FROM forms f
        JOIN words w ON f.word_id = w.id
        WHERE f.tags LIKE '%"PRTF"%' OR f.tags LIKE '%"PRTS"%'
        LIMIT 10
    """)
    print("\nSample participle forms:")
    print(f"{'Form':<20} {'Lemma':<20} {'Tags':<30}")
    print("-" * 70)
    for row in cursor.fetchall():
        print(f"{row[0]:<20} {row[2]:<20} {row[1]:<30}")

    # Frequency stats for participles
    cursor.execute("""
        SELECT f.form
        FROM forms f
        WHERE f.tags LIKE '%"PRTF"%' OR f.tags LIKE '%"PRTS"%'
    """)
    participle_freqs = [word_frequency(row[0], 'ru') for row in cursor.fetchall()]
    if participle_freqs:
        avg_freq = sum(participle_freqs) / len(participle_freqs)
        min_freq = min(participle_freqs)
        max_freq = max(participle_freqs)
        print(f"\nParticiple frequency stats:")
        print(f"Average frequency: {avg_freq:.2e}")
        print(f"Minimum frequency: {min_freq:.2e}")
        print(f"Maximum frequency: {max_freq:.2e}")
    else:
        print("\nNo participle forms found in database.")
except sqlite3.Error as e:
    print(f"Error querying database: {str(e)}")

# Close database
conn.close()
print("\n=== Tests Complete ===")