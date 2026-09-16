"""Translation practice and its reference library, with resumable server-owned content."""
import logging
import sqlite3

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from repositories import WordRepository
from repositories.translation_repository import TranslationRepository, TranslationConflict
from services.sentence_service import TranslationUnavailable
from utils.activity_display import topic_label, readable_date
from utils.i18n import translate_ui
from utils.shell import render_page

logger = logging.getLogger(__name__)


def create_sentences_blueprint(db_path, sentence_service, user_service):
    blueprint = Blueprint('sentences', __name__)
    repository = TranslationRepository(db_path)
    words = WordRepository(db_path)

    def language():
        return 'ru' if session.get('ui_lang') == 'ru' else 'en'

    def t(key):
        return translate_ui('translation.' + key, language())

    def present(item):
        if not item:
            return None
        item = dict(item)
        item['topic_label'] = topic_label(item.get('topic'), language())
        item['level_label'] = t('level_' + str(item['difficulty']))
        item['display_date'] = readable_date(item.get('draft_saved_at') or item.get('created_at'), language())
        item.setdefault('draft', '')
        item.setdefault('saved_draft', item['draft'])
        item['state'] = ('draft' if item.get('draft_saved_at') and item['draft'] != item.get('checked_response')
                         else 'checked' if item.get('checked_response') is not None else 'ready')
        return item

    def context():
        library = [present(item) for item in repository.list_saved()]
        topics = set(words.list_topics()) | {item['topic'] for item in library if item.get('topic')}
        return {'sentences': library, 'topics': sorted(
            [{'value': topic, 'label': topic_label(topic, language())} for topic in topics if topic != 'any'],
            key=lambda item: item['label'].casefold()), 'active_page': 'sentences'}

    def page(practice=None, **extra):
        return render_page('sentences.html', practice=present(practice), **context(), **extra)

    def enhanced():
        return request.accept_mimetypes.best == 'application/json'

    def failure(error, practice=None, preparing=False):
        if isinstance(error, LookupError):
            key, status = 'missing', 404
        elif isinstance(error, TranslationConflict):
            key, status = 'conflict', 409
        elif isinstance(error, TranslationUnavailable):
            key, status = ('prepare_failed' if preparing else 'check_failed'), 503
        elif isinstance(error, sqlite3.Error):
            key, status = 'request_failed', 503
        else:
            key, status = 'invalid', 400
        if status == 503:
            logger.warning('Translation request unavailable (%s)', type(error).__name__)
        if enhanced():
            return jsonify(error=t(key)), status
        return page(practice, error=t(key), selected_topic=request.form.get('topic', 'any'),
                    selected_level=request.form.get('difficulty', '1')), status

    @blueprint.get('/sentences')
    def sentences_page():
        return page()

    @blueprint.get('/sentences/practice/<int:sentence_id>')
    def practice(sentence_id):
        item = repository.load(sentence_id)
        return page(item) if item else (page(error=t('missing')), 404)

    @blueprint.route('/sentence/generate', methods=['GET', 'POST'])
    def generate_sentence():
        # Keep old bookmarks/client URLs, but generate only on an explicit POST.
        if request.method == 'GET':
            if 'difficulty' in request.args and request.args.get('difficulty', type=int) not in range(1, 6):
                return jsonify(error=t('invalid')), 400
            return redirect('/sentences', code=303)
        try:
            difficulty = request.form.get('difficulty', type=int)
            topic = request.form.get('topic', 'any')
            if difficulty not in range(1, 6) or not topic or len(topic) > 100:
                raise ValueError('Invalid setup')
            pair = sentence_service.get_sentence(topic, difficulty)
            sentence_id, _ = repository.save_content(pair['sentence'], pair['english'], topic, difficulty)
        except (ValueError, LookupError, TranslationUnavailable, sqlite3.Error) as error:
            return failure(error, preparing=True)
        target = url_for('sentences.practice', sentence_id=sentence_id)
        return jsonify(url=target) if enhanced() else redirect(target, code=303)

    def submit(checking):
        sentence_id = request.form.get('sentence_id', type=int)
        response = request.form.get('user_response', '')
        revision = request.form.get('revision', type=int)
        item = repository.load(sentence_id)
        try:
            if not item:
                raise LookupError('Sentence not found')
            repository.validate_answer(response, checking=checking)
            repository.check_revision(sentence_id, revision)
            if checking:
                # No score, difficulty, prompt or reference answer is accepted from the browser.
                assessment = sentence_service.assess_translation(item['sentence'], item['english'], response, language())
                revision = repository.save_check(sentence_id, response, revision, assessment, language())
            else:
                revision = repository.save_draft(sentence_id, response, revision)
        except (ValueError, LookupError, TranslationUnavailable, sqlite3.Error) as error:
            if item:
                item = {**item, 'saved_draft': item['draft'], 'draft': response, 'revision': revision or 0}
            return failure(error, item)
        if enhanced():
            current = present(repository.load(sentence_id))
            return jsonify(revision=revision, message=t('checked_ok' if checking else 'saved_ok'),
                           state=t(current['state']), display_date=current['display_date'],
                           feedback=render_template('_translation_feedback.html', practice=current))
        return redirect(url_for('sentences.practice', sentence_id=sentence_id), code=303)

    @blueprint.post('/sentence/assess')
    def assess_sentence():
        return submit(checking=True)

    @blueprint.post('/sentence/save')
    def save_sentence():
        return submit(checking=False)

    @blueprint.post('/sentence/audio/<int:sentence_id>')
    def sentence_audio(sentence_id):
        item = repository.load(sentence_id)
        if not item:
            return jsonify(error=t('missing')), 404
        # Audio reveals the reference; keep it with feedback, after the first check.
        if not item['attempts']:
            return jsonify(error=t('check_first')), 400
        try:
            url = item['audio_url'] or sentence_service.generate_audio(item['sentence'])
            if not url:
                raise TranslationUnavailable('No audio')
            repository.save_audio(sentence_id, url)
        except (ValueError, TranslationUnavailable, sqlite3.Error):
            return jsonify(error=t('audio_failed')), 503
        return jsonify(html=render_template('_translation_audio.html', audio_url=url))

    @blueprint.post('/sentence/add')
    def add_sentence():
        try:
            russian = request.form.get('sentence', '')
            english = request.form.get('english', '')
            topic = request.form.get('topic') or 'general'
            difficulty = request.form.get('difficulty', type=int)
            repository.validate_answer(russian, checking=True)
            if difficulty not in range(1, 6):
                raise ValueError('Invalid level')
            if not english.strip():
                english = sentence_service.translate_for_library(russian)
            sentence_id, created = repository.save_content(russian, english, topic, difficulty)
        except (ValueError, TranslationUnavailable, sqlite3.Error) as error:
            if enhanced():
                return failure(error, preparing=True)
            return render_page('saved_sentences.html', **context(), error=t('add_failed'),
                               added_russian=request.form.get('sentence', ''), added_english=request.form.get('english', ''), add_open=True), 400
        target = url_for('sentences.sentences_saved_detail', sentence_id=sentence_id)
        return jsonify(url=target) if enhanced() else redirect(target, code=303)

    @blueprint.get('/sentences/saved/<int:sentence_id>')
    def sentences_saved_detail(sentence_id):
        item = repository.load(sentence_id)
        if not item:
            return page(error=t('missing')), 404
        return render_page('sentence_detail.html', sentence=present(item), active_page='sentences')

    @blueprint.get('/sentences/saved')
    def sentences_saved():
        library = context()
        if request.args.get('fetch_all') == 'true' and enhanced():
            return jsonify(sentences=library['sentences'], topics=[topic['value'] for topic in library['topics']], error=None)
        selected = request.args.get('topic', '')
        if selected:
            library['sentences'] = [item for item in library['sentences'] if item['topic'] == selected]
        return render_page('saved_sentences.html', **library, selected_topic=selected)

    return blueprint
