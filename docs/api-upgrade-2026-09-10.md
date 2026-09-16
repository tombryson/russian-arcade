# API upgrade and connection results — 10 September 2026

## Changes

- Updated OpenAI Python 1.83.0 → 3.11.0, Google API client 2.170.0 → 2.200.0, Google Auth 2.40.2 → 2.58.0, OAuthlib integration 1.2.2 → 1.4.1 and Requests 2.32.3 → 2.34.2. Regenerated the hashed dependency lock and installed it locally.
- Preserved Astra with low reasoning for stories, GPT-5.2 for structured cards and GPT-5 mini for lighter activities. Removed unsupported sampling parameters from grading, lesson and sync requests; replaced legacy token limits with completion limits that allow room for reasoning.
- Switched active images to GPT Image 2, a migration target with account access confirmed by actual generation. Retired DALL·E calls in the three standalone card generators now delegate to shared application providers. Image 2.5 remains a future quality/cost evaluation, rather than an untested default.
- Native and application Anki card generation now share the same structured content request: meaning, Russian sentence, sentence translation and optional nuance. Anki no longer requires Yandex translation. Native schedules remain independent of Anki.
- Migrated optional Yandex translation to Cloud v2 service-account API-key authentication. Failed translations return an explicit error and no translation, rather than the string “Unknown”.
- Made ElevenLabs voice pool/model configurable. Random selection on every generation is preserved to provide listening variety. Audio is decoded and normalised in a temporary file before replacing the destination, preserving existing audio if generation fails.
- Added an Anki write timeout, image download timeout, application model overrides and a repeatable connection diagnostic.
- Repaired the two transcription utilities to use `audio.transcriptions.create`, shared `.env` loading and current morphology imports.

## Live results

| Check | Result | Required action |
|---|---|---|
| OpenAI model access | HTTP 200; all configured models listed | None |
| Astra low text generation | Passed | None |
| GPT-5 mini text generation | Passed | None |
| Structured native card generation | Passed | None |
| GPT Image 2 generation | Passed | None |
| ElevenLabs voice access and Russian speech | HTTP 200; audio generated and decoded | None |
| Yandex Cloud translation | HTTP 401 | Supply a Cloud service-account API key with `ai.translate.user` access if optional Yandex translation is wanted |
| Google Drive vocabulary file access | Refresh failed with `invalid_grant` | Reconnect Google OAuth; this does not establish that the OAuth client itself needs replacement |
| AnkiConnect | Local connection refused/unavailable | Run Anki with AnkiConnect enabled, then repeat the check |

Existing secret files were not modified. Google refresh was attempted in memory without replacing its saved token. Smoke tests did not create cards, edit vocabulary or write Anki notes. Generated speech was temporary; image output was not saved to the library. Small provider generation charges may apply.

Validation: the 185-test application suite passed; the expanded six-test provider suite also passed. Dependency compatibility, Python compilation and Git whitespace checks passed. The restarted preview returned HTTP 200 for `/post/`, `/` and `/comprehension`.

The optional legacy Forvo credential is absent, so that standalone integration was not exercised. It is not needed by native cards or the active Anki generator.

## Repeat the checks

From the repository root:

```sh
.venv/bin/python scripts/check_connections.py
# Includes small billable text, image and speech generations:
.venv/bin/python scripts/check_connections.py --generate
```

The command prints status and known error codes, never key values or raw provider exception bodies. A nonzero exit means at least one check failed, including an optional integration.

Put replacement credentials in `flask_vocab_app/.env`, preserving every other entry. `YANDEX_API_KEY` now means a Yandex Cloud service-account key; an old Translate v1.5 key is not interchangeable. OpenAI and ElevenLabs do not need replacement keys based on these tests. Restart the app after configuration changes.

The oldest standalone utilities still have local file-path assumptions and optional Forvo/SpeechKit helpers; those utilities were not run end-to-end against the user's Anki library. The active Flask application does not depend on those helpers. No Anki write or full Drive sync was possible while their connections were unavailable. Speech generation success establishes valid audio, not a linguistic listening evaluation.

## Sources

- [OpenAI parameter compatibility](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2)
- [OpenAI model retirements](https://developers.openai.com/api/docs/deprecations)
- [Image API guide](https://developers.openai.com/api/docs/guides/image-generation)
- [Yandex Cloud authentication](https://aistudio.yandex.ru/en/docs/translate/api-ref/authentication)
- [ElevenLabs model documentation](https://elevenlabs.io/docs/overview/models)
- [Google Drive Python quickstart](https://developers.google.com/workspace/drive/api/quickstart/python)
