"""Scene facts, component grading, owned snapshots and correction flows."""
import hashlib
import json
import unittest
from tests.game_fixtures import grant_earned_game_access
from unittest.mock import patch

from repositories.learning_repository import LearningError, identifier, transaction
from services.journey_games import assess_answer, normalise_answer
from services.scene_builder import FAMILIES, build_content, curriculum, options
from tests.support import select_test_profile
from tests import test_journey_games as existing


class SceneContentTests(unittest.TestCase):
    def test_each_focus_has_ten_distinct_complete_rounds_and_frozen_choices(self):
        all_rounds=curriculum()
        self.assertGreaterEqual(len(all_rounds),50)
        self.assertEqual(len({r['id'] for r in all_rounds}),len(all_rounds))
        for focus in (*FAMILIES,'mixed'):
            pack=build_content('seed',options({'grammar_focus':focus,'rounds':10}))
            self.assertEqual(len(pack['rounds']),10)
            self.assertEqual(len({r['id'] for r in pack['rounds']}),10)
            self.assertEqual(build_content('seed',options({'grammar_focus':focus,'rounds':10})),pack)
            for row in pack['rounds']:
                scene=row['scene_builder']
                self.assertEqual(len(scene['segments']),len(scene['slots'])+1)
                self.assertEqual(normalise_answer(row,row['expected_answer'],'scene-builder'),row['expected_answer'])
                self.assertTrue(assess_answer(row,row['expected_answer'])['correct'])
                self.assertEqual(row['answer_audio'][0]['audio_key'],hashlib.sha256(row['correct_sentence'].encode()).hexdigest())
                self.assertTrue(row['hint_ru'])
        mixed=build_content('seed',options({'grammar_focus':'mixed','rounds':10}))
        self.assertEqual({family:sum(r['scene_builder']['family']==family for r in mixed['rounds']) for family in FAMILIES},dict.fromkeys(FAMILIES,2))

    def test_case_and_preposition_are_graded_independently(self):
        row=next(r for r in curriculum() if r['id']=='position-under')
        result=assess_answer(row,['preposition:under','noun:prepositional'])
        self.assertEqual((result['score'],result['matched'],result['total']),(.5,1,2))
        result=assess_answer(row,['preposition:on','noun:instrumental'])
        self.assertEqual(result['score'],.5)
        for answer in (['preposition:under'],['noun:instrumental','preposition:under'],['preposition:invented','noun:instrumental']):
            with self.assertRaises(LearningError):
                normalise_answer(row,answer,'scene-builder')

    def test_options_reject_foreign_sources_and_invalid_counts(self):
        for value in ({'grammar_focus':'invented'},{'rounds':True},{'rounds':100},{'source':'vocabulary'},{'rounds':'5'}):
            with self.assertRaises(LearningError):
                options(value)

    def test_motion_caption_establishes_the_distinction_and_choices_are_stable(self):
        rows={r['id']:r for r in curriculum()}
        self.assertIn('taxi',rows['motion-arrive-ride']['scene_builder']['scenario'])
        self.assertIn('walked',rows['motion-arrive-foot']['scene_builder']['scenario'])
        self.assertIn('every morning',rows['motion-walk-habit']['scene_builder']['scenario'])
        self.assertEqual(rows['motion-walk-habit']['scene_builder']['slots'],rows['motion-ride-now']['scene_builder']['slots'])
        self.assertNotEqual(rows['motion-walk-habit']['expected_answer'],rows['motion-walk-now']['expected_answer'])


