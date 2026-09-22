"""Published listening assets must match the authored checkpoint variants."""
import hashlib
import json
from pathlib import Path
import unittest

from services.course_progression import course_catalogue
from services.speech_provider import audio_info


class CourseAudioTests(unittest.TestCase):
    def test_every_checkpoint_has_its_published_decodable_recording(self):
        static = Path(__file__).resolve().parents[1] / 'static'
        manifest = json.loads((static / 'audio/course/manifest.json').read_text())
        for chapter in course_catalogue()['chapters']:
            for variant in chapter['variants']:
                with self.subTest(variant=variant['id']):
                    clip = variant['listening']
                    record = manifest['clips'][variant['id']]
                    path = static / clip['audio_url'].removeprefix('/static/')
                    self.assertEqual(record['text_sha256'], hashlib.sha256(clip['transcript'].encode()).hexdigest())
                    self.assertEqual(record['audio_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
                    duration = audio_info(path)
                    self.assertGreater(duration, 3)
                    self.assertLess(duration, 30)
                    self.assertAlmostEqual(duration, record['duration'], places=1)
