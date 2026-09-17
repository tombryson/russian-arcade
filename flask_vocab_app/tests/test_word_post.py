import json
import html as html_module
import os
import re
from pathlib import Path
import tempfile
import unittest
from flask.testing import FlaskClient

from blueprints.word_post import build_assets, BuildUnavailable
from tests.support import isolated_app
from utils.navigation import activity_navigation


class WordPostTests(unittest.TestCase):
    def setUp(self):
        self.app = isolated_app(self)
        self.client = self.app.test_client()
        temporary = tempfile.TemporaryDirectory(prefix='word-post-build-')
        self.addCleanup(temporary.cleanup)
        self.dist = Path(temporary.name)
        (self.dist / '.vite').mkdir()
        (self.dist / 'assets').mkdir()
        self.app.config['WORD_POST_DIST_DIR'] = str(self.dist)
        self.app.config['WORD_POST_ENABLED'] = True
        self.app.config['WORD_POST_CATALOGUE_ENABLED'] = False
        for filename in ('main-test.js', 'shared-test.js', 'main-test.css', 'shared-test.css'):
            (self.dist / 'assets' / filename).write_text('/* fixture */')
        self.manifest = {
            'src/main.tsx': {'file': 'assets/main-test.js', 'css': ['assets/main-test.css'], 'imports': ['shared']},
            'shared': {'file': 'assets/shared-test.js', 'css': ['assets/main-test.css', 'assets/shared-test.css']},
        }
        self.write_manifest()

    def write_manifest(self):
        (self.dist / '.vite/manifest.json').write_text(json.dumps(self.manifest))

    def test_brand_icons_load_without_a_profile_cookie_but_private_media_stays_protected(self):
        # Browsers can request favicons separately from the page session.
        for household in (False, True):
            self.app.config.update(WORD_POST_HOUSEHOLD_ENABLED=household, SECRET_KEY='test-only-' * 4)
            client = FlaskClient(self.app)
            for filename, mimetypes in (('favicon.svg', ('image/svg+xml',)),
                                       ('favicon.ico', ('image/x-icon', 'image/vnd.microsoft.icon')),
                                       ('apple-touch-icon.png', ('image/png',))):
                with client.get('/static/images/' + filename) as response:
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(response.mimetype, mimetypes)
                    self.assertNotIn('Set-Cookie', response.headers)
            self.assertEqual(client.get('/static/media/private.mp3').status_code, 302)
            self.assertEqual(client.get('/static/images/private.png').status_code, 302)

    def test_page_owns_its_document_and_assets_without_initializing_services(self):
        response = self.client.get('/post/', headers={'HX-Request': 'true'})
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertTrue(html.startswith('<!doctype html>'))
        for legacy in ('bootstrap', 'htmx', 'app_shell', 'https://', 'cdn.'):
            self.assertNotIn(legacy, html)
        self.assertEqual(html.count('/post/assets/main-test.css'), 1)
        self.assertIn('/post/assets/shared-test.css', html)
        self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        for service in self.app.extensions['services'].values():
            self.assertIsNone(service.instance)

    def test_scene_artwork_is_public_without_opening_private_static_media(self):
        for household in (False, True):
            self.app.config.update(WORD_POST_HOUSEHOLD_ENABLED=household, SECRET_KEY='test-only-' * 4)
            client = FlaskClient(self.app)
            for name in ('cat', 'table', 'book', 'book-upright', 'walking', 'taxi',
                         'walking-away', 'taxi-moving', 'taxi-away', 'doorway-inside', 'courtyard-in', 'courtyard-out'):
                with client.get(f'/static/images/scene-builder/{name}-v1.webp') as response:
                    self.assertEqual(response.status_code, 200, name)
                    self.assertEqual(response.mimetype, 'image/webp')
                    self.assertNotIn('Set-Cookie', response.headers)
            self.assertEqual(client.get('/static/images/scene-builder/private.png').status_code, 302)
            self.assertEqual(client.get('/static/images/scene-builder/../../media/private.mp3').status_code, 302)

    def test_missing_or_invalid_build_has_a_recoverable_setup_page(self):
        manifest_path = self.dist / '.vite/manifest.json'
        for content in ('', 'null', '{}', '[]', '{"src/main.tsx": 1}'):
            manifest_path.write_text(content)
            response = self.client.get('/post/')
            self.assertEqual(response.status_code, 503)
            self.assertIn('npm run build', response.get_data(as_text=True))
        manifest_path.unlink()
        self.assertEqual(self.client.get('/post/').status_code, 503)

    def test_native_and_flask_pages_share_the_localized_activity_menu(self):
        for language in ('en', 'ru'):
            with self.client.session_transaction() as session:
                session['ui_lang'] = language
            native = self.client.get('/post/').get_data(as_text=True)
            serialized = re.search(r'data-navigation="([^"]+)"', native).group(1)
            menu = json.loads(html_module.unescape(serialized))
            self.assertEqual(menu, activity_navigation(language))
            self.assertEqual(menu['activities'][0]['href'], '/post/#flashcards')
            self.assertEqual(menu['tools'][0]['href'], '/')
            legacy = self.client.get('/writing').get_data(as_text=True)
            for item in menu['activities'] + menu['tools']:
                self.assertIn(f'href="{item["href"]}"', legacy)
                self.assertIn(item['label'], legacy)

    def test_unsafe_missing_or_external_manifest_assets_are_rejected(self):
        for filename in ('../main.js', '/tmp/main.js', 'https://example.com/main.js', 'assets/../main.js', 'assets/missing.js'):
            self.manifest['src/main.tsx']['file'] = filename
            self.write_manifest()
            with self.subTest(filename=filename), self.assertRaises(BuildUnavailable):
                build_assets(self.dist)

    def test_shared_styles_are_deduplicated_and_cycles_terminate(self):
        self.manifest['shared']['imports'] = ['src/main.tsx']
        self.write_manifest()
        self.assertEqual(build_assets(self.dist)['styles'], ['main-test.css', 'shared-test.css'])

    def test_assets_are_cached_but_manifest_and_private_paths_are_inaccessible(self):
        response = self.client.get('/post/assets/main-test.js')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.cache_control.immutable)
        response.close()
        for path in ('/post/assets/../.vite/manifest.json', '/post/assets/.env', '/post/.vite/manifest.json', '/post/assets/main-test.js.map'):
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_preview_switch_and_catalogue_gate(self):
        self.assertEqual(self.client.get('/post/catalogue').status_code, 404)
        self.app.config['WORD_POST_CATALOGUE_ENABLED'] = True
        self.assertIn('data-view="catalogue"', self.client.get('/post/catalogue').get_data(as_text=True))
        self.app.config['WORD_POST_ENABLED'] = False
        for path in ('/post/', '/post/catalogue', '/post/assets/main-test.js'):
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_household_bootstrap_is_explicit_and_does_not_leak_a_profile(self):
        html = self.client.get('/post/').get_data(as_text=True)
        self.assertIn('data-household="false"', html)
        self.app.config.update(WORD_POST_HOUSEHOLD_ENABLED=True, SECRET_KEY='test-private-household-secret-at-least-32-chars')
        html = self.client.get('/post/').get_data(as_text=True)
        self.assertIn('data-household="true"', html)
        self.assertNotIn('csrf_token', html)

    def test_legacy_styles_use_their_own_entry_and_fall_back_without_breaking_routes(self):
        with self.app.test_request_context('/'):
            context = {}; self.app.update_template_context(context)
            self.assertEqual(context['arcade_styles'](), [])
        self.manifest['src/legacy.ts'] = {'file': 'assets/shared-test.js', 'css': ['assets/shared-test.css']}
        self.write_manifest()
        with self.app.test_request_context('/'):
            context = {}; self.app.update_template_context(context)
            self.assertEqual(context['arcade_styles'](), ['shared-test.css'])


