"""A saved writing task, a durable draft and feedback for each checked version."""
import logging
import sqlite3

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from repositories.word_repository import WordRepository
from repositories.writing_repository import WritingRepository, WritingConflict, word_count
from services.writing_service import WritingUnavailable
from utils.activity_display import topic_label, readable_date
from utils.i18n import translate_ui
from utils.shell import render_page

logger = logging.getLogger(__name__)


def create_writing_blueprint(db_path, service):
    blueprint = Blueprint('writing',__name__)
    repository = WritingRepository(db_path)

    def language():
        return 'ru' if session.get('ui_lang') == 'ru' else 'en'

    def t(key):
        return translate_ui('writing.'+key,language())

    def present(item):
        if item is None:
            return None
        item = dict(item)
        item['topic_label'] = topic_label(item['topic'],language())
        item['display_title'] = item.get('title' if language() == 'ru' else 'title_en') or item['topic_label']+' · '+t('title')
        item['display_task'] = item.get('task_en') if language() == 'en' and item.get('task_en') else item['task']
        item['task_language'] = 'en' if language() == 'en' and item.get('task_en') else 'ru'
        item['level_label'] = t('level_'+item['difficulty'])
        item['display_date'] = readable_date(item.get('draft_saved_at') or item.get('created_at'),language())
        item['saved_draft'] = item.get('saved_draft',item['draft'])
        item['word_count'] = word_count(item['draft'])
        item['state'] = 'draft' if item['draft'] != (item.get('checked_response') or '') else 'checked' if item.get('checked_response') is not None else 'ready'
        return item

    def page(exercise=None,**extra):
        saved = [present(item) for item in repository.list_saved()]
        topics = set(WordRepository(db_path).list_topics()) | {item['topic'] for item in saved}
        topics = sorted([{'value':topic,'label':topic_label(topic,language())} for topic in topics if topic != 'any'],key=lambda item:item['label'])
        context = dict(exercise=present(exercise),saved_exercises=saved,topics=topics,active_page='writing',**extra)
        if request.headers.get('HX-Target') == 'writing-content':
            return render_template('_writing_content.html',**context)
        return render_page('writing.html',**context)

    def enhanced():
        return request.accept_mimetypes.best == 'application/json'

    def failure(error,exercise=None,preparing=False):
        if isinstance(error,LookupError):
            key,status = 'missing',404
        elif isinstance(error,WritingConflict):
            key,status = 'conflict',409
        elif isinstance(error,WritingUnavailable):
            key,status = ('prepare_failed' if preparing else 'check_failed'),503
        elif isinstance(error,sqlite3.Error):
            key,status = 'request_failed',503
        else:
            key,status = 'invalid',400
        if status == 503:
            logger.warning('Writing request unavailable (%s)',type(error).__name__)
        if enhanced():
            return jsonify(error=t(key)),status
        return page(exercise,error=t(key),selected_topic=request.form.get('topic','any'),
                    selected_level=request.form.get('difficulty','beginner'),selected_length=request.form.get('target_words','30')),status

    @blueprint.get('/writing')
    def home():
        return page()

    @blueprint.get('/writing/load/<int:exercise_id>')
    def load(exercise_id):
        exercise = repository.load(exercise_id)
        return page(exercise) if exercise else failure(LookupError())

    @blueprint.post('/writing/generate')
    def generate():
        try:
            topic = request.form.get('topic','any')
            difficulty = request.form.get('difficulty','beginner')
            target = request.form.get('target_words',type=int) if 'target_words' in request.form else 30
            if not topic.strip() or len(topic)>100 or difficulty not in ('beginner','intermediate','advanced') or target not in (30,100):
                raise ValueError('Invalid setup')
            task = service.generate_writing_task(topic,difficulty,target)
            exercise_id = repository.create(task,topic,difficulty,target)
        except (ValueError,WritingUnavailable,sqlite3.Error) as error:
            return failure(error,preparing=True)
        url = url_for('writing.load',exercise_id=exercise_id)
        return jsonify(url=url) if enhanced() else redirect(url,code=303)

    def submit(checking):
        exercise_id = request.form.get('exercise_id',type=int)
        revision = request.form.get('revision',type=int)
        response = request.form.get('user_response','')
        exercise = repository.load(exercise_id)
        try:
            if not exercise:
                raise LookupError('Writing not found')
            repository.validate_answer(response,checking=checking)
            repository.check_revision(exercise_id,revision)
            assessment = service.assess_writing(task=exercise['task'],required_words=exercise['required_words'],
                min_words=exercise['min_words'],response=response,difficulty=exercise['difficulty'],language=language()) if checking else None
            revision = repository.save(exercise_id,response,revision,assessment,language())
        except (ValueError,LookupError,WritingUnavailable,sqlite3.Error) as error:
            if exercise:
                exercise = {**exercise,'saved_draft':exercise['draft'],'draft':response,'revision':revision if type(revision) is int else -1}
            return failure(error,exercise)
        if enhanced():
            current = present(repository.load(exercise_id))
            return jsonify(revision=revision,message=t('checked_ok' if checking else 'saved_ok'),state=t(current['state']),
                display_date=current['display_date'],feedback=render_template('_writing_feedback.html',exercise=current))
        return redirect(url_for('writing.load',exercise_id=exercise_id),code=303)

    @blueprint.post('/writing/save')
    def save():
        return submit(False)

    @blueprint.post('/writing/assess')
    def assess():
        return submit(True)

    return blueprint
