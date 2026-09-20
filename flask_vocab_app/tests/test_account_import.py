import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from contracts.flashcards import objective
from migrations import upgrade_database
from services.account_import import ImportConflict, _allocate, build_account_import, digest


class AccountImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.local, self.hosted, self.output = [self.root / name for name in ('local.db', 'hosted.db', 'merged.db')]
        for path in (self.local, self.hosted):
            upgrade_database(path, backup=False)
        with sqlite3.connect(self.local) as conn:
            conn.execute("UPDATE learning_profiles SET study_timezone='Australia/Melbourne' WHERE id='personal-learning'")
            conn.execute("INSERT INTO words(id,lemma,pos,lemma_difficulty,mnemonic) VALUES (1,'кот','NOUN',1,'local cat'),(2,'письмо','NOUN',1,'local letter')")
            conn.execute("INSERT INTO forms(id,word_id,form,tags) VALUES (1,1,'кот','{}'),(20,2,'письмо','{}')")
            self.add_writing(conn, 1, 'Local draft', 'Мой черновик')
            self.add_writing(conn, 2, 'Another local draft', None)
            conn.execute("INSERT INTO household_access VALUES ('never-copy-local-access','personal-learning',100,200)")
            conn.execute("INSERT INTO household_settings VALUES (1,'Local household','never-copy-pin',0,0,1)")
            conn.execute("UPDATE profile_onboarding SET coins_introduced_at=10,progress_introduced_at=20 WHERE profile_id='personal-learning'")
        with sqlite3.connect(self.hosted) as conn:
            conn.execute("UPDATE learning_profiles SET display_name='tombryson' WHERE id='personal-learning'")
            conn.execute("INSERT INTO words(id,lemma,pos,lemma_difficulty,mnemonic) VALUES (1,'письмо','NOUN',1,'hosted letter'),(2,'чай','NOUN',1,'hosted tea')")
            conn.execute("INSERT INTO forms(id,word_id,form,tags) VALUES (1,1,'письмо','{}'),(2,2,'чай','{}')")
            self.add_writing(conn, 1, 'Hosted draft', 'Мой новый текст')
            conn.execute("INSERT INTO household_access VALUES ('never-copy-hosted-access','personal-learning',100,200)")
            conn.execute("UPDATE profile_onboarding SET coins_introduced_at=30,progress_introduced_at=NULL WHERE profile_id='personal-learning'")
            self.card = dict(id='item', card_id='hosted-card', word_id=1, form_id=1,
                             type='cloze', direction='ru-cloze', sense_key='letter-use',
                             sense_label='A letter', context='Это письмо.',
                             prompt='Это [[blank]].', answer='письмо', context_meaning='This is a letter.')
            pack = dict(schema_version=2, id='hosted-deck', kind='deck', title='Hosted deck', source='test', items=[self.card])
            conn.execute("INSERT INTO learning_content VALUES ('hosted-deck','deck',1)")
            conn.execute("INSERT INTO learning_content_versions(id,content_id,version,title,payload,source,created_at) VALUES ('hosted-version','hosted-deck',1,'Hosted deck',?,'test',1)", (json.dumps(pack),))
            conn.execute("INSERT INTO card_definitions(id,word_id,form_id,retrieval_mode,sense_key,sibling_key,objective_hash,created_at) VALUES ('hosted-card',1,1,'ru-cloze','letter-use','word:1',?,1)", (objective(self.card),))
            conn.execute("INSERT INTO card_versions VALUES ('hosted-card-version','hosted-card','hosted-version','item')")
            conn.execute("INSERT INTO learning_content_words VALUES ('hosted-version','item',1)")

    @staticmethod
    def add_writing(conn, identifier, title, response):
        conn.execute("INSERT INTO writing_exercises(id,topic,difficulty,task,required_words,min_words,user_response,created_at,owner_profile_id) VALUES (?,'home','A1',?,'[]',30,?,'2026-09-19','personal-learning')", (identifier, title, response))
        conn.execute('INSERT INTO writing_details VALUES (?,?,?,?)', (identifier, title, title, title))
        if response:
            conn.execute("INSERT INTO writing_drafts VALUES (?,?,1,'2026-09-19')", (identifier, response))

    def test_merge_preserves_hosted_urls_local_drafts_and_card_relations(self):
        before = (digest(self.local), digest(self.hosted))
        report = build_account_import(self.local, self.hosted, self.output)
        self.assertEqual(before, (digest(self.local), digest(self.hosted)))
        self.assertEqual(report['local_id_mappings']['writing_exercises'], {'1': 3})
        with sqlite3.connect(self.output) as conn:
            self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertEqual(conn.execute('SELECT id,task FROM writing_exercises ORDER BY id').fetchall(),
                             [(1, 'Hosted draft'), (2, 'Another local draft'), (3, 'Local draft')])
            self.assertEqual(conn.execute('SELECT exercise_id,response FROM writing_drafts ORDER BY exercise_id').fetchall(),
                             [(1, 'Мой новый текст'), (3, 'Мой черновик')])
            self.assertEqual(conn.execute('SELECT word_id,form_id,sibling_key FROM card_definitions').fetchone(), (2, 20, 'word:2'))
            item = json.loads(conn.execute('SELECT payload FROM learning_content_versions').fetchone()[0])['items'][0]
            self.assertEqual((item['word_id'], item['form_id']), (2, 20))
            self.assertEqual(conn.execute('SELECT objective_hash FROM card_definitions').fetchone()[0], objective(item))
            self.assertEqual(conn.execute('SELECT word_id FROM learning_content_words').fetchone()[0], 2)
            self.assertEqual(conn.execute('SELECT count(*) FROM words').fetchone()[0], 3)
            self.assertEqual(conn.execute('SELECT count(*) FROM forms').fetchone()[0], 3)
            self.assertEqual(conn.execute("SELECT display_name,study_timezone FROM learning_profiles WHERE id='personal-learning'").fetchone(), ('tombryson', 'Australia/Melbourne'))
            self.assertEqual(conn.execute("SELECT coins_introduced_at,progress_introduced_at FROM profile_onboarding WHERE profile_id='personal-learning'").fetchone(), (10, 20))
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'Content versions are immutable'):
                conn.execute("UPDATE learning_content_versions SET payload='{}'")

    def test_credentials_are_excluded_and_alternate_mnemonics_are_preserved(self):
        build_account_import(self.local, self.hosted, self.output)
        with sqlite3.connect(self.output) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM household_access').fetchone()[0], 0)
            self.assertEqual(conn.execute('SELECT count(*) FROM household_settings').fetchone()[0], 0)
            local, hosted = conn.execute("SELECT local_row_json,hosted_row_json FROM account_import_archive WHERE table_name='words'").fetchone()
            self.assertEqual(json.loads(local)['mnemonic'], 'local letter')
            self.assertEqual(json.loads(hosted)['mnemonic'], 'hosted letter')

    def test_unsupported_hosted_progress_aborts_without_output(self):
        with sqlite3.connect(self.hosted) as conn:
            conn.execute("INSERT INTO progression_preferences VALUES ('personal-learning','B2')")
        with self.assertRaisesRegex(ImportConflict, 'additional merge policy: progression_preferences'):
            build_account_import(self.local, self.hosted, self.output)
        self.assertFalse(self.output.exists())

    def test_conflicting_content_identity_aborts_instead_of_overwriting(self):
        with sqlite3.connect(self.local) as conn:
            conn.execute("INSERT INTO learning_content VALUES ('hosted-deck','activity',1)")
        with self.assertRaisesRegex(ImportConflict, 'Conflicting learning_content record'):
            build_account_import(self.local, self.hosted, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_output_is_never_replaced(self):
        self.output.write_bytes(b'previous artifact')
        with self.assertRaisesRegex(ImportConflict, 'Output must be a new file'):
            build_account_import(self.local, self.hosted, self.output)
        self.assertEqual(self.output.read_bytes(), b'previous artifact')

    def test_independent_legacy_balances_require_review(self):
        with sqlite3.connect(self.hosted) as conn:
            conn.execute('UPDATE users SET lingocoins=8')
        with self.assertRaisesRegex(ImportConflict, 'Conflicting users record'):
            build_account_import(self.local, self.hosted, self.output)
        self.assertFalse(self.output.exists())

    def test_ambiguous_lemma_and_part_of_speech_is_not_guessed(self):
        existing = [{'id': 1, 'lemma': 'замок', 'pos': 'NOUN'},
                    {'id': 2, 'lemma': 'замок', 'pos': 'NOUN'}]
        incoming = [{'id': 3, 'lemma': 'замок', 'pos': 'NOUN'}]
        with self.assertRaisesRegex(ImportConflict, 'Ambiguous words natural key'):
            _allocate(existing, incoming, 'words', natural=('lemma', 'pos'))

    def test_same_spelling_with_different_part_of_speech_stays_separate(self):
        existing = [{'id': 1, 'lemma': 'печь', 'pos': 'NOUN'}]
        incoming = [{'id': 1, 'lemma': 'печь', 'pos': 'INFN'}]
        self.assertEqual(_allocate(existing, incoming, 'words', natural=('lemma', 'pos')), {1: 2})


if __name__ == '__main__':
    unittest.main()
