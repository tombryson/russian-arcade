"""Speaking selection, saved briefs and repeat avoidance across both modes."""
import json
import unittest
from unittest.mock import patch

from repositories.learning_repository import transaction
from repositories.speaking_history import recent_variants
from tests.support import isolated_app


class SpeakingIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app = isolated_app(self)
        self.app.config.update(OPENAI_API_KEY='synthetic')
        self.client = self.app.test_client()
        state = self.client.get('/api/v1/user-session').json
        self.profile_id = state['profile']['id']
        self.headers = {'X-CSRF-Token': state['csrf_token']}
        self.db = self.app.config['DB_PATH']
        self.step = self.app.extensions['learning']['step_conversation']
        for service in (self.app.extensions['learning']['conversation'],
                        self.app.extensions['learning']['live_conversation'],
                        self.app.extensions['learning']['live_conversation'].reviews):
            self.addCleanup(service.executor.shutdown, wait=True)

    def options(self, mode='live', level='A2', exclude=None):
        query = {'scenario_id': 'shop', 'level': level}
        if exclude:
            query['exclude_seed'] = exclude
        response = self.client.get(f'/api/v1/{mode}-conversations/options', query_string=query)
        self.assertEqual(response.status_code, 200, response.json)
        return response.json['scenario']

    def start(self, mode, key, scenario=None):
        scenario = scenario or self.options(mode)
        body = {'submission_id': key, 'scenario_id': scenario['scenario_id'],
                'target_level': scenario['target_level'], 'scenario_seed': scenario['seed']}
        # Persist the real Step-through session, without buying generation/audio.
        with patch.object(self.step, '_prepare'):
            response = self.client.post(f'/api/v1/{mode}-conversations', json=body, headers=self.headers)
        self.assertEqual(response.status_code, 201, response.json)
        self.assertEqual(response.json['scenario'], scenario)
        return response.json

    def test_both_previews_avoid_situations_started_in_either_mode(self):
        played = set()
        for index, mode in enumerate(('step', 'live', 'step')):
            for preview_mode in ('step', 'live'):
                self.assertNotIn(self.options(preview_mode)['seed'], played)
            saved = self.start(mode, f'mixed-{index}')
            self.assertNotIn(saved['scenario']['seed'], played)
            played.add(saved['scenario']['seed'])
        self.assertEqual(len(played), 3)

    def test_switching_to_step_preserves_the_preview_and_counts_it_for_live(self):
        preview = self.options('live')
        first = self.start('step', 'switch', preview)
        retry = self.start('step', 'switch', preview)
        self.assertEqual(first['id'], retry['id'])
        self.assertNotEqual(self.options('live')['seed'], preview['seed'])
        with transaction(self.db) as conn:
            self.assertEqual(recent_variants(conn, self.profile_id, 'shop', 'A2'), [preview['seed']])
            self.assertEqual(recent_variants(conn, self.profile_id, 'shop', 'A1'), [])
            self.assertEqual(recent_variants(conn, self.profile_id, 'station', 'A2'), [])
            self.assertEqual(recent_variants(conn, 'another-profile', 'shop', 'A2'), [])

    def test_least_recent_selection_uses_both_modes_after_all_variants_are_used(self):
        with transaction(self.db) as conn:
            seeds = [row[0] for row in conn.execute("SELECT id FROM speaking_scenario_variants "
                "WHERE scenario_id='shop' AND target_level='A2' AND enabled=1 ORDER BY id")]
        oldest = None
        for index, seed in enumerate(seeds):
            mode = 'live' if index % 2 else 'step'
            # Use the real repository to obtain a specific current catalogue snapshot.
            from repositories.speaking_repository import choose_variant
            with transaction(self.db) as conn:
                preview = choose_variant(conn, 'shop', level='A2', seed=seed)
            saved = self.start(mode, f'cycle-{index}', preview)
            oldest = oldest or seed
            with transaction(self.db, write=True) as conn:
                table = 'live_conversation_sessions' if mode == 'live' else 'step_conversation_sessions'
                conn.execute(f'UPDATE {table} SET created_at=? WHERE id=?', (1000 + index, saved['id']))
        for mode in ('live', 'step'):
            self.assertEqual(self.options(mode)['seed'], oldest)

    def test_another_situation_excludes_current_preview_without_recording_a_play(self):
        first = self.options()
        self.assertNotEqual(self.options(exclude=first['seed'])['seed'], first['seed'])
        with transaction(self.db) as conn:
            self.assertEqual(recent_variants(conn, self.profile_id, 'shop', 'A2'), [])

    def test_saved_curriculum_and_facts_survive_catalogue_changes(self):
        for mode in ('live', 'step'):
            preview = self.options(mode)
            self.assertEqual(preview['curriculum_context']['topic_id'], 'shopping')
            self.assertEqual(preview['curriculum_context']['target_level'], 'A2')
            self.assertTrue(preview['learning_contract']['requirements'])
            saved = self.start(mode, f'snapshot-{mode}', preview)
            with transaction(self.db, write=True) as conn:
                payload = json.loads(conn.execute('SELECT payload_json FROM speaking_scenario_variants WHERE id=?',
                                                  (preview['seed'],)).fetchone()[0])
                payload['curriculum_context']['activity_brief'] = 'A future curriculum revision'
                conn.execute('UPDATE speaking_scenario_variants SET payload_json=? WHERE id=?',
                             (json.dumps(payload), preview['seed']))
            again = self.client.get(f'/api/v1/{mode}-conversations/{saved["id"]}')
            self.assertEqual(again.status_code, 200, again.json)
            self.assertEqual(again.json['scenario'], preview)


if __name__ == '__main__':
    unittest.main()
