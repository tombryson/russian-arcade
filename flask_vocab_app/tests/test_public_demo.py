import os
import shutil
import unittest
from unittest.mock import patch

from hosted import create_hosted_app
from public_demo import prepare_demo
from services.demo_limits import DemoLimits


class PublicDemoTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, PUBLIC_DEMO='true', FLASK_SECRET_KEY='synthetic-test-secret-' * 3,
                         HOSTED_HOSTNAME='russian-arcade.fly.dev')
        env.start()
        self.addCleanup(env.stop)
        root = prepare_demo()
        self.addCleanup(shutil.rmtree, root)
        self.app = create_hosted_app()
        self.a, self.b = self.app.test_client(), self.app.test_client()
        self.base = 'https://russian-arcade.fly.dev'
        network = patch('socket.socket.connect', side_effect=AssertionError('Demo must not use providers'))
        network.start()
        self.addCleanup(network.stop)

    def state(self, client):
        return client.get('/api/v1/user-session', base_url=self.base).json

    def test_profiles_are_isolated_and_cannot_be_selected_by_other_visitors(self):
        a, b = self.state(self.a), self.state(self.b)
        self.assertNotEqual(a['profile']['id'], b['profile']['id'])
        for endpoint in ('/api/v1/user-session', '/api/v1/household'):
            state = self.a.get(endpoint, base_url=self.base).json
            self.assertEqual([p['id'] for p in state['profiles']], [a['profile']['id']])
        result = self.a.post('/api/v1/user-session/select', base_url=self.base,
                             json={'profile_id': b['profile']['id']}, headers={'X-CSRF-Token': a['csrf_token']})
        self.assertEqual(result.status_code, 403)

    def test_sample_pages_work_and_provider_upload_edit_routes_are_blocked(self):
        for path in ('/post/', '/vocab', '/api/v1/flashcards', '/api/v1/first-steps', '/api/v1/games'):
            self.assertEqual(self.a.get(path, base_url=self.base).status_code, 200, path)
        for path in ('/sentence/generate', '/sync_vocab', '/vocab?source=cloud', '/sync/preview'):
            self.assertEqual(self.a.get(path, base_url=self.base).status_code, 403, path)
        state = self.state(self.a)
        for path in ('/api/v1/user-session/profiles', '/api/v1/live-conversations', '/lessons/create',
                     '/api/v1/card-generation/batches', '/api/v1/card-generation/batches/example/next',
                     '/api/v1/live-conversations/example/connect', '/api/v1/flashcards/example/media',
                     '/api/v1/games/example/start'):
            self.assertEqual(self.a.post(path, base_url=self.base, json={},
                          headers={'X-CSRF-Token': state['csrf_token']}).status_code, 403, path)

    def test_new_routes_in_public_modules_are_denied_by_default(self):
        self.app.add_url_rule('/test-provider', endpoint='onboarding.future_provider', view_func=lambda: self.fail('Provider executed'))
        self.assertEqual(self.a.get('/test-provider', base_url=self.base).status_code, 403)

    def test_global_write_limit_survives_fresh_cookies(self):
        a, b = self.state(self.a), self.state(self.b)
        limiter = DemoLimits(self.app.config['DB_PATH'])
        limiter.consume([('writes', 86400, 1)])
        # Fill the daily bucket without thousands of HTTP calls.
        from repositories.learning_repository import transaction
        with transaction(self.app.config['DB_PATH'], write=True) as conn:
            conn.execute("UPDATE demo_limits SET used=10000 WHERE scope='writes' AND duration=86400")
        for client, state in ((self.a, a), (self.b, b)):
            response = client.post('/api/v1/onboarding', json={'milestone': 'coins'}, base_url=self.base,
                                   headers={'X-CSRF-Token': state['csrf_token']})
            self.assertEqual(response.status_code, 429)
            self.assertGreater(int(response.headers['Retry-After']), 0)
        self.assertEqual(self.app.test_client().get('/post/', base_url=self.base).status_code, 200)

    def test_new_cookie_profile_creation_is_globally_limited(self):
        limiter = DemoLimits(self.app.config['DB_PATH'])
        limiter.consume([('new-visitors', 3600, 1)])
        from repositories.learning_repository import transaction
        with transaction(self.app.config['DB_PATH'], write=True) as conn:
            conn.execute("UPDATE demo_limits SET used=120 WHERE scope='new-visitors' AND duration=3600")
        self.assertEqual(self.a.get('/api/v1/user-session', base_url=self.base).status_code, 429)
        self.assertEqual(self.b.get('/api/v1/user-session', base_url=self.base).status_code, 429)
        self.assertEqual(self.a.get('/static/css/public_demo.css', base_url=self.base).status_code, 200)

    def test_demo_notices_use_external_styles_under_the_existing_csp(self):
        page = self.a.get('/post/', base_url=self.base)
        self.assertIn("style-src 'self'", page.headers['Content-Security-Policy'])
        self.assertNotIn('style=', page.get_data(as_text=True))
        self.assertIn('<details class="demo-notice">', page.get_data(as_text=True))
        self.assertIn('/static/css/public_demo.css?v=2', page.get_data(as_text=True))
        css = self.a.get('/static/css/public_demo.css?v=2', base_url=self.base)
        self.assertEqual(css.status_code, 200)
        self.assertIn('position: fixed', css.get_data(as_text=True))
        blocked = self.a.get('/comprehension', base_url=self.base)
        self.assertNotIn('style=', blocked.get_data(as_text=True))
        self.assertIn('/static/css/public_demo.css?v=2', blocked.get_data(as_text=True))

    def test_native_review_is_interactive_owned_and_csrf_protected(self):
        state = self.state(self.a)
        data = {'profile_id': state['profile']['id'], 'scope': {}, 'size': 5, 'submission_id': 'demo-start'}
        self.assertEqual(self.a.post('/api/v1/review-sessions', json=data, base_url=self.base).status_code, 403)
        headers = {'X-CSRF-Token': state['csrf_token']}
        response = self.a.post('/api/v1/review-sessions', json=data, base_url=self.base, headers=headers)
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        saved = response.json
        self.assertNotIn('answer', saved['item'])
        path = '/api/v1/review-sessions/' + saved['id']
        self.state(self.b)
        self.assertIn(self.b.get(path, base_url=self.base).status_code, (403, 404))
        reveal = self.a.post(path + '/reveal', json={'submission_id': 'reveal',
            'expected_revision': saved['revision'], 'item_id': saved['item']['id']}, base_url=self.base, headers=headers)
        self.assertEqual(reveal.status_code, 200)
        self.assertTrue(reveal.json['item']['answer'])
