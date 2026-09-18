"""Hosted sample and funded workspace composition, without provider traffic."""
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from hosted import create_hosted_app
from public_demo import prepare_demo
from services.ai_trial_budget import AITrialBudget, TrialDenied
from tests.test_hosted_trial import IdentityProvider


class HostedTrialIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.env = patch.dict(os.environ, {
            'PUBLIC_DEMO': 'true', 'HOSTED_HOSTNAME': 'arcade.example',
            'FLASK_SECRET_KEY': 'synthetic-session-secret-' * 3,
            'HOSTED_TRIAL_ROOT': str(self.root), 'AI_TRIAL_ENABLED': 'true',
            'GITHUB_OAUTH_CLIENT_ID': 'synthetic-client-id',
            'GITHUB_OAUTH_CLIENT_SECRET': 'synthetic-client-secret',
            'DEMO_OPENAI_API_KEY': 'synthetic-demo-openai',
            'DEMO_ELEVENLABS_API_KEY': 'synthetic-demo-elevenlabs',
            'DEMO_OPENROUTER_API_KEY': 'synthetic-demo-openrouter',
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.samples = prepare_demo()
        self.addCleanup(shutil.rmtree, self.samples)
        self.ledger_path = self.root / 'ai-budget.sqlite3'
        self.ledger = AITrialBudget(self.ledger_path, enabled=True)
        self.ledger.initialize()
        self.network = patch('socket.socket.connect', side_effect=AssertionError('Hosted smoke must not call providers'))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.base = 'https://arcade.example'

    def app(self):
        app = create_hosted_app()
        self.provider = IdentityProvider()
        app.extensions['hosted_trial'].provider = self.provider
        return app

    def login(self, client, identity='github:11'):
        self.provider.identity = identity
        response = client.get('/trial/sign-in', base_url=self.base, buffered=True)
        state = parse_qs(urlsplit(response.location).query)['state'][0]
        response = client.get('/trial/callback?code=valid&state=' + state, base_url=self.base, buffered=True)
        self.assertEqual(response.status_code, 302, response.text)

    def test_all_core_activity_pages_work_without_calls_and_samples_remain_public(self):
        app = self.app()
        visitor = app.test_client()
        learner = app.test_client()
        self.assertEqual(visitor.get('/comprehension', base_url=self.base).status_code, 403)
        self.assertEqual(visitor.get('/post/', base_url=self.base).status_code, 200)
        self.login(learner)
        paths = ('/post/', '/comprehension', '/writing', '/word_jumble', '/sentences',
                 '/sentences/saved', '/lessons', '/vocab', '/api/v1/user-session',
                 '/api/v1/flashcards', '/api/v1/games', '/api/v1/first-steps',
                 '/api/v1/live-conversations/scenarios', '/api/v1/live-conversations/options',
                 '/api/v1/conversations/options')
        for path in paths:
            response = learner.get(path, base_url=self.base, buffered=True)
            self.assertEqual(response.status_code, 200, f'{path}: {response.text[:250]}')
        home = learner.get('/post/', base_url=self.base).text
        self.assertIn('/trial/account', home)
        self.assertNotIn('AI generation and uploads need a local installation', home)
        self.assertEqual(visitor.get('/comprehension', base_url=self.base).status_code, 403)
        with sqlite3.connect(self.ledger_path) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM trial_requests').fetchone()[0], 0)

    def test_dedicated_provider_settings_and_mutated_sample_paths_do_not_leak_between_apps(self):
        app = self.app()
        client = app.test_client()
        self.login(client)
        trial = app.extensions['hosted_trial'].cache['github:11']
        self.assertEqual(trial.config['OPENAI_API_KEY'], 'synthetic-demo-openai')
        self.assertEqual(trial.config['ELEVENLABS_API_KEY'], 'synthetic-demo-elevenlabs')
        self.assertEqual(trial.config['OPENROUTER_API_KEY'], 'synthetic-demo-openrouter')
        self.assertEqual(trial.config['AI_TRIAL_IDENTITY'], 'github:11')
        self.assertTrue(trial.config['AI_TRIAL_ENABLED'])
        self.assertFalse(trial.config['PUBLIC_DEMO'])
        self.assertTrue(app.config['PUBLIC_DEMO'])
        for key in ('OPENAI_API_KEY', 'ELEVENLABS_API_KEY', 'OPENROUTER_API_KEY', 'YANDEX_API_KEY'):
            self.assertEqual(app.config[key], '')
        for key in ('DB_PATH', 'APP_MEDIA_DIR', 'UPLOAD_FOLDER', 'SESSION_FILE_DIR', 'WORD_POST_ASSET_DIR', 'ANKI_MEDIA_DIR'):
            self.assertNotEqual(trial.config[key], app.config[key], key)
            self.assertTrue(Path(trial.config[key]).is_relative_to(self.root / 'tenants'), key)
        self.assertEqual(trial.config['AI_TRIAL_LEDGER_PATH'], str(self.ledger_path))
        self.assertEqual(trial.config['LESSON_MAX_PAGES'], 12)
        self.assertEqual(trial.config['MAX_CONTENT_LENGTH'], 12 * 1024 * 1024)

    def test_profile_control_reaches_account_before_and_after_signin(self):
        app = self.app()
        client = app.test_client()
        visitor = client.get('/post/profiles', base_url=self.base)
        self.assertEqual(visitor.status_code, 302)
        self.assertEqual(visitor.location, '/trial/account')
        page = client.get(visitor.location, base_url=self.base)
        self.assertIn('href="/trial/sign-in"', page.text)
        self.login(client)
        learner = client.get('/post/profiles', base_url=self.base)
        self.assertEqual(learner.status_code, 302)
        self.assertEqual(learner.location, '/trial/account')
        page = client.get(learner.location, base_url=self.base)
        self.assertIn('Signed in as sample-user.', page.text)
        self.assertIn('action="/trial/sign-out"', page.text)

    def test_disabled_profile_account_explains_unavailable_signin(self):
        with patch.dict(os.environ, {'AI_TRIAL_ENABLED': 'false',
                                    'GITHUB_OAUTH_CLIENT_ID': '', 'GITHUB_OAUTH_CLIENT_SECRET': ''}):
            client = create_hosted_app().test_client()
            response = client.get('/post/profiles', base_url=self.base)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/trial/account')
            page = client.get(response.location, base_url=self.base)
            self.assertEqual(page.status_code, 200)
            self.assertIn('<h1>Public preview</h1>', page.text)
            self.assertIn('sign-in', page.text.lower())
            self.assertIn('not enabled', page.text.lower())
            self.assertNotIn('href="/trial/sign-in"', page.text)
            self.assertNotIn('action="/trial/sign-out"', page.text)

    def test_dedicated_credentials_required_to_enable_and_no_fallback_to_regular_keys(self):
        required = ('GITHUB_OAUTH_CLIENT_ID', 'GITHUB_OAUTH_CLIENT_SECRET', 'DEMO_OPENAI_API_KEY',
                    'DEMO_ELEVENLABS_API_KEY', 'DEMO_OPENROUTER_API_KEY')
        for name in required:
            with patch.dict(os.environ, {name: '', 'OPENAI_API_KEY': 'synthetic-regular-key'}):
                with self.assertRaisesRegex(RuntimeError, 'dedicated demo provider keys'):
                    create_hosted_app()
        with patch.dict(os.environ, {'AI_TRIAL_ENABLED': 'false', **dict.fromkeys(required, '')}):
            app = create_hosted_app()
            client = app.test_client()
            self.assertEqual(client.get('/post/', base_url=self.base).status_code, 200)
            self.assertEqual(client.get('/trial/sign-in', base_url=self.base).status_code, 503)
            self.assertEqual(client.get('/trial/status', base_url=self.base).json['enabled'], False)

    def test_missing_spend_ledger_fails_closed_without_reinitializing(self):
        self.ledger_path.unlink()
        with self.assertRaises(TrialDenied):
            create_hosted_app()
        self.assertFalse(self.ledger_path.exists())

    def test_second_identity_has_distinct_sessions_and_samples(self):
        app = self.app()
        a, b = app.test_client(), app.test_client()
        self.login(a, 'github:11')
        self.login(b, 'github:22')
        for client in (a, b):
            self.assertEqual(client.get('/api/v1/user-session', base_url=self.base, buffered=True).status_code, 200)
        apps = app.extensions['hosted_trial'].cache
        self.assertNotEqual(apps['github:11'].config['DB_PATH'], apps['github:22'].config['DB_PATH'])
        self.assertNotEqual(apps['github:11'].config['SESSION_COOKIE_NAME'], apps['github:22'].config['SESSION_COOKIE_NAME'])
        for identity in ('github:11', 'github:22'):
            with sqlite3.connect(apps[identity].config['DB_PATH']) as conn:
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM saved_stories').fetchone()[0], 0)
        with sqlite3.connect(self.ledger_path) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM trial_accounts').fetchone()[0], 2)


if __name__ == '__main__':
    unittest.main()
