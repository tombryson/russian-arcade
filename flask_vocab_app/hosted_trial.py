"""Verified GitHub sign-in and isolated workspaces for the hosted AI trial.

The public sample application remains usable without signing in. A verified
GitHub account gets a separate database, media directory and Flask session.
Provider credentials never pass through the browser or the identity database.
"""
from collections import OrderedDict
from contextlib import closing, contextmanager
from hashlib import sha256
import base64
import hmac
import json
from pathlib import Path
import secrets
import shutil
import sqlite3
import threading
import time
from urllib.parse import urlencode, urlsplit

import requests
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.wrappers import Request, Response
from werkzeug.utils import redirect
from werkzeug.wsgi import ClosingIterator

COOKIE = '__Host-russian-arcade-trial'
FLOW_COOKIE = '__Host-russian-arcade-oauth'
SESSION_SECONDS = 7 * 24 * 3600
FLOW_SECONDS = 600


def safe_return_url(value):
    """Only absolute paths on this application are accepted after sign-in."""
    if (not isinstance(value, str) or not value.startswith('/') or value.startswith('//')
            or '\\' in value or any(ord(char) < 32 for char in value)
            or len(value) > 2000):
        return '/post/'
    parts = urlsplit(value)
    if parts.scheme or parts.netloc or parts.path.startswith('/trial/'):
        return '/post/'
    return value


class TrialIdentityError(ValueError):
    pass


