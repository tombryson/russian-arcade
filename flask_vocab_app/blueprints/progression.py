"""Shared level preference, participation wallet and permanent story stops."""
from flask import Blueprint, jsonify, request
from contracts.learning import fields
from repositories.learning_repository import LearningError, require_access, timestamp, transaction
from services.progression import LEVELS, snapshot, journey_read, journey_answer
from utils.household_access import access_id, access_policy, csrf_token


def create_progression_blueprint(db_path):
    bp = Blueprint('progression', __name__, url_prefix='/api/v1')

    def body(required):
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise LearningError('invalid_input','Send a JSON object.')
        fields(data, required)
        return data

    @bp.get('/progression')
    @access_policy('child')
    def read():
        with transaction(db_path) as conn:
            profile = require_access(conn,access_id(),timestamp())
            return jsonify(snapshot(conn,profile['id']) | {'csrf_token':csrf_token()})

    @bp.post('/progression/preferences')
    @access_policy('child')
    def preferences():
        data = body({'level'})
        if data['level'] not in [level['id'] for level in LEVELS]:
            raise LearningError('invalid_level','Choose A1, A2, B1 or B2.')
        with transaction(db_path,write=True) as conn:
            profile = require_access(conn,access_id(),timestamp())
            conn.execute('INSERT INTO progression_preferences(profile_id,preferred_level) VALUES (?,?) ON CONFLICT(profile_id) DO UPDATE SET preferred_level=excluded.preferred_level',(profile['id'],data['level']))
            return jsonify(snapshot(conn,profile['id']))

    @bp.get('/journey/<world_id>')
    @access_policy('child')
    def world(world_id):
        with transaction(db_path) as conn:
            profile = require_access(conn,access_id(),timestamp())
            return jsonify(journey_read(conn,profile['id'],world_id))

    @bp.post('/journey/<world_id>/answer')
    @access_policy('child')
    def answer(world_id):
        data = body({'answer','submission_id'})
        with transaction(db_path,write=True) as conn:
            profile = require_access(conn,access_id(),timestamp())
            return jsonify(journey_answer(conn,profile['id'],world_id,data['answer'],data['submission_id']))

    return bp
