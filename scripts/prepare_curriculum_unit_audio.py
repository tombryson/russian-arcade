"""Prepare the three authored location/destination listening clips once.

This maintenance command uses the existing speech provider and configured random
voices. It never runs during a learner request. Published recordings are checked
against their manifest and cannot be silently regenerated or replaced.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
UNIT_ID = 'location-destination-listening-v1'
MAX_NEW = 3
MAX_CHARACTERS = 750


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _atomic_write(path, data):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(data)
            handle.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def _manifest_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def plan_recordings(source, directory, probe):
    """Validate all published assets before returning any new paid work."""
    if source.get('id') != UNIT_ID or source.get('version') != 'listening-v1':
        raise ValueError('Unsupported listening content version.')
    items = source.get('items')
    if not isinstance(items, list) or len(items) != MAX_NEW:
        raise ValueError('This command prepares exactly three authored clips.')
    directory = Path(directory)
    manifest_path = directory / 'manifest.json'
    if directory.is_symlink() or manifest_path.is_symlink():
        raise ValueError('Recording paths must not be symbolic links.')
    saved = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        'version': 'curriculum-unit-audio-v1',
        'content_id': UNIT_ID,
        'provider': 'elevenlabs',
        'source': 'App-authored learning material with synthetic narration.',
        'clips': {},
    }
    if (saved.get('version') != 'curriculum-unit-audio-v1'
            or saved.get('content_id') != UNIT_ID
            or saved.get('provider') != 'elevenlabs'
            or not isinstance(saved.get('clips'), dict)):
        raise ValueError('Unsupported recording manifest.')
    identifiers = set()
    todo = []
    for item in items:
        identifier = item.get('id')
        text = item.get('transcript')
        if (not isinstance(identifier, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,79}', identifier)
                or identifier in identifiers or not isinstance(text, str) or not text.strip()):
            raise ValueError('Each authored clip needs a unique safe ID and transcript.')
        identifiers.add(identifier)
        expected_url = f'/static/audio/course/curriculum/{UNIT_ID}/{identifier}.mp3'
        if item.get('audio_url') != expected_url:
            raise ValueError('Recording URL does not match its authored ID.')
        digest = _sha256(text.encode())
        path = directory / (identifier + '.mp3')
        previous = saved['clips'].get(identifier)
        if path.is_symlink():
            raise ValueError('Recording paths must not be symbolic links.')
        if previous is None:
            if path.exists():
                raise ValueError(f'{identifier} has an untracked recording. Restore its manifest before continuing.')
            todo.append((item, digest))
            continue
        if not isinstance(previous, dict) or previous.get('text_sha256') != digest:
            raise ValueError(f'{identifier} has published speech. Use a new content version for changed text.')
        if not path.is_file():
            raise ValueError(f'{identifier} is missing its published recording. Restore it from source control.')
        if previous.get('audio_sha256') != _sha256(path.read_bytes()):
            raise ValueError(f'{identifier} differs from its published recording manifest.')
        duration = previous.get('duration')
        if (not isinstance(duration, (int, float)) or isinstance(duration, bool)
                or not math.isfinite(duration) or not 0.2 <= duration <= 90
                or not previous.get('voice_id') or not previous.get('model')
                or abs(probe(path) - duration) > 0.01):
            raise ValueError(f'{identifier} has invalid recording metadata.')
    if set(saved['clips']) - identifiers:
        raise ValueError('Manifest contains clips absent from the authored content.')
    if sum(len(item['transcript']) for item in items) > MAX_CHARACTERS:
        raise ValueError('Authored speech exceeds the 750-character limit.')
    return saved, todo


def prepare_recordings(source, directory, config, provider_factory, probe, *, dry_run=False, max_new=MAX_NEW):
    if isinstance(max_new, bool) or not isinstance(max_new, int) or not 0 <= max_new <= MAX_NEW:
        raise ValueError('Recording limit must be between zero and three.')
    directory = Path(directory)
    saved, todo = plan_recordings(source, directory, probe)
    print(f'{len(todo)} new recordings; {sum(len(item["transcript"]) for item, _ in todo)} Russian characters.', flush=True)
    if dry_run or not todo:
        return
    if len(todo) > max_new:
        raise ValueError('Recording limit exceeded; no provider calls made.')
    voices = config.get('ELEVENLABS_VOICE_IDS') or ()
    if not voices or not config.get('ELEVENLABS_API_KEY') or not config.get('ELEVENLABS_MODEL'):
        raise ValueError('Configured ElevenLabs credentials, model and voices are required.')
    provider = provider_factory(config)
    directory.mkdir(parents=True, exist_ok=True)
    for item, digest in todo:
        identifier = item['id']
        voice = random.choice(voices)
        try:
            # No retries: a failure stops before spending on another clip.
            audio = provider.speak(item['transcript'], voice)
            with tempfile.TemporaryDirectory(dir=directory) as temporary:
                staged = Path(temporary) / 'clip.mp3'
                staged.write_bytes(audio)
                duration = probe(staged)
            if not math.isfinite(duration) or not 0.2 <= duration <= 90:
                raise ValueError('Invalid recording duration.')
        except Exception as error:
            raise ValueError(f'Recording stopped ({type(error).__name__}); completed clips are preserved.') from None
        _atomic_write(directory / (identifier + '.mp3'), audio)
        saved['clips'][identifier] = {
            'text_sha256': digest,
            'audio_sha256': _sha256(audio),
            'duration': duration,
            'voice_id': voice,
            'model': config['ELEVENLABS_MODEL'],
        }
        _atomic_write(directory / 'manifest.json', _manifest_bytes(saved))
        print(f'Saved {identifier}: {duration:.1f}s', flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', action='append', type=Path, default=[])
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--max-new', type=int, choices=range(MAX_NEW + 1), default=MAX_NEW)
    args = parser.parse_args(argv)
    from dotenv import load_dotenv
    for path in args.env_file:
        if not path.is_file():
            raise SystemExit('The supplied configuration file does not exist.')
        load_dotenv(path, override=False)
    sys.path.insert(0, str(ROOT / 'flask_vocab_app'))
    from config import app_config
    from services.speech_provider import SpeechProvider, audio_info
    source = json.loads((ROOT / 'flask_vocab_app/data/curriculum_units' / (UNIT_ID + '.json')).read_text())
    directory = ROOT / 'flask_vocab_app/static/audio/course/curriculum' / UNIT_ID
    try:
        prepare_recordings(source, directory, app_config(), SpeechProvider, audio_info,
                           dry_run=args.dry_run, max_new=args.max_new)
    except ValueError as error:
        raise SystemExit(str(error)) from None


if __name__ == '__main__':
    main()
