"""Publication checks must exclude data even when it was accidentally tracked."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'release_snapshot.py'
SPEC = importlib.util.spec_from_file_location('release_snapshot', SCRIPT)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseSnapshotTests(unittest.TestCase):
    def test_private_tracked_files_cannot_pass_source_allowlist(self):
        for path in ('.env', '.env.local', '.git/config', '.codex/generated_images/art.png',
                     'scripts/API_key.py', 'flask_vocab_app/credentials.json',
                     'flask_vocab_app/vocab.db', 'flask_vocab_app/vocab.db-wal',
                     'flask_vocab_app/static/media/sentence_1.mp3',
                     'flask_vocab_app/static/audio/course/learner-recording.mp3',
                     'flask_vocab_app/static/uploads/lesson.png', 'docs/tutor.pdf',
                     'flask_vocab_app/ui/node_modules/source.js', 'instance/config.py'):
            with self.subTest(path=path):
                self.assertIsNotNone(release.exclusion(path))

    def test_reviewed_source_and_authored_assets_are_included(self):
        for path in ('.env.example', '.github/workflows/security.yml', 'README.md',
                     'scripts/release_snapshot.py', 'flask_vocab_app/migrations/039_game_shop.sql',
                     'flask_vocab_app/ui/src/assets/barsik-shop-v1.png',
                     'flask_vocab_app/content/deliveries/map-blocks.json',
                     'flask_vocab_app/static/audio/course/manifest.json',
                     'flask_vocab_app/static/audio/course/a1-post-office-v1.mp3',
                     'flask_vocab_app/static/audio/deliveries/0123456789abcdef01234567.mp3'):
            with self.subTest(path=path):
                self.assertIsNone(release.exclusion(path))

    def test_export_refuses_to_follow_file_or_directory_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'source.txt').write_text('test')
            (root / 'link.txt').symlink_to(root / 'source.txt')
            (root / 'linked-dir').symlink_to(root, target_is_directory=True)
            for path in ('link.txt', 'linked-dir/source.txt'):
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'Symlink'):
                    release.read_file(root, path)

    def test_changed_source_cannot_be_exported_under_an_old_scan_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'source'
            root.mkdir()
            (root / 'README.md').write_text('changed after scan')
            report = {'files': [{'path': 'README.md', 'sha256': hashlib.sha256(b'old').hexdigest(), 'executable': False}]}
            with self.assertRaisesRegex(ValueError, 'Source changed during export'):
                release.copy_snapshot(root, Path(temp) / 'export', report)

    def test_existing_checkout_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(FileExistsError):
                release.copy_snapshot(root, root, {'files': []})
