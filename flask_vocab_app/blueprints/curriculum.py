"""Read-only course catalogue. Activity links prefill existing generators."""
from flask import Blueprint, session

from services.curriculum import band_summaries
from services.course_progression import course_catalogue
from services.speaking_curriculum import scenario_for_topic
from utils.course_context import selected_course_progress
from utils.household_access import access_policy
from utils.shell import render_page


def create_curriculum_blueprint():
    blueprint = Blueprint('curriculum', __name__)

    @blueprint.get('/curriculum')
    @access_policy('public')
    def index():
        language = 'ru' if session.get('ui_lang') == 'ru' else 'en'
        progress = selected_course_progress()
        bands = band_summaries(language)
        chapters = progress['chapters'] if progress else course_catalogue()['chapters']
        topics = {topic['id']: topic for band in bands for topic in band['topics']}
        milestones = []
        for chapter in chapters:
            status = chapter.get('status', 'practice' if chapter['number'] == 1 else 'locked')
            if status == 'locked':
                milestones.append({'id': chapter['id'], 'number': chapter['number'], 'status': 'locked'})
                continue
            topic_ids = ([topic['id'] for topic in chapter['topics']]
                         if progress else chapter['topic_ids'])
            milestones.append({**chapter, 'status': status, 'curriculum_topics': [topics[topic_id] for topic_id in topic_ids]})
        return render_page('curriculum.html', active_page='curriculum',
                           bands=bands, language=language, milestones=milestones,
                           course_progress=progress,
                           speaking_scenario=scenario_for_topic)

    return blueprint
