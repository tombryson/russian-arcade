"""Translation direction, persistence, provider failures and reward integrity."""
import json
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import httpx
import openai

from repositories.translation_repository import TranslationRepository, TranslationConflict
from services.sentence_service import SentenceService, TranslationUnavailable
from tests.support import isolated_app
from tests.test_activity_cleanup import Document


class TranslationCleanupTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=SentenceService)
        self.app = isolated_app(self, {'SentenceService': self.service})
        self.repository = TranslationRepository(self.app.config['DB_PATH'])
        self.id, _ = self.repository.save_content('Кот спит дома.', 'The cat is sleeping at home.', 'home', 1)
        self.client = self.app.test_client()
        # These exercise behavior tests submit as the explicitly selected learner.
        self.client.environ_base['HTTP_X_CSRF_TOKEN'] = self.client.get('/api/v1/user-session').json['csrf_token']
        self.headers = {'Accept': 'application/json'}
        self.assessment = {'score': 3, 'strength': 'The meaning is clear.', 'next_step': 'Check the verb ending.', 'example': 'Кот спит дома.'}
        self.service.assess_translation.return_value = self.assessment
        self.service.get_sentence.return_value = {'sentence': 'Мы идём в школу.', 'english': 'We are going to school.'}
        self.url = f'/sentences/practice/{self.id}'

    def submit(self, kind='assess', answer='Кот спит дома.', revision=0, headers=None, **extra):
        return self.client.post('/sentence/' + kind, data={'sentence_id': self.id, 'user_response': answer,
            'revision': revision, **extra}, headers=self.headers if headers is None else headers)

    def count(self, table):
        with sqlite3.connect(self.app.config['DB_PATH']) as conn:
            return conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]

    def test_setup_and_saved_practice_work_without_ai_and_hide_reference(self):
        for headers in ({}, {'HX-Request': 'true', 'HX-Target': 'mainContent'}):
            response = self.client.get(self.url, headers=headers)
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('The cat is sleeping at home.', html)
            self.assertNotIn('Кот спит дома.', html)
            document = Document(html)
            self.assertEqual(document.answers['translation-answer'], '')
            ids = [attrs['id'] for _, attrs in document.elements if 'id' in attrs]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual('<!DOCTYPE html>' in html, not headers)
        self.service.assess_translation.assert_not_called()
        self.service.get_sentence.assert_not_called()
        self.assertEqual(self.client.get('/sentences/practice/999999').status_code, 404)

    def test_draft_round_trip_preserves_punctuation_and_has_no_reward(self):
        text = 'Он сказал: "Привет!"\n</textarea><script>bad()</script>'
        result = self.submit('save', text)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['revision'], 1)
        self.assertEqual(result.json['state'], 'Draft saved')
        html = self.client.get(self.url).get_data(as_text=True)
        self.assertEqual(Document(html).answers['translation-answer'], text)
        self.assertNotIn('<script>bad()', html)
        self.assertEqual(self.count('translation_attempts'), 0)
        self.assertEqual(self.count('reward_events'), 0)
        self.service.assess_translation.assert_not_called()

    def test_check_uses_server_prompt_and_level_records_answer_and_awards_once(self):
        result = self.submit(answer='Мой вариант.', sentence='forged', english='forged', score=4, difficulty=5)
        self.assertEqual(result.status_code, 200)
        self.service.assess_translation.assert_called_once_with('Кот спит дома.', 'The cat is sleeping at home.', 'Мой вариант.', 'en')
        self.service.generate_audio.assert_not_called()
        first = self.repository.load(self.id)['attempts'][0]
        self.assertEqual(first['response'], 'Мой вариант.')
        self.assertEqual((first['coins_earned'], first['elo_change']), (3, 0))
        self.assertEqual(self.submit(revision=1).status_code, 200)
        current = self.repository.load(self.id)
        self.assertEqual(len(current['attempts']), 2)
        self.assertEqual(current['attempts'][0]['coins_earned'], 0)
        self.assertTrue(current['attempts'][0]['already_rewarded'])
        self.assertEqual(self.count('reward_events'), 0)
        self.assertEqual(self.count('progression_entries'), 1)
        with sqlite3.connect(self.app.config['DB_PATH']) as conn:
            self.assertEqual(conn.execute('SELECT lingocoins FROM users WHERE user_id=1').fetchone()[0], 0)
            self.assertEqual(conn.execute('SELECT score FROM sentences WHERE id=?', (self.id,)).fetchone()[0], 0)

    def test_old_reward_ledger_is_preserved_separately_from_new_participation(self):
        with sqlite3.connect(self.app.config['DB_PATH']) as conn:
            conn.execute('UPDATE users SET lingocoins=70,elo_rating=1100 WHERE user_id=1')
            conn.execute('INSERT INTO reward_events(user_id,reward_key,coins,elo_change,legacy) VALUES (1,?,0,0,1)', (f'sentence:{self.id}',))
        self.assertEqual(self.repository.load(self.id)['attempts'], [])
        self.submit()
        self.assertEqual(self.repository.load(self.id)['attempts'][0]['coins_earned'], 3)
        with sqlite3.connect(self.app.config['DB_PATH']) as conn:
            self.assertEqual(conn.execute('SELECT lingocoins,elo_rating FROM users WHERE user_id=1').fetchone(), (70,1100))
            self.assertEqual(conn.execute('SELECT coins,elo_change FROM reward_events').fetchall(), [(0,0)])

    def test_check_transaction_rolls_back_draft_attempt_and_reward_together(self):
        with sqlite3.connect(self.app.config['DB_PATH']) as conn:
            conn.execute("CREATE TRIGGER fail_attempt BEFORE INSERT ON translation_attempts BEGIN SELECT RAISE(ABORT,'test failure'); END")
        result = self.submit()
        self.assertEqual(result.status_code, 503)
        for table in ('translation_attempts', 'translation_drafts', 'reward_events', 'progression_events', 'progression_entries'):
            self.assertEqual(self.count(table), 0)
        with sqlite3.connect(self.app.config['DB_PATH']) as conn:
            self.assertEqual(conn.execute('SELECT lingocoins,elo_rating FROM users WHERE user_id=1').fetchone(), (0,1000))
        self.assertEqual(self.repository.load(self.id)['revision'], 0)

    def test_provider_failure_has_no_score_and_native_form_retains_answer(self):
        self.service.assess_translation.side_effect = TranslationUnavailable('private details')
        for headers in (self.headers, {}):
            response = self.submit(answer='Сохраните это.', headers=headers)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('private details', response.get_data(as_text=True))
            if not headers:
                self.assertEqual(Document(response.get_data(as_text=True)).answers['translation-answer'], 'Сохраните это.')
        self.assertEqual(self.count('translation_attempts'), 0)
        self.assertEqual(self.count('reward_events'), 0)
        self.assertEqual(self.submit('save', 'Сохраните это.', headers={}).status_code, 303)

    def test_stale_and_in_flight_requests_cannot_overwrite(self):
        self.submit('save', 'Первый черновик.')
        self.assertEqual(self.submit(revision=0).status_code, 409)
        self.service.assess_translation.assert_not_called()
        def racing(*args):
            self.repository.save_draft(self.id, 'Новый черновик.', 1)
            return self.assessment
        self.service.assess_translation.side_effect = racing
        self.assertEqual(self.submit(revision=1).status_code, 409)
        self.assertEqual(self.repository.load(self.id)['draft'], 'Новый черновик.')
        self.assertEqual(self.count('reward_events'), 0)

    def test_invalid_or_blank_input_never_reaches_ai(self):
        for answer in (' ', 'я' * 1001):
            self.assertEqual(self.submit(answer=answer).status_code, 400)
        self.assertEqual(self.submit(revision='bad').status_code, 409)
        self.assertEqual(self.submit('save', '').status_code, 200)
        self.service.assess_translation.assert_not_called()

    def test_generation_is_explicit_and_saved_and_has_no_silent_fallback(self):
        self.assertEqual(self.client.get('/sentence/generate?topic=home&difficulty=1').status_code, 303)
        self.service.get_sentence.assert_not_called()
        result = self.client.post('/sentence/generate', data={'topic':'school','difficulty':1}, headers=self.headers)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json['url'].startswith('/sentences/practice/'))
        self.assertEqual(self.client.get(result.json['url']).status_code, 200)
        before = self.count('sentences')
        self.service.get_sentence.side_effect = TranslationUnavailable('provider unavailable')
        self.assertEqual(self.client.post('/sentence/generate', data={'topic':'home','difficulty':1}, headers=self.headers).status_code, 503)
        self.assertEqual(self.count('sentences'), before)
        self.assertEqual(self.count('reward_events'), 0)

    def test_audio_is_optional_and_failure_leaves_saved_check(self):
        self.assertEqual(self.client.post(f'/sentence/audio/{self.id}').status_code, 400)
        self.submit()
        self.service.generate_audio.return_value = ''
        self.assertEqual(self.client.post(f'/sentence/audio/{self.id}').status_code, 503)
        self.assertEqual(self.count('translation_attempts'), 1)
        self.service.generate_audio.return_value = '/static/media/test.mp3'
        response = self.client.post(f'/sentence/audio/{self.id}')
        self.assertIn('/static/media/test.mp3', response.json['html'])
        self.service.generate_audio.reset_mock()
        self.client.post(f'/sentence/audio/{self.id}')
        self.service.generate_audio.assert_not_called()
        self.assertEqual(self.count('reward_events'), 0)
        self.assertEqual(self.count('progression_entries'), 1)

    def test_library_adds_bilingual_content_without_ai_or_rewards(self):
        data = {'sentence':'Мы дома.','english':'We are at home.','topic':'home','difficulty':1}
        for _ in range(2):
            result = self.client.post('/sentence/add', data=data, headers=self.headers)
            self.assertEqual(result.status_code, 200)
        self.assertEqual(self.count('sentences'), 2)
        self.assertEqual(self.count('reward_events'), 0)
        self.assertEqual(self.count('progression_entries'), 0)
        self.service.translate_for_library.assert_not_called()
        self.assertIn('Мы дома.', self.client.get(result.json['url']).get_data(as_text=True))

    def test_library_topic_filter_and_russian_interface(self):
        self.repository.save_content('Мы в школе.', 'We are at school.', 'school', 2)
        exported = self.client.get('/sentences/saved?fetch_all=true', headers=self.headers).json
        self.assertIn('school', exported['topics'])
        self.assertTrue(all(isinstance(topic, str) for topic in exported['topics']))
        html = self.client.get('/sentences/saved?topic=school').get_data(as_text=True)
        self.assertIn('We are at school.', html)
        self.assertNotIn('The cat is sleeping at home.', html)
        with self.client.session_transaction() as session:
            session['ui_lang'] = 'ru'
        html = self.client.get(self.url).get_data(as_text=True)
        self.assertIn('Проверить перевод', html)
        self.assertIn('The cat is sleeping at home.', html)
        self.submit()
        self.assertEqual(self.service.assess_translation.call_args.args[-1], 'ru')
        self.assertEqual(self.repository.load(self.id)['attempts'][0]['ui_language'], 'ru')