class SceneGameTests(unittest.TestCase):
    setUp=existing.JourneyGamesTests.setUp
    token=existing.JourneyGamesTests.token
    request=existing.JourneyGamesTests.request
    seed_lesson=existing.JourneyGamesTests.seed_lesson
    expected=existing.JourneyGamesTests.expected
    post=existing.JourneyGamesTests.post
    read=existing.JourneyGamesTests.read
    finish=existing.JourneyGamesTests.finish

    def start_scene(self,focus='location',request_id=None,**kwargs):
        select_test_profile(self.client)
        return self.request('/api/v1/games/scene-builder/start',{'request_id':request_id or identifier(),
            'options':{'grammar_focus':focus,'rounds':5},**kwargs})

    def test_starts_without_provider_or_vocabulary_and_hides_answer_until_check(self):
        self.seed_lesson('bag')
        grant_earned_game_access(self.db)
        with patch('services.journey_vocabulary.select_examples',side_effect=AssertionError('must not sample vocabulary')):
            state=self.start_scene()
        self.assertEqual(state['phase'],'play')
        row=self.expected(state['id'])[0]
        for secret in ('expected_answer','answer_audio','correct_sentence','translation','slot_explanations','vocabulary'):
            self.assertNotIn(secret,state['round'])
        key=row['answer_audio'][0]['audio_key']
        self.assertEqual(self.client.get('/api/v1/games/media/'+key+'/status').status_code,404)
        checked=self.post(state['id'],'answer',{'round_id':row['id'],'answer':row['expected_answer']})
        self.assertEqual(checked['result']['correct_sentence'],row['correct_sentence'])
        self.assertTrue(all(slot['correct'] for slot in checked['result']['slot_results']))
        self.assertEqual(self.client.get('/api/v1/games/media/'+key+'/status').status_code,200)
        other=self.app.test_client()
        self.assertEqual(other.get('/api/v1/games/sessions/'+state['id']).status_code,404)

    def test_resume_idempotency_and_new_focus_preserve_prior_snapshot(self):
        self.seed_lesson('bag')
        grant_earned_game_access(self.db)
        first=self.start_scene(request_id='scene-request-1')
        self.assertEqual(self.start_scene(request_id='scene-request-2')['id'],first['id'])
        second=self.start_scene('motion')
        self.assertNotEqual(first['id'],second['id'])
        self.assertEqual(self.start_scene(request_id='scene-request-1')['id'],first['id'])
        self.assertEqual(self.read(first['id'])['round'],first['round'])
        self.request('/api/v1/games/scene-builder/start',{'request_id':'scene-request-1','options':{'grammar_focus':'roles'}},status=409)

    def test_hint_retry_review_and_reward_keep_the_first_attempt(self):
        self.seed_lesson('bag')
        grant_earned_game_access(self.db)
        state=self.start_scene()
        sid=state['id']
        rounds=self.expected(sid)
        row=rounds[0]
        wrong=list(row['expected_answer'])
        wrong[-1]=next(c['id'] for c in row['scene_builder']['slots'][-1]['choices'] if c['id']!=wrong[-1])
        hinted=self.post(sid,'hint',{'round_id':row['id']})
        self.assertEqual(hinted['round']['hint_ru'],row['hint_ru'])
        checked=self.post(sid,'answer',{'round_id':row['id'],'answer':wrong})
        self.assertEqual([r['correct'] for r in checked['result']['slot_results']],[True,False])
        retry=self.post(sid,'retry',{'round_id':row['id']})
        self.assertIsNone(retry['result'])
        self.post(sid,'practice_answer',{'round_id':row['id'],'answer':row['expected_answer'],'request_id':'scene-correction-1'})
        self.post(sid,'practice_continue',{'round_id':row['id']})
        for row in rounds[1:]:
            self.post(sid,'answer',{'round_id':row['id'],'answer':row['expected_answer']})
            self.post(sid,'continue',{'round_id':row['id']})
        done=self.post(sid,'complete')
        self.assertEqual(done['summary']['missed_rounds'],1)
        self.assertEqual(done['reward']['amount'],3)
        self.assertTrue(done['study_available'])
        self.assertTrue(done['words'])
        self.assertEqual(self.post(sid,'complete')['reward']['amount'],3)
        self.assertEqual(self.post(sid,'review')['practice']['total'],1)
        with transaction(self.db) as conn:
            saved=conn.execute('SELECT answers_json FROM journey_game_sessions WHERE id=?',(sid,)).fetchone()[0]
            self.assertEqual(json.loads(saved)[rounds[0]['id']]['answer'],wrong)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM progression_events WHERE activity='journey_game' AND source_key=?",(sid,)).fetchone()[0],1)

    def test_catalogue_replaces_pairs_without_breaking_legacy_urls(self):
        select_test_profile(self.client)
        self.seed_lesson('bag')
        grant_earned_game_access(self.db)
        games=self.client.get('/api/v1/games').json['games']
        self.assertNotIn('pairs',{g['id'] for g in games})
        self.assertTrue(next(g for g in games if g['id']=='scene-builder')['unlocked'])
        legacy=self.request('/api/v1/games/pairs/start',{'request_id':'legacy-pairs-start','options':{'source':'first_steps'}})
        self.assertEqual(legacy['round']['mechanic'],'pairs')
        self.assertEqual(self.read(legacy['id'])['id'],legacy['id'])

    def test_authored_card_targets_resolve_to_the_lemma_and_exact_case(self):
        from services.first_steps_practice import _game_word
        with self.app.app_context(), transaction(self.db,write=True) as conn:
            for row in curriculum():
                with self.subTest(round=row['id']):
                    target=row['vocabulary']
                    word=_game_word(conn,target)
                    self.assertEqual(word['lemma'],target['lemma'])
                    self.assertEqual(word['form'],target['form'])
                    for key,value in target['grammar'].items():
                        self.assertEqual(word['tags'][key],value)
                    self.assertIn(target['form'].lower(),row['correct_sentence'].lower())


if __name__=='__main__':
    unittest.main()
