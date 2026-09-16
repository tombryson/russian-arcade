"""Fly-only entry point. Local development continues to use app.create_app.

Supports a private installation behind HTTP Basic auth, or an isolated sample
demo with providers disabled. Local files and credentials are never published.
"""
import hashlib
import hmac
import os
from pathlib import Path
import sqlite3
from contextlib import closing

from werkzeug.wrappers import Request, Response
from werkzeug.middleware.proxy_fix import ProxyFix


class PrivateSite:
    """Protect HTML, APIs and every asset before Flask's profile middleware."""

    def __init__(self, application, username, password, database, hostname, public=False):
        self.application = application
        self.username = hashlib.sha256(username.encode()).digest()
        self.password = hashlib.sha256(password.encode()).digest()
        self.database = database
        self.hostname = hostname
        self.public = public

    def __call__(self, environ, start_response):
        request = Request(environ)
        if request.host != self.hostname:
            return Response('Unknown host', status=400)(environ, start_response)
        original_start_response = start_response

        def start_response(status, headers, exc_info=None):
            if request.is_secure:
                headers = [(key, value) for key, value in headers if key.lower() != 'strict-transport-security']
                headers.append(('Strict-Transport-Security', 'max-age=31536000'))
            return original_start_response(status, headers, exc_info)
        if request.path == '/healthz' and request.method in ('GET', 'HEAD'):
            try:
                uri = Path(self.database).resolve().as_uri() + '?mode=ro'
                with closing(sqlite3.connect(uri, uri=True, timeout=2)) as conn:
                    conn.execute('SELECT MAX(version) FROM schema_migrations').fetchone()
                response = Response('ok\n')
            except sqlite3.Error:
                response = Response('unavailable\n', status=503)
        else:
            credentials = request.authorization
            valid = self.public
            if credentials and credentials.type == 'basic':
                username = hashlib.sha256((credentials.username or '').encode()).digest()
                password = hashlib.sha256((credentials.password or '').encode()).digest()
                valid = hmac.compare_digest(username, self.username) & hmac.compare_digest(password, self.password)
            if valid:
                # Do not forward site credentials to application/provider code.
                environ.pop('HTTP_AUTHORIZATION', None)
                return self.application(environ, start_response)
            response = Response('Sign in to Russian Arcade.\n', status=401,
                                headers={'WWW-Authenticate': 'Basic realm="Russian Arcade", charset="UTF-8"'})
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response(environ, start_response)


def settings():
    """Validate before opening or migrating any database."""
    public = os.environ.get('PUBLIC_DEMO') == 'true'
    required = ('FLASK_SECRET_KEY', 'HOSTED_HOSTNAME', 'VOCAB_DB_PATH')
    if not public:
        required += ('HOSTED_ACCESS_USERNAME', 'HOSTED_ACCESS_PASSWORD')
    if any(not os.environ.get(key) for key in required):
        raise RuntimeError('Hosted deployment requires session/access secrets, hostname and database path.')
    if len(os.environ['FLASK_SECRET_KEY']) < 32 or (not public and len(os.environ['HOSTED_ACCESS_PASSWORD']) < 24):
        raise RuntimeError('Use a generated session secret (32+ characters) and access password (24+ characters).')
    if not Path(os.environ['VOCAB_DB_PATH']).is_file():
        raise RuntimeError('Import a verified database snapshot onto the volume before starting the app.')
    return {key: os.environ[key] for key in required}


def create_hosted_app():
    values = settings()
    public = os.environ.get('PUBLIC_DEMO') == 'true'
    from app import create_app
    overrides = {
        'SECRET_KEY': values['FLASK_SECRET_KEY'],
        'SESSION_COOKIE_SECURE': True,
        'WORD_POST_ALLOWED_HOSTS': (values['HOSTED_HOSTNAME'],),
        'WORD_POST_HOUSEHOLD_ENABLED': False,
    }
    if public:
        overrides.update(OPENAI_API_KEY='', OPENROUTER_API_KEY='', ELEVENLABS_API_KEY='',
                         YANDEX_API_KEY='', GOOGLE_DRIVE_AUTO_AUTH=False, PUBLIC_DEMO=True,
                         MAX_CONTENT_LENGTH=16384)
    app = create_app(overrides)
    if public:
        from public_demo import install_demo
        install_demo(app)
    app.wsgi_app = PrivateSite(app.wsgi_app, values.get('HOSTED_ACCESS_USERNAME', ''),
                              values.get('HOSTED_ACCESS_PASSWORD', ''), values['VOCAB_DB_PATH'],
                              values['HOSTED_HOSTNAME'], public=public)
    # Fly terminates HTTPS; trust its protocol header, never forwarded host/IP.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=0, x_proto=1, x_host=0, x_port=0, x_prefix=0)
    return app


def main():
    if os.environ.get('PUBLIC_DEMO') == 'true':
        from public_demo import prepare_demo
        prepare_demo()
    values = settings()
    from migrations import upgrade_database
    upgrade_database(values['VOCAB_DB_PATH'])  # Transactional, with pre-migration backup.
    # One process owns in-process background jobs. Threads serve concurrent requests.
    os.execvp('gunicorn', ['gunicorn', '--bind', '0.0.0.0:8080', '--workers', '1',
                         '--worker-class', 'gthread', '--threads', '8', '--timeout', '300',
                         '--graceful-timeout', '110', '--error-logfile', '-',
                         'hosted:create_hosted_app()'])


if __name__ == '__main__':
    main()
