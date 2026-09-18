"""Disposable public preview: authored samples, isolated visitors, no providers."""
import hashlib
import os
from pathlib import Path
import tempfile

from flask import jsonify, redirect, request, session

from repositories.learning_repository import transaction, LearningError
from services.personal_learning import PersonalSessions, personal_access
from services.demo_limits import DemoLimits
from utils.household_access import csrf_token

MESSAGE = 'This public preview includes First steps, sample games, vocabulary and flashcard practice. AI generation, uploads and editing are available in your own installation.'

# New endpoints stay private even when added to an existing public blueprint.
READ_ENDPOINTS = frozenset({
    'word_post.home', 'word_post.assets', 'word_post.licenses', 'static',
    'ui_preferences.appearance',
    'vocab.vocab_list', 'vocab.inventory', 'learning.state', 'learning.asset',
    'live_conversation.scenarios', 'live_conversation.options', 'user_sessions.read',
    'onboarding.read', 'onboarding.practice_read', 'first_steps.chapter', 'first_steps.lesson',
    'progression.read', 'progression.world', 'native_review.overview', 'native_review.read',
    'native_review.history', 'journey_games.catalogue', 'journey_games.read',
})
WRITE_ENDPOINTS = frozenset({
    'onboarding.introduce', 'onboarding.practice_write', 'first_steps.command',
    'progression.preferences', 'progression.answer', 'native_review.start',
    'native_review.command', 'native_review.suspension', 'set_ui_language',
    'ui_preferences.set_navigation',
    'journey_games.start', 'journey_games.command', 'journey_games.route_command',
})


def prepare_demo():
    # Always create a NEW sandbox. Never reset a configured or personal DB.
    root = Path(tempfile.mkdtemp(prefix='russian-arcade-demo-'))
    paths = {'VOCAB_DB_PATH': 'vocab.db', 'VOCAB_SESSION_DIR': 'sessions',
             'VOCAB_UPLOAD_DIR': 'uploads', 'APP_MEDIA_DIR': 'media',
             'WORD_POST_ASSET_DIR': 'assets', 'ANKI_MEDIA_DIR': 'anki-media'}
    for name, relative in paths.items():
        os.environ[name] = str(root / relative)
    from migrations import upgrade_database
    from services.sample_vocabulary import seed_sample_items
    from services.learning_assets import LocalAssetStore
    from services.learning_content import ContentService
    db = os.environ['VOCAB_DB_PATH']
    upgrade_database(db, backup=False)
    with transaction(db, write=True) as conn:
        items = seed_sample_items(conn, 'demo')
    credential = personal_access(db)
    content = ContentService(db, LocalAssetStore(os.environ['WORD_POST_ASSET_DIR']))
    version = content.import_draft(dict(schema_version=2, id='public-demo', kind='deck',
        title='First Russian words · sample cards', source='Authored First steps content; synthetic public demo, no personal records.', items=items))
    content.publish(credential, version, 'Russian Arcade demo')
    with transaction(db, write=True) as conn:
        conn.execute("UPDATE learning_profiles SET archived=1 WHERE id='personal-learning'")
        conn.execute('DELETE FROM household_access')
    return root


