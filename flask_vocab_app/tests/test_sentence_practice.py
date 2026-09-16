"""Sentence practice contracts: offline drafts, safe checks, and complete navigation."""
from tests.support import latest_schema_version
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import httpx
import openai

from migrations import upgrade_database
from services.word_jumble_service import WordJumbleService, AssessmentUnavailable, DraftConflict
from tests.support import isolated_app, strip_progression_and_levels
from tests.test_activity_cleanup import Document


class SentencePracticeTests(unittest.TestCase):
    def setUp(self):
        self.service = WordJumbleService.__new__(WordJumbleService)
        self.app = isolated_app(self, {'WordJumbleService': self.service})
        self.service.db_path = self.app.config['DB_PATH']
        self.service.client = Mock()
        self.evaluation = {'score': 3, 'commentary': 'You expressed a clear idea about your family.',
                           'corrections': [], 'polished_sentence': 'Семья идёт в школу.',
                           'phrasing_note': '', 'extension': ''}
        self.service.client.responses.create.return_value = SimpleNamespace(
            status='completed', output_text=json.dumps(self.evaluation))
        self.client = self.app.test_client()
        # These exercise behavior tests submit as the explicitly selected learner.
        self.client.environ_base['HTTP_X_CSRF_TOKEN'] = self.client.get('/api/v1/user-session').json['csrf_token']
        self.game = self.service.create_game('any', 'easy')
        self.id = self.game['id']
        self.url = '/word_jumble/load/' + self.id
        self.headers = {'Accept': 'application/json'}

    def submit(self, kind, text, revision=0, enhanced=True):
        return self.client.post(f'/word_jumble/{kind}/{self.id}',
                                data={'user_response': text, 'revision': revision},
                                headers=self.headers if enhanced else {})

    def test_create_and_resume_without_provider(self):
        response = self.client.post('/word_jumble/create', data={'topic': 'any', 'difficulty': 'easy'})
        self.assertEqual(response.status_code, 303)
        html = self.client.get(response.location).get_data(as_text=True)
        self.assertIn('семья', html)
        self.assertIn('Your sentence', html)
        self.service.client.responses.create.assert_not_called()
        self.assertEqual(self.client.get('/word_jumble/load/missing').status_code, 404)

    def test_short_library_is_completed_and_saved_without_replacing_known_words(self):
        self.service.client.responses.create.return_value.output_text = json.dumps({'words': ['мама', 'любить']})
        result = self.client.post('/word_jumble/create', data={'topic': 'family', 'difficulty': 'easy'})
        self.assertEqual(result.status_code, 303)
        saved = self.service.get_game(result.location.rsplit('/', 1)[1])
        self.assertEqual(set(saved['words']), {'семья', 'мама', 'любить'})
        self.assertEqual(saved['topic'], 'family')
        self.assertEqual(saved['difficulty'], 'easy')
        request = self.service.client.responses.create.call_args.kwargs
        self.assertEqual(json.loads(request['input'][1]['content']), {
            'topic': 'family', 'level': 'easy', 'existing_words': ['семья'], 'additional_count': 2})
        self.assertEqual(request['text']['format']['schema']['properties']['words']['minItems'], 2)
        self.assertTrue(request['text']['format']['strict'])
        self.service.client.responses.create.reset_mock()
        self.assertEqual(self.service.get_game(saved['id'])['words'], saved['words'])
        self.service.client.responses.create.assert_not_called()
        # Exercise additions do not bypass the vocabulary ingestion pipeline.
        with sqlite3.connect(self.service.db_path) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM words').fetchone()[0], 3)

    def test_topic_with_no_matching_words_gets_a_complete_set_at_each_level(self):
        choices = ['актёр', 'играть', 'роль', 'сценарий', 'экранизировать']
        for level, count in WordJumbleService.WORD_COUNTS.items():
            with self.subTest(level=level):
                self.service.client.responses.create.return_value.output_text = json.dumps({'words': choices[:count]})
                result = self.client.post('/word_jumble/create', data={'topic': 'cinema', 'difficulty': level})
                self.assertEqual(result.status_code, 303)
                game = self.service.get_game(result.location.rsplit('/', 1)[1])
                self.assertEqual(len(game['words']), count)
                payload = json.loads(self.service.client.responses.create.call_args.kwargs['input'][1]['content'])
                self.assertEqual(payload['level'], level)
                self.assertEqual(payload['existing_words'], [])
                self.assertEqual(game['topic'], 'cinema')

    def test_bad_word_selection_retries_then_fails_without_partial_game(self):
        before = len(self.service.get_saved_games())
        for words in ([], ['мама'], ['мама', 'мама'], ['семья', 'мама'], ['мама', 'mother'],
                      ['мама', 'читать книгу'], ['мама', None]):
            with self.subTest(words=words):
                self.service.client.responses.create.reset_mock()
                self.service.client.responses.create.return_value.output_text = json.dumps({'words': words})
                response = self.client.post('/word_jumble/create', data={'topic': 'family', 'difficulty': 'easy'})
                self.assertEqual(response.status_code, 503)
                self.assertIn('Please try again', response.get_data(as_text=True))
                self.assertIn('value="family" selected', response.get_data(as_text=True))
                self.assertEqual(self.service.client.responses.create.call_count, 2)
                self.assertEqual(len(self.service.get_saved_games()), before)
        self.service.client.responses.create.side_effect = RuntimeError('private provider detail')
        self.service.client.responses.create.reset_mock()
        response = self.client.post('/word_jumble/create', data={'topic': 'family'})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private provider detail', response.get_data(as_text=True))
        self.assertEqual(self.service.client.responses.create.call_count, 1)
        self.assertEqual(len(self.service.get_saved_games()), before)

    def test_repaired_word_selection_is_saved_once_and_invalid_settings_do_not_call_provider(self):
        self.service.client.responses.create.side_effect = [
            SimpleNamespace(status='completed', output_text=json.dumps({'words': ['еще', 'ещё']})),
            SimpleNamespace(status='completed', output_text=json.dumps({'words': ['мама', 'любить']})),
        ]
        before = len(self.service.get_saved_games())
        self.assertEqual(self.client.post('/word_jumble/create', data={'topic': 'family'}).status_code, 303)
        self.assertEqual(len(self.service.get_saved_games()), before + 1)
        self.assertEqual(self.service.client.responses.create.call_count, 2)
        self.service.client.responses.create.reset_mock()
        for data in ({'topic': 'family', 'difficulty': 'unknown'}, {'topic': 'a' * 101}):
            self.assertEqual(self.client.post('/word_jumble/create', data=data).status_code, 400)
        self.service.client.responses.create.assert_not_called()

    def test_full_fragment_and_shell_navigation_have_one_editor(self):
        for headers in ({}, {'HX-Request': 'true', 'HX-Target': 'jumble-content'},
                        {'HX-Request': 'true', 'HX-Target': 'mainContent'}):
            with self.subTest(headers=headers):
                html = self.client.get(self.url, headers=headers).get_data(as_text=True)
                document = Document(html)
                self.assertEqual(len(document.answers), 1)
                ids = [attrs['id'] for _, attrs in document.elements if 'id' in attrs]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual('<!DOCTYPE html>' in html, not headers)
                if headers.get('HX-Target') == 'mainContent':
                    self.assertTrue(html.startswith('<main '))

    def test_save_preserves_exact_draft_without_creating_feedback(self):
        text = 'Она говорит: "Привет!"\n\n</textarea><script>bad()</script>'
        result = self.submit('save', text)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['revision'], 1)
        saved = self.service.get_game(self.id)
        self.assertEqual(saved['draft'], text)
        self.assertIsNone(saved['user_response'])
        self.assertEqual(saved['attempts'], [])
        self.service.client.responses.create.assert_not_called()
        html = self.client.get(self.url).get_data(as_text=True)
        self.assertEqual(Document(html).answers['response-' + self.id], text)
        self.assertNotIn('<script>bad()', html)
        self.assertIn('Draft saved', self.client.get('/word_jumble').get_data(as_text=True))

    def test_checks_append_and_drafts_do_not_change_previous_results(self):
        self.assertEqual(self.submit('mark', 'Семья дома.').status_code, 200)
        self.assertEqual(self.submit('save', 'Семья в школе.', 1).status_code, 200)
        game = self.service.get_game(self.id)
        self.assertEqual(game['user_response'], 'Семья дома.')
        self.assertEqual(game['draft'], 'Семья в школе.')
        self.assertEqual(len(game['attempts']), 1)
        self.assertEqual(self.submit('mark', 'Семья в школе.', 2).status_code, 200)
        game = self.service.get_game(self.id)
        self.assertEqual([a['response'] for a in game['attempts']], ['Семья в школе.', 'Семья дома.'])
        self.assertEqual(game['attempts'][0]['source'], 'sentence-v1')
        html = self.client.get(self.url).get_data(as_text=True)
        self.assertIn('Previous checks', html)
        self.assertIn('3/4', html)

    def test_stale_revision_rejected_before_check_or_save(self):
        self.submit('save', 'Новый черновик.')
        for kind in ('save', 'mark'):
            response = self.submit(kind, 'Старый черновик.')
            self.assertEqual(response.status_code, 409)
            self.assertIn('another tab', response.json['error'])
        self.assertEqual(self.service.get_game(self.id)['draft'], 'Новый черновик.')
        self.service.client.responses.create.assert_not_called()

    def test_storage_error_rolls_back_check_and_logs_database_diagnostics(self):
        self.submit('save', 'Сохранённый черновик.')
        with sqlite3.connect(self.service.db_path) as conn:
            conn.execute('''CREATE TRIGGER broken_check BEFORE INSERT ON word_jumble_attempts
                BEGIN SELECT missing_test_function(); END''')
        with self.assertLogs('blueprints.word_jumble', level='WARNING') as logs:
            response = self.submit('mark', 'Новая версия.', revision=1)
        self.assertEqual(response.status_code, 503)
        self.assertIn('SQLITE_ERROR', logs.output[0])
        self.assertIn('missing_test_function', logs.output[0])
        self.assertNotIn('missing_test_function', response.get_data(as_text=True))
        game = self.service.get_game(self.id)
        self.assertEqual(game['draft'], 'Сохранённый черновик.')
        self.assertEqual(game['revision'], 1)
        self.assertEqual(game['attempts'], [])
        with sqlite3.connect(self.service.db_path) as conn:
            conn.execute('DROP TRIGGER broken_check')
        self.assertEqual(self.submit('mark', 'Новая версия.', revision=1).status_code, 200)
        self.assertEqual(len(self.service.get_game(self.id)['attempts']), 1)

    def test_in_flight_check_cannot_overwrite_newer_draft(self):
        def concurrent_edit(**kwargs):
            self.service.save_draft(self.id, 'Новая мысль.', 0)
            return SimpleNamespace(status='completed', output_text=json.dumps(self.evaluation))
        self.service.client.responses.create.side_effect = concurrent_edit
        self.assertEqual(self.submit('mark', 'Старая мысль.').status_code, 409)
        game = self.service.get_game(self.id)
        self.assertEqual(game['draft'], 'Новая мысль.')
        self.assertEqual(game['attempts'], [])
        self.assertIsNone(game['score'])

    def test_invalid_grades_refusals_and_failures_do_not_write(self):
        bad = [dict(self.evaluation, score=95), dict(self.evaluation, score=-1),
               dict(self.evaluation, score=True), dict(self.evaluation, score=2.5),
               dict(self.evaluation, commentary=''), dict(self.evaluation, polished_sentence=None), []]
        for output in bad:
            with self.subTest(output=output):
                self.service.client.responses.create.return_value = SimpleNamespace(status='completed', output_text=json.dumps(output))
                self.assertEqual(self.submit('mark', 'Ответ.').status_code, 503)
        for status, text in [('incomplete', '{}'), ('completed', '')]:
            self.service.client.responses.create.return_value = SimpleNamespace(status=status, output_text=text)
            self.assertEqual(self.submit('mark', 'Ответ.').status_code, 503)
        self.service.client.responses.create.side_effect = RuntimeError('secret technical detail')
        response = self.submit('mark', 'Ответ.')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.get_data(as_text=True))
        game = self.service.get_game(self.id)
        self.assertEqual(game['revision'], 0)
        self.assertEqual(game['attempts'], [])
        self.assertIsNone(game['score'])

    def test_native_failure_retains_submitted_text_and_revision(self):
        self.service.client.responses.create.side_effect = RuntimeError('unavailable')
        result = self.submit('mark', 'Не потеряйте мой ответ.', enhanced=False)
        self.assertEqual(result.status_code, 503)
        document = Document(result.get_data(as_text=True))
        self.assertEqual(document.answers['response-' + self.id], 'Не потеряйте мой ответ.')
        self.assertEqual(self.submit('save', 'Черновик.', enhanced=False).status_code, 303)
        conflict = self.submit('save', 'Другой черновик.', enhanced=False)
        self.assertEqual(conflict.status_code, 409)
        document = Document(conflict.get_data(as_text=True))
        self.assertEqual(document.answers['response-' + self.id], 'Другой черновик.')

    def test_empty_and_long_checks_rejected_but_empty_draft_can_be_saved(self):
        for text in ('  ', 'а' * 1001):
            self.assertEqual(self.submit('mark', text).status_code, 400)
        self.assertEqual(self.submit('save', 'а' * 1001).status_code, 400)
        self.assertEqual(self.submit('save', '').status_code, 200)
        self.service.client.responses.create.assert_not_called()

    def test_exact_topics_unique_words_and_invalid_levels(self):
        with sqlite3.connect(self.service.db_path) as conn:
            conn.execute("INSERT INTO words(lemma,pos,topic,lemma_difficulty) VALUES ('семья','OTHER','[\"family\"]',1)")
            conn.execute("INSERT INTO words(lemma,pos,topic,lemma_difficulty) VALUES ('плохо','OTHER','[\"extended_family\"]',1)")
        self.assertEqual(self.service.get_words('family', 'easy', 5), ['семья'])
        with self.assertRaises(ValueError):
            self.service.get_words('any', 'invalid', 3)

    def test_russian_interface_and_assessment_prompt(self):
        with self.client.session_transaction() as session:
            session['ui_lang'] = 'ru'
        html = self.client.get(self.url).get_data(as_text=True)
        self.assertIn('Сохранить черновик', html)
        self.assertNotIn('Save draft', html)
        text = 'Она сказала: "Привет!"\nСемья дома.'
        self.evaluation['commentary'] = 'Вы ясно выразили мысль о своей семье.'
        self.service.client.responses.create.return_value.output_text = json.dumps(self.evaluation)
        self.submit('mark', text)
        kwargs = self.service.client.responses.create.call_args.kwargs
        self.assertIn('in Russian', kwargs['input'][0]['content'])
        self.assertEqual(json.loads(kwargs['input'][1]['content'])['response'], text)
        self.assertEqual(self.service.get_game(self.id)['attempts'][0]['ui_language'], 'ru')

    def test_actual_sdk_serializes_the_structured_check(self):
        requests = []
        def handler(request):
            requests.append(json.loads(request.content))
            return httpx.Response(200, json={'id': 'resp_test', 'object': 'response', 'created_at': 0,
                'model': 'gpt-5-mini', 'status': 'completed', 'output': [{'id': 'msg_test',
                'type': 'message', 'role': 'assistant', 'status': 'completed', 'content': [
                {'type': 'output_text', 'text': json.dumps(self.evaluation), 'annotations': []}]}]})
        self.service.client = openai.OpenAI(api_key='test-only', http_client=httpx.Client(transport=httpx.MockTransport(handler)))
        self.addCleanup(self.service.client.close)
        self.service.mark_response(self.id, 'Семья дома.', 0)
        payload = requests[0]
        self.assertEqual(payload['reasoning'], {'effort': 'medium'})
        self.assertTrue(payload['text']['format']['strict'])
        self.assertFalse(payload['store'])
        self.assertNotIn('temperature', payload)

    def test_tutor_feedback_saves_explanations_and_separates_optional_phrasing(self):
        answer = 'Я рад когда читаю книгу с моими очкими и пию чай'
        self.evaluation.update(commentary='You connected reading and tea in a clear personal thought.',
            corrections=[{'original':'очкими','replacement':'очками',
                          'explanation':'Use the instrumental plural after с; моими already has the correct ending.'},
                         {'original':'пию','replacement':'пью','explanation':'This is the я form of пить.'}],
            polished_sentence='Я рад, когда читаю книгу в очках и пью чай.',
            phrasing_note='В очках is the usual expression for wearing glasses.')
        self.service.client.responses.create.return_value.output_text = json.dumps(self.evaluation)
        response = self.submit('mark', answer)
        self.assertEqual(response.status_code, 200)
        game = self.service.get_game(self.id)
        self.assertEqual(game['attempts'][0]['tutor_feedback'], self.evaluation)
        self.assertEqual(game['attempts'][0]['response'], answer)
        self.assertIn('Use the instrumental plural', game['feedback'])
        html = self.client.get(self.url).get_data(as_text=True)
        self.assertIn(self.evaluation['commentary'], html)
        self.assertIn('Corrections explained', html)
        self.assertIn('See a polished version', html)
        self.assertNotIn('What’s working', html)
        self.assertNotIn('Try this next', html)
        details = [attrs for tag,attrs in Document(html).elements
                   if tag == 'details' and 'sentence-polished' in attrs.get('class','')]
        self.assertEqual(len(details), 1)
        self.assertNotIn('open', details[0])
        self.assertIn(self.evaluation['commentary'], response.json['feedback'])
        self.assertIn('class="visually-hidden">change to', html)
        # The legacy feedback fragment uses Bootstrap's visible-to-AT utility.
        # The shared header has its own correctly scoped sr-only progress bar.
        self.assertNotIn('class="sr-only"', response.json['feedback'])

    def test_repeated_whole_sentence_fix_is_removed_but_distinct_fixes_remain(self):
        answer = 'Я люблю сериалы и фильми'
        correction = dict(original='фильми', replacement='фильмы', explanation='The plural of фильм is фильмы, with ы.')
        duplicate = dict(original=answer, replacement='Я люблю сериалы и фильмы.', explanation='The same correction again.')
        self.evaluation.update(corrections=[duplicate, correction], polished_sentence='Я люблю сериалы и фильмы.')
        self.service.client.responses.create.return_value.output_text = json.dumps(self.evaluation)
        self.assertEqual(self.submit('mark', answer).status_code, 200)
        self.assertEqual(self.service.get_game(self.id)['attempts'][0]['tutor_feedback']['corrections'], [correction])

    def test_missing_final_stop_is_not_a_reason_to_deduct_points(self):
        answer = 'Я люблю кино'
        wrong = {**self.evaluation, 'corrections': [dict(original='кино', replacement='кино.', explanation='Add a full stop.')]}
        correct = {**self.evaluation, 'score': 4, 'corrections': [], 'polished_sentence': ''}
        self.service.client.responses.create.side_effect = [
            SimpleNamespace(status='completed', output_text=json.dumps(wrong)),
            SimpleNamespace(status='completed', output_text=json.dumps(correct)),
        ]
        self.assertEqual(self.submit('mark', answer).status_code, 200)
        attempt = self.service.get_game(self.id)['attempts'][0]
        self.assertEqual(attempt['score'], 4)
        self.assertEqual(attempt['tutor_feedback']['corrections'], [])
        self.assertIn('full stop is optional', self.service.client.responses.create.call_args.kwargs['input'][0]['content'])

    def test_wrong_language_in_individual_explanation_is_retried(self):
        correction = dict(original='пить', replacement='пью', explanation='Используйте правильную форму глагола в первом лице единственного числа.')
        wrong = {**self.evaluation, 'corrections': [correction]}
        correct = {**wrong, 'corrections': [{**correction, 'explanation': 'With я, use пью.'}]}
        self.service.client.responses.create.side_effect = [
            SimpleNamespace(status='completed', output_text=json.dumps(wrong)),
            SimpleNamespace(status='completed', output_text=json.dumps(correct)),
        ]
        self.assertEqual(self.submit('mark', 'Я пить чай.').status_code, 200)
        self.assertEqual(self.service.get_game(self.id)['attempts'][0]['tutor_feedback'], correct)
        self.assertEqual(self.service.client.responses.create.call_count, 2)

    def test_good_answer_needs_no_correction_or_rewrite(self):
        self.evaluation.update(score=4, polished_sentence='', extension='Could you say where your family lives?')
        self.service.client.responses.create.return_value.output_text = json.dumps(self.evaluation)
        self.assertEqual(self.submit('mark', 'Семья дома.').status_code, 200)
        html = self.client.get(self.url).get_data(as_text=True)
        self.assertIn('4/4', html)
        self.assertIn(self.evaluation['extension'], html)
        self.assertNotIn('Corrections explained', html)
        self.assertNotIn('See a polished version', html)

    def test_wrong_language_is_retried_before_saving_one_assessment(self):
        wrong = {**self.evaluation, 'commentary': 'Вы хорошо выразили свою мысль и правильно использовали все слова.'}
        self.service.client.responses.create.side_effect = [
            SimpleNamespace(status='completed', output_text=json.dumps(wrong)),
            SimpleNamespace(status='completed', output_text=json.dumps(self.evaluation)),
        ]
        self.assertEqual(self.submit('mark', 'Семья дома.').status_code, 200)
        game = self.service.get_game(self.id)
        self.assertEqual(game['revision'], 1)
        self.assertEqual(len(game['attempts']), 1)
        self.assertEqual(game['attempts'][0]['tutor_feedback']['commentary'], self.evaluation['commentary'])
        self.assertEqual(self.service.client.responses.create.call_count, 2)

    def test_invented_or_invalid_corrections_never_become_saved_feedback(self):
        correction = dict(original='пить', replacement='пью', explanation='Use the я form.')
        for changes in ({'corrections':[dict(correction, original='несуществующее')]},
                        {'corrections':[dict(correction, replacement='пить')]},
                        {'corrections':[dict(correction, explanation='')]},
                        {'corrections':[correction, correction]}, {'corrections':[correction]*4},
                        {'corrections':[correction], 'extension':'Now write another sentence.'},
                        {'corrections':'пью'}, {'polished_sentence':'', 'phrasing_note':'Missing example'}):
            with self.subTest(changes=changes):
                self.service.client.responses.create.return_value.output_text = json.dumps({**self.evaluation, **changes})
                self.assertEqual(self.submit('mark', 'Я пить чай.').status_code, 503)
                self.assertEqual(self.service.get_game(self.id)['attempts'], [])

    def test_tutor_text_is_escaped_and_old_feedback_keeps_its_content(self):
        with sqlite3.connect(self.service.db_path) as conn:
            conn.execute('''INSERT INTO word_jumble_attempts
                (game_id,response,score,score_max,feedback,strength,next_step,example,ui_language,source)
                VALUES (?, 'Семья дома.', 3, 4, 'Earlier summary', 'Earlier strength',
                        'Earlier advice', 'Семья в школе.', 'en', 'sentence-v1')''', (self.id,))
        self.evaluation['commentary'] = 'Your text says <script>alert("bad")</script>.'
        self.service.client.responses.create.return_value.output_text = json.dumps(self.evaluation)
        self.assertEqual(self.submit('mark', 'Семья дома.').status_code, 200)
        html = self.client.get(self.url).get_data(as_text=True)
        self.assertNotIn('<script>alert', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('Earlier strength', html)
        self.assertIn('Earlier advice', html)
        self.assertIsNone(self.service.get_game(self.id)['attempts'][1]['tutor_feedback'])

    def test_tutor_migration_preserves_every_old_attempt_field(self):
        with sqlite3.connect(self.service.db_path) as conn:
            conn.execute('ALTER TABLE word_jumble_attempts DROP COLUMN tutor_feedback')
            strip_progression_and_levels(conn)
            conn.execute('DROP INDEX live_sessions_scenario')
            conn.execute('ALTER TABLE live_conversation_sessions DROP COLUMN variant_id')
            conn.execute('ALTER TABLE live_conversation_sessions DROP COLUMN scenario_id')
            conn.execute('ALTER TABLE live_conversation_sessions DROP COLUMN end_reason')
            conn.execute('DROP TABLE speaking_reviews')
            conn.execute('DELETE FROM schema_migrations WHERE version>=20')
            conn.execute('''INSERT INTO word_jumble_attempts
                (game_id,response,score,score_max,feedback,strength,next_step,example,ui_language,source)
                VALUES (?, 'Семья дома.', 4, 4, 'Keep this feedback', 'Keep strength',
                        'Keep advice', 'Keep example', 'en', 'sentence-v1')''', (self.id,))
            before = conn.execute('SELECT * FROM word_jumble_attempts').fetchall()
        version, backup = upgrade_database(self.service.db_path)
        self.assertEqual(version, latest_schema_version())
        with sqlite3.connect(self.service.db_path) as conn, sqlite3.connect(backup) as old:
            after = conn.execute('SELECT * FROM word_jumble_attempts').fetchall()
            self.assertEqual([row[:-1] for row in after], before)
            self.assertTrue(all(row[-1] is None for row in after))
            self.assertEqual(old.execute('SELECT * FROM word_jumble_attempts').fetchall(), before)
        self.assertEqual(upgrade_database(self.service.db_path), (latest_schema_version(), None))

    def test_migration_preserves_legacy_answers_without_fabricating_a_scale(self):
        with sqlite3.connect(self.service.db_path) as conn:
            conn.execute('DROP TABLE word_jumble_attempts')
            conn.execute('DROP TABLE word_jumble_drafts')
            # Remove the later region extension when constructing an older schema.
            conn.execute('DROP INDEX lesson_pick_region')
            conn.execute('ALTER TABLE lesson_word_picks DROP COLUMN reading_confirmed')
            conn.execute('ALTER TABLE lesson_word_picks DROP COLUMN region_id')
            conn.execute('DROP TABLE lesson_word_regions')
            strip_progression_and_levels(conn)
            conn.execute('DROP INDEX live_sessions_scenario')
            conn.execute('ALTER TABLE live_conversation_sessions DROP COLUMN variant_id')
            conn.execute('ALTER TABLE live_conversation_sessions DROP COLUMN scenario_id')
            conn.execute('ALTER TABLE live_conversation_sessions DROP COLUMN end_reason')
            conn.execute('DROP TABLE speaking_reviews')
            conn.execute('DELETE FROM schema_migrations WHERE version>=6')
            conn.execute('UPDATE word_jumble_games SET user_response=?,score=95,feedback=? WHERE id=?',
                         ('Мой отец дома.', 'Earlier advice.', self.id))
            original = conn.execute('SELECT * FROM word_jumble_games').fetchall()
        version, backup = upgrade_database(self.service.db_path)
        self.assertEqual(version, latest_schema_version())
        self.assertTrue(Path(backup).exists())
        with sqlite3.connect(self.service.db_path) as conn:
            self.assertEqual([row[:-1] for row in conn.execute('SELECT * FROM word_jumble_games')], original)
            self.assertEqual(conn.execute('SELECT DISTINCT owner_profile_id FROM word_jumble_games').fetchall(), [('personal-learning',)])
        game = self.service.get_game(self.id)
        self.assertEqual(game['attempts'][0]['score'], 95)
        self.assertIsNone(game['attempts'][0]['score_max'])
        self.assertIsNone(game['attempts'][0]['created_at'])
        html = self.client.get(self.url).get_data(as_text=True)
        self.assertIn('Earlier advice.', html)
        self.assertNotIn('95/4', html)
        self.assertEqual(self.submit('mark', 'Новый ответ.').status_code, 200)
        self.assertEqual(self.service.get_game(self.id)['attempts'][1]['response'], 'Мой отец дома.')
        self.assertEqual(upgrade_database(self.service.db_path), (latest_schema_version(), None))
