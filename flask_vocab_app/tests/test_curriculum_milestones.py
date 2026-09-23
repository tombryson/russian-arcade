"""Curriculum and Profile show the same earned milestones as Journey."""
import json
import sqlite3
import unittest
from flask.testing import FlaskClient

from tests.support import isolated_app


class CurriculumMilestoneTests(unittest.TestCase):
    def setUp(self):
        self.app = isolated_app(self, demo=False)
        self.client = self.app.test_client()
        self.state = self.client.get('/api/v1/course').json
        self.headers = {'X-CSRF-Token': self.state['csrf_token']}

    def test_public_catalogue_has_all_topics_without_assigning_progress(self):
        visitor = FlaskClient(self.app)
        html = visitor.get('/curriculum').text
        self.assertEqual(html.count('class="curriculum-milestone"'), 4)
        self.assertEqual(html.count('class="curriculum-topic"'), 50)
        self.assertFalse('milestones complete' in html)
        self.assertFalse('curriculum-milestone-count' in html)
        with visitor.session_transaction() as session:
            self.assertNotIn('personal_access_id', session)

    def test_pass_and_profile_switch_are_reflected_without_new_rewards(self):
        first = self.state['chapters'][0]
        response = self.client.post(f'/api/v1/course/chapters/{first["id"]}/checkpoint',
                                    json={'request_id': 'curriculum-start', 'challenge': True,
                                          'release_id': self.state['release_id']}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        attempt = response.json
        with sqlite3.connect(self.app.config['DB_PATH']) as conn:
            frozen = json.loads(conn.execute('SELECT frozen_json FROM course_checkpoint_attempts WHERE id=?',
                                            (attempt['id'],)).fetchone()[0])
        answers = {item['id']: item['answer'] for item in frozen['variant']['questions']}
        self.client.post(f'/api/v1/course/checkpoints/{attempt["id"]}/listened', json={}, headers=self.headers)
        checked = self.client.post(f'/api/v1/course/checkpoints/{attempt["id"]}/answer',
                                   json={'answers': answers, 'submission_id': 'curriculum-submit'}, headers=self.headers)
        self.assertEqual(checked.status_code, 200)
        self.assertTrue(checked.json['result']['passed'])
        state = self.client.get('/api/v1/course').json
        self.assertEqual(state['completed_milestones'], 1)
        html = self.client.get('/curriculum').text
        self.assertIn('A1 · 1 of 4 milestones complete', html)
        self.assertIn('1 of 4 milestones complete', self.client.get('/post/profiles').text)
        self.assertIn(f'data-profile-id="{state["profile_id"]}"', html)
        self.assertNotIn(attempt['letter'], html)
        for table in ('progression_events', 'native_reviews'):
            with sqlite3.connect(self.app.config['DB_PATH']) as conn:
                exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
                if exists:
                    self.assertEqual(conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0], 0)
        created = self.client.post('/api/v1/user-session/profiles', json={'display_name': 'Another learner'},
                                   headers=self.headers)
        self.assertEqual(created.status_code, 201)
        html = self.client.get('/curriculum').text
        self.assertIn('A1 · 0 of 4 milestones complete', html)
        self.assertNotIn(f'data-profile-id="{state["profile_id"]}"', html)
        self.assertIn('0 of 4 milestones complete', self.client.get('/post/profiles').text)
        stale = self.client.get('/curriculum', headers={'X-Profile-ID': state['profile_id'], 'HX-Target': 'mainContent'})
        self.assertEqual(stale.status_code, 409)
        self.assertFalse('milestones complete' in stale.text)

    def test_null_release_is_not_an_implicit_legacy_start(self):
        response = self.client.post(f'/api/v1/course/chapters/{self.state["chapters"][0]["id"]}/checkpoint',
                                    json={'request_id': 'invalid-release', 'challenge': True, 'release_id': None},
                                    headers=self.headers)
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