def install_demo(app):
    database = app.config['DB_PATH']
    sessions = PersonalSessions(database)
    limits = DemoLimits(database)

    def rate_limited(seconds):
        return jsonify(error={'code': 'rate_limited', 'message': 'The demo is busy. Please try again later.'}), 429, {'Retry-After': str(seconds)}

    def limited():
        available = app.config.get('HOSTED_TRIAL_AVAILABLE')
        message = 'Sign in with GitHub to use the AI activities and save your progress.' if available else MESSAGE
        if request.path.startswith('/api/'):
            return jsonify(error={'code': 'demo_limit', 'message': message,
                                  'sign_in_url': '/trial/sign-in' if available else None}), 403
        sign_in = '<p><a href="/trial/sign-in">Sign in with GitHub</a></p>' if available else ''
        return (f'<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width"><title>Russian Arcade preview</title>'
                '<link rel="stylesheet" href="/static/css/public_demo.css?v=2"></head><body class="demo-unavailable">'
                f'<main class="demo-unavailable-content">'
                f'<h1>Explore the public preview</h1><p>{message}</p>{sign_in}'
                '<p><a href="/post/#first-delivery">Try First steps</a> · <a href="/post/#flashcards">Try flashcards</a> · '
                '<a href="/post/#home">Home</a></p></main></body></html>'), 403

    def boundary():
        if request.endpoint is None:
            return None
        if request.endpoint == 'journey_games.purchase':
            return jsonify(error={'code': 'demo_unavailable', 'message': 'Game purchases are unavailable in the public demo.'}), 403
        if request.path == '/':
            return redirect('/post/')
        if request.path == '/post/profiles' and request.method == 'GET':
            return redirect('/post/#home')
        read = request.method in ('GET', 'HEAD')
        allowed = ((read and request.endpoint in READ_ENDPOINTS)
                   or (request.method == 'POST' and request.endpoint in WRITE_ENDPOINTS))
        if request.endpoint == 'journey_games.start':
            from services.demo_games import SAMPLE_GAMES
            allowed = allowed and request.view_args.get('game_id') in SAMPLE_GAMES
        if request.endpoint == 'journey_games.command':
            allowed = allowed and request.view_args.get('operation') in {'hint', 'answer', 'continue', 'complete', 'retry', 'review', 'practice_answer', 'practice_continue', 'practice_exit', 'practice_hint'}
        if not allowed:
            return limited()
        if request.blueprint == 'vocab' and request.args.get('source', 'db') != 'db':
            return limited()
        if request.endpoint == 'static' or request.endpoint in {'word_post.assets', 'word_post.licenses'}:
            return None
        # Global limits cannot be bypassed by resetting a cookie. No IPs stored.
        admission = [('requests', 60, 1200)]
        if not read:
            visitor = hashlib.sha256(str(session.get('personal_access_id', 'new')).encode()).hexdigest()
            admission += [('writes', 60, 600), ('writes', 86400, 10000),
                          ('visitor:' + visitor, 60, 60), ('visitor:' + visitor, 86400, 300)]
        retry = limits.consume(admission)
        if retry:
            return rate_limited(retry)
        state = sessions.state(session.get('personal_access_id'))
        if not state['profile']:
            retry = limits.consume([('new-visitors', 60, 30), ('new-visitors', 3600, 120)])
            if retry:
                return rate_limited(retry)
            session['personal_access_id'] = sessions.create('Demo visitor', max_profiles=2000)
            session.permanent = True

    # Run before local profile selection and provider-backed route handlers.
    app.before_request_funcs.setdefault(None, []).insert(0, boundary)

    def visitor_state():
        state = sessions.state(session.get('personal_access_id'))
        state['profiles'] = [state['profile']] if state['profile'] else []
        return jsonify(state | {'csrf_token': csrf_token(), 'public_demo': True,
                               'configured': True, 'adult': False})

    app.view_functions['user_sessions.read'] = visitor_state
    app.view_functions['learning.state'] = visitor_state
    visitor_state.household_policy = 'public'

    @app.after_request
    def banner(response):
        if response.mimetype == 'text/html' and not response.direct_passthrough:
            body = response.get_data(as_text=True)
            notice = ('<details class="demo-notice"><summary>Public demo</summary>'
                      '<p>Try First steps, sample games and flashcards. Sample progress is temporary.</p>'
                      + ('<p><a href="/trial/sign-in">Sign in with GitHub</a> to use AI activities '
                         'and save your progress. The demo shares a US$1 daily and US$20 monthly AI allowance.</p>'
                         if app.config.get('HOSTED_TRIAL_AVAILABLE') else
                         '<p>AI activities are not enabled in this public demo yet. You can use them in a local installation.</p>')
                      + '</details>')
            if '<body>' in body:
                body = body.replace('</head>', '<link rel="stylesheet" href="/static/css/public_demo.css?v=2"></head>', 1)
                response.set_data(body.replace('</body>', notice + '</body>', 1))
        return response
