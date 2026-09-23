"""Read-only course catalogue. Activity links prefill existing generators."""
from flask import Blueprint, session

from services.curriculum import band_summaries
from services.speaking_curriculum import scenario_for_topic
from services.torfl_requirements import requirement_groups
from utils.household_access import access_policy
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
                           requirement_groups=requirement_groups)

    return blueprint
