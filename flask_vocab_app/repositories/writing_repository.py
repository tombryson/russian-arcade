"""Writing content, exact drafts and append-only checks for local practice."""
import json
import re
import sqlite3
from datetime import datetime, timezone

from models.database import connect_db
from services.progression import award, legacy_profile
from utils.activity_owner import activity_profile_id


class WritingConflict(ValueError):
    pass


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def word_count(text):
    return len(re.findall(r"[^\W_]+(?:[-’'][^\W_]+)*", text, re.UNICODE))


class WritingRepository:
    def __init__(self, db_path):
        self.db_path = db_path

    @staticmethod
    def decode(row):
        item = dict(row)
        try:
            words = json.loads(item['required_words'])
            # Historical imports sometimes escaped Unicode inside JSON strings.
            item['required_words'] = [re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m[1],16)), word)
                for word in words if isinstance(word,str)] if isinstance(words,list) else []
        except (ValueError, TypeError):
            item['required_words'] = []
        return item

    def list_saved(self):
        with connect_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [self.decode(row) for row in conn.execute('''SELECT e.*, m.title,m.title_en,m.task_en,
                COALESCE(d.response,e.user_response,'') AS draft, COALESCE(d.revision,0) AS revision,d.updated_at AS draft_saved_at,
                (SELECT response FROM writing_attempts a WHERE a.exercise_id=e.id ORDER BY a.id DESC LIMIT 1) AS checked_response
                FROM writing_exercises e LEFT JOIN writing_details m ON m.exercise_id=e.id
                LEFT JOIN writing_drafts d ON d.exercise_id=e.id
                WHERE COALESCE(e.owner_profile_id,'personal-learning')=?
                ORDER BY COALESCE(d.updated_at,e.created_at) DESC,e.id DESC''', (activity_profile_id(conn),))]

    def load(self, exercise_id):
        item = next((item for item in self.list_saved() if item['id'] == exercise_id), None)
        if item is None:
            return None
        with connect_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            item['attempts'] = [dict(row) for row in conn.execute(
                'SELECT * FROM writing_attempts WHERE exercise_id=? ORDER BY id DESC', (exercise_id,))]
        return item

    @staticmethod
    def validate_answer(response, checking=False):
        if not isinstance(response,str) or len(response) > 20000 or (checking and not response.strip()):
            raise ValueError('Invalid writing')

    @staticmethod
    def validate_task(task):
        if not isinstance(task,dict):
            raise ValueError('Invalid task')
        for key, limit in [('title',100),('title_en',100),('task',3000),('task_en',3000)]:
            if not isinstance(task.get(key),str) or not task[key].strip() or len(task[key]) > limit:
                raise ValueError('Invalid task text')
        words = task.get('required_words')
        if not isinstance(words,list) or not 3 <= len(words) <= 5 or any(
                not isinstance(word,str) or not word.strip() or len(word) > 80 for word in words):
            raise ValueError('Invalid task words')

    def create(self, task, topic, difficulty, target_words):
        self.validate_task(task)
        if difficulty not in ('beginner','intermediate','advanced') or target_words not in (30,100):
            raise ValueError('Invalid setup')
        if not isinstance(topic,str) or not topic.strip() or len(topic) > 100:
            raise ValueError('Invalid topic')
        with connect_db(self.db_path) as conn:
            conn.execute('BEGIN IMMEDIATE')
            cursor = conn.execute('''INSERT INTO writing_exercises
                (topic,difficulty,task,required_words,min_words,user_response,created_at,owner_profile_id) VALUES (?,?,?,?,?,'',?,?)''',
                (topic,difficulty,task['task'],json.dumps(task['required_words'],ensure_ascii=False),target_words,timestamp(),activity_profile_id(conn)))
            exercise_id = cursor.lastrowid
            conn.execute('INSERT INTO writing_details(exercise_id,title,title_en,task_en) VALUES (?,?,?,?)',
                         (exercise_id,task['title'],task['title_en'],task['task_en']))
        return exercise_id

    @staticmethod
    def assert_revision(conn, exercise_id, revision):
        if not conn.execute("SELECT 1 FROM writing_exercises WHERE id=? AND COALESCE(owner_profile_id,'personal-learning')=?",(exercise_id,activity_profile_id(conn))).fetchone():
            raise LookupError('Writing not found')
        row = conn.execute('SELECT revision FROM writing_drafts WHERE exercise_id=?',(exercise_id,)).fetchone()
        if type(revision) is not int or revision != (row[0] if row else 0):
            raise WritingConflict('Newer draft exists')

    def check_revision(self, exercise_id, revision):
        with connect_db(self.db_path) as conn:
            self.assert_revision(conn,exercise_id,revision)

    @staticmethod
    def validate_assessment(assessment):
        if not isinstance(assessment,dict) or type(assessment.get('score')) is not int or not 0 <= assessment['score'] <= 10:
            raise ValueError('Invalid score')
        for key in ('strength','next_step','example'):
            if not isinstance(assessment.get(key),str) or not assessment[key].strip() or len(assessment[key]) > 1500:
                raise ValueError('Invalid advice')

    def save(self, exercise_id, response, revision, assessment=None, language='en'):
        self.validate_answer(response, checking=assessment is not None)
        if assessment is not None:
            self.validate_assessment(assessment)
        with connect_db(self.db_path) as conn:
            conn.execute('BEGIN IMMEDIATE')
            self.assert_revision(conn,exercise_id,revision)
            conn.execute('''INSERT INTO writing_drafts(exercise_id,response,revision,updated_at) VALUES (?,?,?,?)
                ON CONFLICT(exercise_id) DO UPDATE SET response=excluded.response,
                revision=excluded.revision,updated_at=excluded.updated_at''',(exercise_id,response,revision+1,timestamp()))
            if assessment is not None:
                attempt = conn.execute('''INSERT INTO writing_attempts
                    (exercise_id,response,score,score_max,strength,next_step,example,ui_language,created_at,source)
                    VALUES (?,?,?,10,?,?,?,?,?,'writing-v1')''',
                    (exercise_id,response,assessment['score'],assessment['strength'],assessment['next_step'],assessment['example'],language,timestamp()))
                profile_id = legacy_profile(conn)
                if profile_id:
                    award(conn, profile_id, activity='writing', content_key=f'writing:{exercise_id}',
                          source_key=f'writing-attempt:{attempt.lastrowid}', title='Writing',
                          evidence={'score': assessment['score'], 'score_max': 10})
        return revision+1
