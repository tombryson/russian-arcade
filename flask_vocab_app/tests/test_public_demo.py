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

    def test_profile_control_without_trial_shows_public_preview_information(self):
        self.assertNotIn('hosted_trial', self.app.extensions)
        page = self.a.get('/post/profiles', base_url=self.base)
        self.assertEqual(page.status_code, 200)
        self.assertIn('<h1>Demo profile</h1>', page.text)
        self.assertIn('temporary profile', page.text.lower())
        self.assertIn('sign-in', page.text.lower())
        self.assertIn('not enabled', page.text.lower())
        self.assertNotIn('href="/trial/sign-in"', page.text)
        self.assertIn('href="/post/#home"', page.text)
        account = self.a.get('/trial/account', base_url=self.base)
        self.assertEqual(account.status_code, 200)
        self.assertIn('<h1>Demo profile</h1>', account.text)
        self.assertNotIn('href="/trial/sign-in"', account.text)

    def test_sample_pages_work_and_provider_upload_edit_routes_are_blocked(self):
        for path in ('/post/', '/vocab', '/curriculum', '/api/v1/flashcards', '/api/v1/first-steps', '/api/v1/games'):
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

    def test_shop_is_visible_but_purchases_are_disabled(self):
        from repositories.learning_repository import transaction
        catalogue = self.a.get('/api/v1/games', base_url=self.base).json
        self.assertFalse(catalogue['shop']['enabled'])
        self.assertTrue(all(not game['purchase']['can_purchase'] for game in catalogue['games']))
        response = self.a.post('/api/v1/games/scene-builder/purchase', base_url=self.base,
                               headers={'X-CSRF-Token': catalogue['csrf_token']},
                               json={'request_id': 'demo-purchase', 'expected_price': 25})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json['error']['code'], 'demo_unavailable')
        with transaction(self.app.config['DB_PATH']) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM journey_game_purchases').fetchone()[0], 0)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM journey_game_access').fetchone()[0], 0)

    def test_advertised_samples_are_playable_without_providers_and_owned(self):
        import json
        from repositories.learning_repository import transaction
        from services.demo_games import SAMPLE_GAMES
        visitor = self.state(self.a)
        headers = {'X-CSRF-Token':visitor['csrf_token']}
        catalogue = self.a.get('/api/v1/games',base_url=self.base).json
        self.assertEqual({g['id'] for g in catalogue['games'] if g['unlocked']}, SAMPLE_GAMES)
        for game in catalogue['games']:
            if game['id'] not in SAMPLE_GAMES:
                self.assertEqual(game['availability'],'local-only')
                continue
            options = {'grammar_focus':'mixed'} if game['id']=='scene-builder' else {'source':'vocabulary','topic':'custom provider bypass'}
            response = self.a.post('/api/v1/games/'+game['id']+'/start',base_url=self.base,headers=headers,
                                   json={'request_id':'sample-'+game['id'],'options':options})
            self.assertEqual(response.status_code,200,response.text)
            state = response.json
            self.assertTrue(state['sample'])
            self.assertEqual(state['phase'],'play')
            root = '/api/v1/games/sessions/'+state['id']
            self.assertEqual(self.b.get(root,base_url=self.base).status_code,404)
            self.assertEqual(self.a.post(root+'/prepare',base_url=self.base,headers=headers,json={}).status_code,403)
            with transaction(self.app.config['DB_PATH']) as conn:
                content = json.loads(conn.execute('SELECT content_json FROM journey_game_sessions WHERE id=?',(state['id'],)).fetchone()[0])
                rounds = content['rounds']
            if state.get('delivery'):
                for index, leg in enumerate(content['legs']):
                    questions = [('ask', {'question_id': leg['required_question']})] if leg.get('required_question') else []
                    for action,payload in [*questions, ('begin',{}),('go',{'path':leg['route']}),('deliver' if index == len(content['legs']) - 1 else 'talk',{})]:
                        result=self.a.post(root+'/route-command',base_url=self.base,headers=headers,json={
                            'request_id':f'demo-route-{state["delivery"]["revision"]}', 'revision':state['delivery']['revision'],
                            'action':action,'payload':payload})
                        self.assertEqual(result.status_code,200,result.text)
                        state=result.json
                self.assertEqual(state['phase'],'completed')
                self.assertFalse(state['study_available'])
                self.assertEqual(state['words'],[])
                continue
            for item in rounds:
                for action, data in [('answer',{'round_id':item['id'],'answer':item['expected_answer']}),('continue',{'round_id':item['id']})]:
                    checked = self.a.post(root+'/'+action,base_url=self.base,headers=headers,json=data)
                    self.assertEqual(checked.status_code,200,checked.text)
                    if action == 'answer':
                        self.assertNotIn('answer_audio',checked.json['result'])
                        if game['id']=='scene-builder':
                            self.assertEqual(checked.json['result']['correct_sentence'],item['correct_sentence'])
                            key=item['answer_audio'][0]['audio_key']
                            self.assertEqual(self.a.post('/api/v1/games/media/'+key+'/prepare',base_url=self.base,
                                                        headers=headers,json={}).status_code,403)
            done = self.a.post(root+'/complete',base_url=self.base,headers=headers,json={})
            self.assertEqual(done.json['phase'],'completed')
            self.assertEqual(done.json['words'],[])
            self.assertFalse(done.json['study_available'])

    def test_riverside_listening_and_section_review_work_without_provider_access(self):
        from services.route_content import build_mission
        visitor = self.state(self.a)
        headers = {'X-CSRF-Token': visitor['csrf_token']}
        result = self.a.post('/api/v1/games/directions/start', base_url=self.base, headers=headers,
                             json={'request_id': 'riverside-listening-demo', 'options': {'delivery_id': 'irina', 'delivery_mode': 'listening'}})
        self.assertEqual(result.status_code, 200)
        state = result.json
        root = '/api/v1/games/sessions/'+state['id']
        def command(action, payload=None):
            nonlocal state
            response = self.a.post(root+'/route-command', base_url=self.base, headers=headers,
                json={'request_id': 'demo-delivery-'+str(state['delivery']['revision']), 'revision': state['delivery']['revision'], 'action': action, 'payload': payload or {}})
            self.assertEqual(response.status_code, 200, response.text)
            state = response.json
        pack = build_mission(mission_id='irina')
        for index, leg in enumerate(pack['legs']):
            self.assertNotIn('text', state['delivery']['lines'][0])
            for line in leg['lines']:
                command('listen', {'leg': index, 'line_id': line['id']})
            command('begin')
            command('go', {'path': leg['route']})
            command('deliver' if index == 2 else 'talk')
        self.assertEqual(state['words'], [])
        self.assertFalse(state['study_available'])
        checks = state['delivery']['first_checks']
        reward = state['reward']['amount']
        command('review_start', {'leg': 1})
        self.assertEqual(state['phase'], 'practice')
        command('review_exit')
        self.assertEqual(state['delivery']['first_checks'], checks)
        self.assertEqual(state['reward']['amount'], reward)
        for suffix in ('words', 'flashcards'):
            response = self.a.post(root+'/'+suffix, base_url=self.base, headers=headers, json={})
            self.assertEqual(response.status_code, 403)

    def test_all_town_missions_are_owned_offline_samples_with_recorded_audio(self):
        import json
        from repositories.learning_repository import transaction
        from services.route_town import TOWN_MISSION_IDS

        other_headers = {'X-CSRF-Token': self.state(self.b)['csrf_token']}
        audio_urls = set()
        self.assertEqual(len(TOWN_MISSION_IDS), 8)
        for mission_id in TOWN_MISSION_IDS:
            with self.subTest(mission=mission_id):
                # Each visitor plays one full mission within the normal write limit.
                client = self.app.test_client()
                headers = {'X-CSRF-Token': self.state(client)['csrf_token']}
                response = client.post('/api/v1/games/directions/start', base_url=self.base, headers=headers,
                    json={'request_id': 'demo-'+mission_id, 'new_game': True,
                          'options': {'delivery_id': mission_id, 'delivery_mode': 'listening'}})
                self.assertEqual(response.status_code, 200, response.text)
                state = response.json
                self.assertTrue(state['sample'])
                self.assertEqual(state['delivery']['map']['scene'], 'town')
                self.assertEqual(state['delivery']['mode'], 'listening')
                root = '/api/v1/games/sessions/'+state['id']
                with transaction(self.app.config['DB_PATH']) as conn:
                    pack = json.loads(conn.execute('SELECT content_json FROM journey_game_sessions WHERE id=?',
                                                   (state['id'],)).fetchone()[0])
                self.assertEqual(pack['mission_id'], mission_id)
                self.assertEqual(self.b.get(root, base_url=self.base).status_code, 404)
                denied = self.b.post(root+'/route-command', base_url=self.base, headers=other_headers,
                    json={'request_id': 'other-'+mission_id, 'revision': state['delivery']['revision'],
                          'action': 'begin', 'payload': {}})
                self.assertEqual(denied.status_code, 404, denied.text)

                def command(action, payload=None):
                    nonlocal state
                    result = client.post(root+'/route-command', base_url=self.base, headers=headers,
                        json={'request_id': 'demo-town-'+str(state['delivery']['revision']),
                              'revision': state['delivery']['revision'], 'action': action, 'payload': payload or {}})
                    self.assertEqual(result.status_code, 200, result.text)
                    state = result.json

                for index, leg in enumerate(pack['legs']):
                    audio_urls.update(line['audio_url'] for line in
                                      [*leg['lines'], leg['clarify'], *(q['reply'] for q in leg.get('questions', []))])
                    self.assertFalse(state['delivery']['can_go'])
                    if leg.get('required_question'):
                        self.assertTrue(state['delivery']['question_required'])
                        command('ask', {'question_id': leg['required_question']})
                        self.assertFalse(state['delivery']['question_required'])
                    for line in state['delivery']['lines']:
                        self.assertNotIn('text', line)
                        command('listen', {'leg': index, 'line_id': line['id']})
                    self.assertTrue(state['delivery']['can_go'])
                    command('begin')
                    if leg.get('transport'):
                        command('board', {'transport_id': leg['transport']['id']})
                        self.assertEqual(state['delivery']['transport']['status'], 'aboard')
                        command('ride', {'stop_id': leg['target']})
                        self.assertEqual(state['delivery']['transport']['stop_id'], leg['target'])
                        command('alight')
                    else:
                        command('go', {'path': leg['route']})
                    self.assertEqual(state['delivery']['phase'], 'arrived', state['delivery']['feedback'])
                    command('deliver' if index == len(pack['legs'])-1 else 'talk')
                audio_urls.add(state['delivery']['ending']['audio_url'])
                self.assertEqual(state['phase'], 'completed')
                self.assertFalse(state['study_available'])
                self.assertEqual(state['words'], [])
                for suffix in ('words', 'flashcards'):
                    denied = client.post(root+'/'+suffix, base_url=self.base, headers=headers, json={})
                    self.assertEqual(denied.status_code, 403)

        self.assertTrue(audio_urls)
        for url in sorted(audio_urls):
            with self.subTest(audio=url):
                with self.a.get(url, base_url=self.base) as audio:
                    self.assertEqual(audio.status_code, 200)
                    self.assertEqual(audio.mimetype, 'audio/mpeg')
                    self.assertGreater(len(audio.data), 0)

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