class ProductionBuildTests(unittest.TestCase):
    def test_production_manifest_and_every_asset_are_served_locally(self):
        dist = Path(__file__).resolve().parents[1] / 'ui/dist'
        if not (dist / '.vite/manifest.json').is_file():
            if os.environ.get('WORD_POST_REQUIRE_BUILD') == '1':
                self.fail('CI requires npm ci and npm run build before Python tests')
            self.skipTest('Build the UI to exercise the production assets')
        app = isolated_app(self)
        app.config.update(WORD_POST_DIST_DIR=str(dist), WORD_POST_ENABLED=True)
        client = app.test_client()
        response = client.get('/post/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('https://', response.get_data(as_text=True))
        resolved = build_assets(dist)
        self.assertTrue(resolved['styles'])
        for file in (dist / 'assets').iterdir():
            with self.subTest(asset=file.name):
                response = client.get('/post/assets/' + file.name)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_data(), file.read_bytes())
                response.close()
                if file.suffix == '.css':
                    self.assertNotIn('@import', file.read_text())
                    self.assertNotIn('https://', file.read_text())
        for font in ('golos-text', 'unbounded'):
            response = client.get(f'/post/licenses/{font}-OFL.txt')
            self.assertEqual(response.status_code, 200)
            self.assertIn('SIL OPEN FONT LICENSE', response.get_data(as_text=True))
            response.close()


if __name__ == '__main__':
    unittest.main()