class GitHubIdentity:
    """OAuth authorization-code flow with PKCE; no repository scopes requested."""
    def __init__(self, client_id, client_secret, callback, *, http=requests):
        self.client_id, self.client_secret, self.callback = client_id, client_secret, callback
        self.http = http

    @property
    def configured(self):
        return bool(self.client_id and self.client_secret)

    def authorization_url(self, state, verifier):
        challenge = base64.urlsafe_b64encode(sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        return 'https://github.com/login/oauth/authorize?' + urlencode({
            'client_id': self.client_id, 'redirect_uri': self.callback,
            'state': state, 'code_challenge': challenge, 'code_challenge_method': 'S256',
            'scope': '',
        })

    def verify(self, code, verifier):
        """Use the token once to identify its user, then discard it."""
        try:
            response = self.http.post('https://github.com/login/oauth/access_token',
                data={'client_id': self.client_id, 'client_secret': self.client_secret,
                      'redirect_uri': self.callback, 'code': code, 'code_verifier': verifier},
                headers={'Accept': 'application/json'}, timeout=15)
            response.raise_for_status()
            token = response.json().get('access_token')
            if not isinstance(token, str) or not token:
                raise TrialIdentityError('GitHub did not complete sign-in. Please try again.')
            response = self.http.get('https://api.github.com/user',
                headers={'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer ' + token,
                         'X-GitHub-Api-Version': '2022-11-28'}, timeout=15)
            response.raise_for_status()
            user = response.json()
        except (requests.RequestException, ValueError, TypeError) as error:
            raise TrialIdentityError('GitHub sign-in is unavailable. Please try again.') from error
        if type(user.get('id')) is not int or user['id'] <= 0 or user.get('type') != 'User':
            raise TrialIdentityError('A personal GitHub account is required.')
        return 'github:' + str(user['id']), str(user.get('login') or 'Learner')[:60]


def tenant_settings(root, identity, *, secret, ledger_path, hostname):
    """Paths are derived exclusively from a server-verified identity."""
    digest = sha256(identity.encode()).hexdigest()
    directory = Path(root).resolve() / 'tenants' / digest
    return {
        'HOSTED_AI_TRIAL': True, 'PUBLIC_DEMO': False,
        'AI_TRIAL_IDENTITY': identity, 'AI_TRIAL_LEDGER_PATH': str(Path(ledger_path).resolve()),
        'SECRET_KEY': hmac.new(secret.encode(), ('tenant:' + identity).encode(), 'sha256').hexdigest(),
        'DB_PATH': str(directory / 'vocab.db'), 'APP_MEDIA_DIR': str(directory / 'media'),
        'UPLOAD_FOLDER': str(directory / 'uploads'), 'WORD_POST_ASSET_DIR': str(directory / 'assets'),
        'ANKI_MEDIA_DIR': str(directory / 'anki-media'), 'SESSION_FILE_DIR': str(directory / 'sessions'),
        'SESSION_COOKIE_NAME': '__Host-ra-session-' + digest[:16],
        'SESSION_COOKIE_SECURE': True, 'SESSION_COOKIE_HTTPONLY': True, 'SESSION_COOKIE_SAMESITE': 'Lax',
        'WORD_POST_HOUSEHOLD_ENABLED': False, 'WORD_POST_ALLOWED_HOSTS': (hostname,),
        'GOOGLE_DRIVE_AUTO_AUTH': False, 'GOOGLE_DRIVE_FILE_ID': '',
        'GOOGLE_DRIVE_CREDENTIALS_FILE': str(directory / 'disabled-drive-credentials.json'),
        'GOOGLE_DRIVE_TOKEN_FILE': str(directory / 'disabled-drive-token.json'),
        'GOOGLE_DRIVE_CACHE_FILE': str(directory / 'disabled-drive-cache.txt'),
        'MAX_CONTENT_LENGTH': 12 * 1024 * 1024, 'LESSON_MAX_PAGES': 12,
    }


def seed_trial_workspace(config, display_name):
    """Seed authored vocabulary and sample cards, never a personal DB snapshot."""
    from migrations import upgrade_database
    from repositories.learning_repository import transaction
    from services.sample_vocabulary import seed_sample_items, sample_needs_repair
    from services.learning_assets import LocalAssetStore
    from services.learning_content import ContentService
    from services.personal_learning import personal_access
    database = config['DB_PATH']
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    upgrade_database(database, backup=Path(database).is_file())
    with closing(sqlite3.connect(database)) as existing:
        needs_repair = sample_needs_repair(existing)
        if needs_repair:
            backup = str(database) + '.before-vocabulary-repair-' + secrets.token_hex(6) + '.bak'
            with closing(sqlite3.connect(backup)) as snapshot:
                existing.backup(snapshot)
    with transaction(database, write=True) as conn:
        seeded = conn.execute("SELECT 1 FROM learning_content_versions WHERE content_id='trial-sample' AND status='published'").fetchone()
        # Repair earlier sample vocabulary even when its published deck exists.
        # Card IDs, published content and review schedules remain unchanged.
        items = seed_sample_items(conn, 'trial-sample')
    if seeded:
        return
    credential = personal_access(database)
    content = ContentService(database, LocalAssetStore(config['WORD_POST_ASSET_DIR']))
    version = content.import_draft(dict(schema_version=2, id='trial-sample', kind='deck',
        title='First Russian words · sample cards', source='Authored sample content, no personal records.', items=items))
    content.publish(credential, version, 'Russian Arcade demo')
    with transaction(database, write=True) as conn:
        conn.execute("UPDATE learning_profiles SET display_name=? WHERE id='personal-learning'", (display_name,))
        conn.execute('DELETE FROM household_access')


def install_trial_session(app):
    """A hosted identity selects its own single profile, never local accounts."""
    from flask import jsonify, redirect as flask_redirect, request, session
    from services.personal_learning import PersonalSessions, PERSONAL_PROFILE
    sessions = PersonalSessions(app.config['DB_PATH'], lifetime=3600)

    def boundary():
        if request.path == '/':
            return flask_redirect('/post/')
        if request.blueprint == 'flashcards' or request.path in {
            '/sync', '/sync/preview', '/sync/history', '/sync_vocab', '/sanitize_vocab',
            '/apply_sanitization', '/edit_word', '/delete_word', '/add_word',
        } or request.args.get('source', 'db') != 'db':
            return jsonify(error={'code': 'local_tool', 'message': 'Drive and Anki tools run in a local installation.'}), 403
        if request.path in {'/post/profiles', '/post/household'}:
            return flask_redirect('/trial/account')
        if request.endpoint in {'user_sessions.create_profile', 'user_sessions.select_profile',
                                'user_sessions.actions', 'user_sessions.end'}:
            return jsonify(error={'code': 'hosted_identity',
                'message': 'Manage your signed-in account from the account menu.'}), 403
        state = sessions.state(session.get('personal_access_id'))
        if not state['profile'] or state['profile']['id'] != PERSONAL_PROFILE:
            session['personal_access_id'] = sessions.select(PERSONAL_PROFILE, session.get('personal_access_id'))
            session.permanent = True
    app.before_request_funcs.setdefault(None, []).insert(0, boundary)

    @app.after_request
    def trial_notice(response):
        if response.mimetype == 'text/html' and not response.direct_passthrough:
            body = response.get_data(as_text=True)
            if '</head>' in body and '</body>' in body:
                notice = ('<details class="demo-notice"><summary>AI demo</summary>'
                          '<p>The shared AI allowance is US$1 a day and US$20 a month. '
                          'Your practice is saved in your account. '
                          '<a href="/trial/account">Account and sign out</a></p></details>')
                body = body.replace('</head>', '<link rel="stylesheet" href="/static/css/public_demo.css?v=2"></head>', 1)
                response.set_data(body.replace('</body>', notice + '</body>', 1))
        return response


class HostedTrialDispatcher:
    """Route a verified browser to its persistent workspace on the same URL."""
    def __init__(self, public_application, app_factory, *, root, ledger_path, secret, hostname,
                 client_id='', client_secret='', app_config=None, enabled=False,
                 max_tenants=100, max_cached_apps=8, identity_provider=None,
                 budget=None, seed=seed_trial_workspace, clock=time.time):
        self.public_application, self.app_factory = public_application, app_factory
        self.root, self.ledger_path = Path(root).resolve(), Path(ledger_path).resolve()
        self.secret, self.hostname, self.enabled = secret, hostname, enabled
        self.config = dict(app_config or {})
        self.max_tenants, self.max_cached_apps = max_tenants, max_cached_apps
        self.clock, self.seed = clock, seed
        self.provider = identity_provider or GitHubIdentity(client_id, client_secret, 'https://' + hostname + '/trial/callback')
        self.signer = URLSafeTimedSerializer(secret, salt='russian-arcade-hosted-trial-v1')
        self.csrf_signer = URLSafeTimedSerializer(secret, salt='russian-arcade-hosted-trial-signout-v1')
        if max_tenants < 1 or max_cached_apps < 1:
            raise ValueError('Positive tenant and application limits are required.')
        self.cache, self.lock = OrderedDict(), threading.RLock()
        self.inflight, self.storage_reserved = {}, {}
        if budget is None:
            from services.ai_trial_budget import AITrialBudget
            budget = AITrialBudget(self.ledger_path, enabled=enabled)
        self.budget = budget
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.registry = self.root / 'identities.sqlite3'
        with self._db() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS identities(identity TEXT PRIMARY KEY, display_name TEXT NOT NULL, created_at INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, identity TEXT NOT NULL REFERENCES identities(identity), expires_at INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS oauth_flows(state_hash TEXT PRIMARY KEY, browser_hash TEXT NOT NULL, verifier TEXT NOT NULL, next_url TEXT NOT NULL, expires_at INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS auth_limits(bucket INTEGER PRIMARY KEY, attempts INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS request_limits(identity TEXT NOT NULL, kind TEXT NOT NULL, bucket INTEGER NOT NULL, attempts INTEGER NOT NULL, PRIMARY KEY(identity,kind,bucket));
            ''')

    @contextmanager
    def _db(self):
        conn = sqlite3.connect(self.registry, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        try:
            conn.execute('BEGIN IMMEDIATE')
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _session(self, request):
        value = request.cookies.get(COOKIE)
        if not value:
            return None
        try:
            token = self.signer.loads(value, max_age=SESSION_SECONDS)
            if not isinstance(token, str):
                return None
        except (BadSignature, SignatureExpired):
            return None
        with self._db() as conn:
            row = conn.execute('SELECT s.token_hash,s.identity,i.display_name FROM sessions s JOIN identities i USING(identity) WHERE token_hash=? AND expires_at>?',
                               (sha256(token.encode()).hexdigest(), int(self.clock()))).fetchone()
        return dict(row) if row else None

    def _response(self, response):
        response.headers.update({'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
            'Referrer-Policy': 'same-origin', 'X-Frame-Options': 'DENY',
            'Content-Security-Policy': "default-src 'none'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"})
        return response

    def _json(self, value, status=200):
        return self._response(Response(json.dumps(value), status=status, content_type='application/json'))

    def _page(self, title, message, status=200, *, account=None):
        from html import escape
        button = '<a href="/trial/sign-in">Sign in with GitHub</a>' if self.enabled and self.provider.configured else ''
        if account:
            csrf = self.csrf_signer.dumps(account['token_hash'])
            button = f'<form method="post" action="/trial/sign-out"><input type="hidden" name="csrf_token" value="{escape(csrf)}"><button type="submit">Sign out</button></form>'
        body = ('<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width, initial-scale=1">'
                f'<title>{escape(title)} · Russian Arcade</title><link rel="stylesheet" href="/static/css/public_demo.css"></head>'
                f'<body class="demo-unavailable"><main class="demo-unavailable-content"><h1>{escape(title)}</h1>'
                f'<p>{escape(message)}</p>{button}<p><a href="/post/">Back to Russian Arcade</a></p></main></body></html>')
        return self._response(Response(body, status=status, content_type='text/html; charset=utf-8'))

    def _begin(self, request):
        if not self.enabled or not self.provider.configured:
            return self._page('AI demo', 'AI sign-in is not configured yet. You can still explore the sample activities.', 503)
        state, browser, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(32), secrets.token_urlsafe(48)
        now = int(self.clock())
        with self._db() as conn:
            bucket = now // 60
            conn.execute('DELETE FROM auth_limits WHERE bucket<?', (bucket - 1,))
            conn.execute('INSERT INTO auth_limits(bucket,attempts) VALUES (?,1) ON CONFLICT(bucket) DO UPDATE SET attempts=attempts+1', (bucket,))
            if conn.execute('SELECT attempts FROM auth_limits WHERE bucket=?', (bucket,)).fetchone()[0] > 30:
                return self._page('Please wait', 'Too many sign-in attempts. Please try again in a minute.', 429)
            conn.execute('DELETE FROM oauth_flows WHERE expires_at<=?', (now,))
            conn.execute('INSERT INTO oauth_flows VALUES (?,?,?,?,?)',
                         (sha256(state.encode()).hexdigest(), sha256(browser.encode()).hexdigest(), verifier,
                          safe_return_url(request.args.get('next')), now + FLOW_SECONDS))
        response = self._response(redirect(self.provider.authorization_url(state, verifier)))
        response.set_cookie(FLOW_COOKIE, browser, max_age=FLOW_SECONDS, httponly=True, secure=True, samesite='Lax', path='/')
        return response

    def _callback(self, request):
        state, browser, code = request.args.get('state', ''), request.cookies.get(FLOW_COOKIE, ''), request.args.get('code', '')
        if not self.enabled or not self.provider.configured or not state or not browser or not code or len(code) > 512:
            return self._page('Sign-in not completed', 'Please start sign-in again.', 400)
        with self._db() as conn:
            flow = conn.execute('SELECT * FROM oauth_flows WHERE state_hash=? AND expires_at>?',
                                (sha256(state.encode()).hexdigest(), int(self.clock()))).fetchone()
            if not flow or not hmac.compare_digest(flow['browser_hash'], sha256(browser.encode()).hexdigest()):
                return self._page('Sign-in expired', 'Please start sign-in again.', 400)
            conn.execute('DELETE FROM oauth_flows WHERE state_hash=?', (flow['state_hash'],))
        try:
            identity, name = self.provider.verify(code, flow['verifier'])
            if not identity.startswith('github:') or not identity[7:].isdigit():
                raise TrialIdentityError('A verified GitHub identity is required.')
            with self._db() as conn:
                existing = conn.execute('SELECT 1 FROM identities WHERE identity=?', (identity,)).fetchone()
                if not existing and conn.execute('SELECT COUNT(*) FROM identities').fetchone()[0] >= self.max_tenants:
                    return self._page('Demo capacity reached', 'The demo is full for now. Sample activities are still available.', 503)
                conn.execute('INSERT INTO identities VALUES (?,?,?) ON CONFLICT(identity) DO UPDATE SET display_name=excluded.display_name',
                             (identity, name[:60], int(self.clock())))
            self.budget.authorize_identity(identity)
            self._application(identity, name)
        except (TrialIdentityError, ValueError) as error:
            # Never expose provider bodies, tokens, file paths or secret values.
            return self._page('Sign-in not completed', 'The AI demo could not be opened. Please try again later.', 503)
        token = secrets.token_urlsafe(40)
        with self._db() as conn:
            conn.execute('DELETE FROM sessions WHERE expires_at<=?', (int(self.clock()),))
            conn.execute('INSERT INTO sessions VALUES (?,?,?)',
                         (sha256(token.encode()).hexdigest(), identity, int(self.clock()) + SESSION_SECONDS))
        response = self._response(redirect(flow['next_url']))
        response.set_cookie(COOKIE, self.signer.dumps(token), max_age=SESSION_SECONDS, httponly=True, secure=True, samesite='Lax', path='/')
        response.delete_cookie(FLOW_COOKIE, secure=True, httponly=True, samesite='Lax', path='/')
        return response

    def _busy(self, identity, app):
        if self.inflight.get(identity, 0) or app.extensions.get('trial_futures'):
            return True
        learning = app.extensions.get('learning', {})
        lessons, live = learning.get('lessons'), learning.get('live_conversation')
        return bool((lessons and lessons._active) or (live and live.connections)
                    or (live and live.reviews and live.reviews.running))

    def _track_executors(self, app):
        pending = app.extensions['trial_futures'] = set()
        executors = app.extensions['trial_executors'] = []
        learning = app.extensions.get('learning', {})
        live = learning.get('live_conversation')
        for service in (live, live.reviews if live else None, learning.get('conversation')):
            if service is None:
                continue
            executor = service.executor
            executors.append(executor)
            submit = executor.submit
            def tracked_submit(*args, _submit=submit, **kwargs):
                with self.lock:
                    future = _submit(*args, **kwargs)
                    pending.add(future)
                def finished(completed):
                    with self.lock:
                        pending.discard(completed)
                future.add_done_callback(finished)
                return future
            executor.submit = tracked_submit

    def _admit(self, identity, request):
        """Bound cheap requests and disk growth before reaching application code."""
        now = int(self.clock())
        mutation = request.method not in ('GET', 'HEAD', 'OPTIONS') or request.path == '/sentence/generate'
        with self._db() as conn:
            conn.execute('DELETE FROM request_limits WHERE bucket<? AND kind!=?', (now // 60 - 1, 'daily-writes'))
            conn.execute("DELETE FROM request_limits WHERE kind='daily-writes' AND bucket<?", (now // 86400 - 1,))
            limits = [('requests', now // 60, 1200)]
            if mutation:
                limits += [('writes', now // 60, 180), ('daily-writes', now // 86400, 5000)]
            for kind, bucket, maximum in limits:
                conn.execute('INSERT INTO request_limits VALUES (?,?,?,1) ON CONFLICT(identity,kind,bucket) DO UPDATE SET attempts=attempts+1',
                             (identity, kind, bucket))
                count = conn.execute('SELECT attempts FROM request_limits WHERE identity=? AND kind=? AND bucket=?',
                                     (identity, kind, bucket)).fetchone()[0]
                if count > maximum:
                    return self._json({'error': {'code': 'rate_limited', 'message': 'Please pause for a moment before trying again.'}}, 429), 0
        if not mutation:
            return None, 0
        length = request.content_length or 0
        if length > 12 * 1024 * 1024:
            return self._json({'error': {'code': 'upload_limit', 'message': 'Choose a file smaller than 12 MB.'}}, 413), 0
        # Let callers finish a call or remove data even when storage is full.
        if request.path.endswith(('/delete', '/finish')) or request.method == 'DELETE':
            return None, 0
        directory = self.root / 'tenants' / sha256(identity.encode()).hexdigest()
        occupied = sum(path.stat().st_size for path in directory.rglob('*') if path.is_file() and not path.is_symlink())
        reservation = max(length, 1024 * 1024)
        if occupied + self.storage_reserved.get(identity, 0) + reservation > 100 * 1024 * 1024 or shutil.disk_usage(self.root).free - reservation < 256 * 1024 * 1024:
            return self._json({'error': {'code': 'storage_limit', 'message': 'The demo workspace is full. Saved activities remain available.'}}, 507), 0
        self.storage_reserved[identity] = self.storage_reserved.get(identity, 0) + reservation
        return None, reservation

    def _application(self, identity, name):
        with self.lock:
            if identity in self.cache:
                self.cache.move_to_end(identity)
                return self.cache[identity]
            if len(self.cache) >= self.max_cached_apps:
                idle = next(((key, value) for key, value in self.cache.items() if not self._busy(key, value)), None)
                if idle is None:
                    raise TrialIdentityError('The demo is busy. Please try again shortly.')
                key, old = idle
                self.cache.pop(key)
                for executor in old.extensions.get('trial_executors', []):
                    executor.shutdown(wait=False, cancel_futures=False)
            config = dict(self.config)
            # Security and storage boundaries always override caller defaults.
            config.update(tenant_settings(self.root, identity, secret=self.secret,
                                         ledger_path=self.ledger_path, hostname=self.hostname))
            self.seed(config, name)
            app = self.app_factory(config)
            install_trial_session(app)
            self._track_executors(app)
            self.cache[identity] = app
            return app

    def __call__(self, environ, start_response):
        request = Request(environ)
        if request.host != self.hostname:
            return self._response(Response('Unknown host', status=400))(environ, start_response)
        try:
            account = self._session(request)
            if request.path == '/trial/status' and request.method == 'GET':
                response = self._json({'authenticated': bool(account), 'enabled': self.enabled,
                    'configured': self.provider.configured, 'display_name': account['display_name'] if account else None,
                    'sign_in_url': '/trial/sign-in', 'account_url': '/trial/account'})
            elif request.path == '/trial/account' and request.method == 'GET':
                response = self._page('Your demo account' if account else 'Try the AI activities',
                    f"Signed in as {account['display_name']}. Your practice and uploads stay in this account. The shared AI allowance is US$1 per day and US$20 per month across all visitors."
                    if account else 'Sign in with GitHub to use the AI activities. No repository access is requested.', account=account)
            elif request.path == '/trial/sign-in' and request.method == 'GET':
                response = self._begin(request)
            elif request.path == '/trial/callback' and request.method == 'GET':
                response = self._callback(request)
            elif request.path == '/trial/sign-out' and request.method == 'POST':
                valid_origin = request.headers.get('Origin') in (None, 'https://' + self.hostname) and request.headers.get('Sec-Fetch-Site') != 'cross-site'
                try:
                    token = self.csrf_signer.loads(request.form.get('csrf_token', ''), max_age=3600)
                except (BadSignature, SignatureExpired):
                    token = None
                if not valid_origin or not account or token != account['token_hash']:
                    response = self._page('Sign-out expired', 'Open your account and try again.', 403)
                else:
                    with self._db() as conn:
                        conn.execute('DELETE FROM sessions WHERE token_hash=?', (account['token_hash'],))
                    response = self._response(redirect('/post/'))
                    response.delete_cookie(COOKIE, secure=True, httponly=True, samesite='Lax', path='/')
            elif request.path.startswith('/trial/'):
                response = self._response(Response('Not found', status=404))
            elif account:
                identity = account['identity']
                with self.lock:
                    app = self._application(identity, account['display_name'])
                    rejected, reserved = self._admit(identity, request)
                    if rejected is not None:
                        return rejected(environ, start_response)
                    self.inflight[identity] = self.inflight.get(identity, 0) + 1
                def release():
                    with self.lock:
                        self.inflight[identity] -= 1
                        self.storage_reserved[identity] = self.storage_reserved.get(identity, 0) - reserved
                try:
                    result = app(environ, start_response)
                except BaseException:
                    release()
                    raise
                return ClosingIterator(result, release)
            else:
                return self.public_application(environ, start_response)
        except (sqlite3.Error, OSError, TrialIdentityError):
            response = self._page('Demo temporarily unavailable', 'Please try again shortly.', 503)
        return response(environ, start_response)
