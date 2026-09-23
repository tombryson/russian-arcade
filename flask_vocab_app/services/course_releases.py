"""Published course identities, separate from schema and marking versions.

The complete shipped A1 catalogue stays at its original path, with its bytes
and media unchanged. Draft authoring files are deliberately not enrolable.
Adding a release here requires its entire course and media to be ready.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from repositories.learning_repository import LearningError

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
DEFAULT_RELEASE_ID = 'a1-v1'
RELEASES = {
    'a1-v1': {
        'release_id': 'a1-v1', 'band': 'A1', 'status': 'published',
        'schema_version': 1, 'chapter_count': 4,
        'requirement_version': 'a1-checkpoint-v1', 'continuation_level': 'A2',
        'catalogue_file': 'course_chapters.json',
        'catalogue_sha256': '2e0201b820a8a512fdac04b1d6f507ecbfd3764ac34480e97380640ff53469df',
    },
}


def release_metadata(release_id=DEFAULT_RELEASE_ID):
    """Resolve only complete published courses, including retained editions."""
    if not isinstance(release_id, str) or not release_id:
        raise LearningError('invalid_input', 'Choose a valid course release.')
    release = RELEASES.get(release_id)
    if release is None or release.get('status') != 'published':
        raise LearningError('course_release_unavailable', 'That course release is not available.', 404)
    return deepcopy(release)


def load_release(release_id=DEFAULT_RELEASE_ID):
    release = release_metadata(release_id)
    content = (DATA_DIR / release['catalogue_file']).read_bytes()
    if sha256(content).hexdigest() != release['catalogue_sha256']:
        raise ValueError('Published course content changed; publish a new release instead.')
    return json.loads(content)