class TranslationProviderTests(unittest.TestCase):
    def setUp(self):
        self.service = SentenceService.__new__(SentenceService)
        self.service.client = Mock()
        self.good = {'score':4, 'strength':'Clear meaning.', 'next_step':'Try another sentence.', 'example':'Кот дома.'}
        self.output(self.good)

    def output(self, value, status='completed'):
        self.service.client.responses.create.return_value = SimpleNamespace(status=status, output_text=json.dumps(value))

    def test_direction_and_exact_text_reach_the_provider(self):
        answer = 'Он сказал: "Привет!"\nИ ушёл.'
        self.service.assess_translation('Кот дома.', 'The cat is at home.', answer, 'en')
        kwargs = self.service.client.responses.create.call_args.kwargs
        self.assertIn('English-to-Russian', kwargs['input'][0]['content'])
        self.assertIn('accept', kwargs['input'][0]['content'].lower())
        self.assertEqual(json.loads(kwargs['input'][1]['content'])['russian_answer'], answer)
        self.assertEqual(kwargs['reasoning'], {'effort':'low'})
        self.assertFalse(kwargs['store'])
        self.assertNotIn('temperature', kwargs)

    def test_refusal_incomplete_invalid_scores_and_empty_feedback_fail_closed(self):
        for result in [dict(self.good, score=95), dict(self.good, score=True), dict(self.good, score=-1),
                       dict(self.good, score=3.5), dict(self.good, strength=''), dict(self.good, next_step=None), []]:
            self.output(result)
            with self.assertRaises(TranslationUnavailable):
                self.service.assess_translation('Кот дома.', 'The cat is at home.', 'Кот дома.')
        self.output(self.good, status='incomplete')
        with self.assertRaises(TranslationUnavailable):
            self.service.assess_translation('Кот дома.', 'The cat is at home.', 'Кот дома.')
        self.service.client.responses.create.return_value = SimpleNamespace(status='completed', output_text='')
        with self.assertRaises(TranslationUnavailable):
            self.service.get_sentence('home', 1)

    def test_generation_never_substitutes_a_fallback_or_rewrites_a_pasted_russian_sentence(self):
        self.service.client.responses.create.side_effect = RuntimeError('offline')
        with self.assertRaises(TranslationUnavailable):
            self.service.get_sentence('home', 1)
        self.service.client.responses.create.assert_called_once()
        self.service.client.responses.create.side_effect = None
        self.output({'english':'Hello, world!'})
        self.assertEqual(self.service.translate_for_library('Привет, мир!'), 'Hello, world!')
        self.assertEqual(json.loads(self.service.client.responses.create.call_args.kwargs['input'][1]['content']), {'russian':'Привет, мир!'})

    def test_installed_sdk_serializes_strict_translation_requests(self):
        captured = []
        def handler(request):
            payload = json.loads(request.content); captured.append(payload)
            value = self.good if payload['text']['format']['name'] == 'translation_feedback' else {'sentence':'Кот дома.','english':'The cat is at home.'}
            return httpx.Response(200, json={'id':'resp_translation', 'object':'response','created_at':0,'model':'gpt-5-mini','status':'completed',
                'output':[{'id':'msg_translation','type':'message','role':'assistant','status':'completed',
                'content':[{'type':'output_text','text':json.dumps(value),'annotations':[]}]}]})
        self.service.client = openai.OpenAI(api_key='test-only', http_client=httpx.Client(transport=httpx.MockTransport(handler)))
        self.addCleanup(self.service.client.close)
        pair = self.service.get_sentence('home', 1)
        self.service.assess_translation(pair['sentence'], pair['english'], 'Кот дома.')
        self.assertEqual(len(captured), 2)
        for payload in captured:
            self.assertTrue(payload['text']['format']['strict'])
            self.assertFalse(payload['store'])
