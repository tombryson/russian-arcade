"""Read-only course catalogue. Activity links prefill existing generators."""
from flask import Blueprint, abort, current_app, redirect, request, session

from services.curriculum import band_summaries
from services.speaking_curriculum import scenario_for_topic
from services.torfl_requirements import requirement_groups
from services.curriculum_units import get_unit, unit_summaries, start_practice, start_writing
from repositories.learning_repository import LearningError, identifier, require_access, timestamp, transaction
from utils.household_access import access_policy, access_id
from utils.shell import render_page


def create_curriculum_blueprint():
    blueprint = Blueprint('curriculum', __name__)

    @blueprint.get('/curriculum')
    @access_policy('public')
    def index():
        language = 'ru' if session.get('ui_lang') == 'ru' else 'en'
        return render_page('curriculum.html', active_page='curriculum',
                           bands=band_summaries(language), language=language,
                           speaking_scenario=scenario_for_topic,
                           requirement_groups=requirement_groups, units=unit_summaries())

    def unit_or_404(unit_id):
        try:
            return get_unit(unit_id)
        except LookupError:
            abort(404)

    @blueprint.get('/curriculum/units/<unit_id>')
    @access_policy('public')
    def unit_page(unit_id):
        unit = unit_or_404(unit_id)
        language = 'ru' if session.get('ui_lang') == 'ru' else 'en'
        profile_id = None
        if access_id():
            with transaction(current_app.config['DB_PATH']) as conn:
                try:
                    profile_id = require_access(conn, access_id(), timestamp())['id']
                except LearningError:
                    pass
        return render_page('curriculum_unit.html', active_page='curriculum', unit=unit,
                           language=language, profile_id=profile_id, request_id=identifier(), forms_request_id=identifier(),
                           unit_writing_available=not current_app.config.get('PUBLIC_DEMO'))

    @blueprint.post('/curriculum/units/<unit_id>/<activity>')
    @access_policy('child')
    def unit_start(unit_id, activity):
        unit_or_404(unit_id)
        if activity not in ('practice', 'forms', 'writing'):
            abort(404)
        if activity == 'writing' and current_app.config['WORD_POST_HOUSEHOLD_ENABLED']:
            # The legacy Writing workspace belongs to the household adult.
            # Do not create an unreachable child-owned exercise in that store.
            raise LearningError('activity_unavailable', 'This writing workspace is not available for the selected learner.', 403)
        db_path = current_app.config['DB_PATH']
        with transaction(db_path) as conn:
            profile = require_access(conn, access_id(), timestamp())
            if request.form.get('profile_id') != profile['id']:
                raise LearningError('profile_changed', 'Your profile changed. Reopen this lesson before continuing.', 409)
        if activity == 'writing':
            return redirect('/writing/load/' + str(start_writing(db_path, access_id(), unit_id,
                            expected_profile_id=profile['id'])), code=303)
        saved = start_practice(db_path, access_id(), unit_id, request.form.get('request_id'),
                               expected_profile_id=profile['id'], stage=activity)
        return redirect('/#practice/' + saved['id'], code=303)

    return blueprint
