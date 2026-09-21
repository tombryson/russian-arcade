# Native flashcards MVP

Updated 10 September 2026 on `codex/native-flashcards-mvp`. **Individual use is the default.** Choose generation settings, generate cards from your vocabulary, and study them. PINs, household setup and another person's approval are not required. The first manual-authoring design was rejected by the owner and is superseded by this workflow.

## Generate, study, adjust

1. Open `/#flashcards` and choose **Generate cards**.
2. Choose card type, number, difficulty, word type, case and topic. The selected words appear before generation. **More options** sets the maximum active native cards per word.
3. Press **Generate cards**. The application generates the answer, Russian example and English translation, then saves each card to your collection automatically. Picture and Russian word/example audio are selected by default; either can be turned off.
4. Choose **Study flashcards**. Reveal the answer, then choose **Again**, **Hard**, **Good** or **Easy**. Scheduling and review history are saved locally.
5. Use **Edit card** or **Delete card** in the collection when the wording is wrong or the card is not useful. Editing is optional, not part of generation. Setting a card aside pauses it without treating it as a forgotten answer.

The vocabulary's `words` table still has no compulsory English-meaning field. The generator writes English wording to each card, where it can be a natural phrase or short explanation. This avoids imposing a single translation on every use of a Russian word. It does not guarantee that AI wording is correct; the individual can change or delete it.

The old `/post/flashcards/manage?word_id=…` link now opens generation for that word. The existing Anki generator remains available at `/tools/anki/`; neither its schedules nor its counters are updated by native generation.

## What is implemented

- Three card types: Russian → English, English → Russian, and a missing Russian word in a sentence.
- Automatic generation using `OpenAIService` and the dedicated `OPENAI_MODEL_FLASHCARDS` setting. As of 10 September its default is `gpt-5.6-luna` with low reasoning; story and other workload settings are separate.
- Structured provider responses, exact selected-form checks, and a generation limit of 20 cards per batch. Case filters read JSON grammatical tags rather than matching their text spacing.
- Saved batch progress. Refresh resumes the same batch; duplicate requests reuse its results. Completed cards survive a failure on another word. Navigation stops starting further requests; an already running request can finish. Reopen the batch URL to continue.
- One durable personal study profile, automatically available across browsers on this local installation. Optional household profiles retain independent schedules.
- FSRS `6.3.2` scheduling at 90% desired retention, five new cards per study day, and sessions of 5, 10 or 20. Due learning steps come first, then due reviews, then new cards. Related cards are spaced apart.
- Counts for words/cards, due/new cards and daily practice; search, collection, topic, direction, state, word type, case and difficulty filters; due/alphabetical/difficulty sorting; set aside/restore and the latest 50 reviews per card.
- Pause, refresh/resume, finish and automatic next-card advancement after each saved rating. Undo is available before revealing the next card, or from the automatic completion summary before another practice starts. Undo records a reversal instead of erasing history. Keyboard: Space reveals; 1 = Again, 2 = Hard, 3 = Good, 4 = Easy.
- English/Russian generation and review controls. The optional Jinja editor remains primarily English.

Automatic picture and Russian word/example speech generation are implemented, with per-stage retry and saved random voice selection. Source grammar, topics, difficulties and mnemonics carry across automatically; the basic-card back shows the full example translation. See the [media migration record](native-media-pass.md). Import/reuse of old Anki media remains separate work. Native review awards no Lingocoins and does not change Elo. Ratings are self-reports, not objective language-proficiency scores.

## Local setup

Use Python 3.12 and Node 24. Follow the [root development guide](../../README.md#start-a-development-instance) to use an isolated database/runtime directory. Install the hash-locked Python requirements, build the UI, and explicitly upgrade the configured database:

```sh
python -m pip install --require-hashes -r flask_vocab_app/requirements.lock
npm ci --prefix flask_vocab_app/ui
npm run build --prefix flask_vocab_app/ui
python -m flask --app flask_vocab_app/app.py:create_app db-upgrade
```

Set `OPENAI_API_KEY` and, for Russian audio, `ELEVENLABS_API_KEY` in the existing ignored `.env` configuration and restart. FFmpeg is required for MP3 decoding and normalization. Preserve existing secrets when changing settings. Existing cards can be studied without a provider. Keep `WORD_POST_HOUSEHOLD_ENABLED=false` and `NATIVE_FLASHCARDS_ENABLED=true`. No `word-post setup` command is needed for individual use. Set `PERSONAL_STUDY_TIMEZONE` before first use if needed; it defaults to UTC and is recorded with the personal profile. The prepared preview uses `Australia/Melbourne`.

Migration **009** introduced the native review tables; **010** adds saved generation batches/items; **011** adds retryable media jobs. Upgrades are transactional, preserve existing records and check foreign keys. Starting the server does not silently upgrade the database.

```sh
python -m flask --app flask_vocab_app/app.py:create_app run --host 127.0.0.1 --port 5052
```

### Optional household controls

Only enable `WORD_POST_HOUSEHOLD_ENABLED=true` if you want separate learner profiles and restricted shared-content editing. This opt-in mode retains the existing setup/PIN and shared draft approval flow described in [Stage 1](stage-1.md). It requires a private `FLASK_SECRET_KEY` of at least 32 characters. Individual credentials cannot unlock household editing. Changing modes preserves both sets of profiles and history; it does not merge their schedules.

### Prepared preview

[Generate flashcards](http://127.0.0.1:5052/#generate) runs from ignored `instance/native-flashcards-mvp/`, with a separate database, settings, assets and build. Restart this particular preview with `.venv/bin/python instance/native-flashcards-mvp/serve.py`. Its ten earlier drafts are retained, but are not required for using the generator. No PIN is needed. The canonical schema-8 database was not upgraded or replaced.

On 11 September, the preview's saved-story media was restored into its configured `media/` directory: five original images and five recordings shared by eight stories. The initial database copy had omitted those files. One duplicate story's two empty media fields were filled from saved copies with identical text; titles, answers and scores were preserved. The private `story-media-repair-*/` directory contains the pre-repair SQLite backup, file hashes and HTTP/media verification. Future preview copies must include legacy media as described in [operations](../operations.md#data-locations).

During the original MVP implementation the API key was unset and generation used a deterministic provider in isolated tests. Live generation is now verified by the dated Astra pilot below.

## Live Astra pilot — 10 September 2026

Five Russian → English cards were generated from the preview vocabulary and saved through the normal native batch API: **что-то, вместе, юмор, зарплата, особенно**. This trial explicitly used `gpt-6-astra` with low reasoning in a separate app instance against the preview database; it did not change the server's global `OPENAI_MODEL_HIGH` default. All five were saved in 25.6 seconds. The ignored preview receipt records the model and batch results in `instance/native-flashcards-mvp/astra-five-20260910.json`.

At the time of the original pilot, the player showed 0/5 practised. Ratings were tested against a temporary copy of the generated database: all five cards completed, Again/Good produced future due times, undo worked, duplicate rating submission was idempotent, and revealed state survived app reconstruction. No original cards were graded by that test. Later user reviews are preserved by the media migration. The 42 backend native-review/generation tests and 15 UI player/generation tests passed.

The examples are natural and the exact selected forms passed validation. The что-то card uses the adverbial meaning “for some reason” in “Мне что-то сегодня не спится.”, with a note distinguishing it from “something.” It is therefore a contextual card, not a universal definition. Its English sentence uses “tonight” for сегодня; this is plausible sleep context but more specific than the Russian wording. This five-card trial establishes working generation and persistence, not a broad model-quality comparison.

Next flashcard priorities: interval previews, accurate recall timing, library collections/bulk operations, configurable scheduling and statistics, then Anki Link export. Four ratings, automatic next-card advancement with undo, audio, pictures, example translations and the first metadata/filter pass are now available. Lingocoins and campaign work follow these flashcard fundamentals.

## Persistence and recovery

Native cards keep vocabulary/form links and immutable versions. Editing the tested prompt/answer creates a replacement objective with a fresh schedule; previous reviews remain intact. Support-only edits can retain the existing objective. Delete removes a card from practice/library while retaining its review history.

The personal profile is a local installation identity, not a hosted account. Native writes still use same-origin CSRF checks. This does not make the application ready for public hosting.

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/card-generation/options` | Available topics, optional word, provider configuration status |
| `POST /api/v1/card-generation/preview` | Select matching words without calling a provider |
| `POST /api/v1/card-generation/batches` | Persist settings and selected words with an idempotency key |
| `GET /api/v1/card-generation/batches/{id}` | Read saved progress/results |
| `POST /api/v1/card-generation/batches/{id}/next` | Advance one text/media stage; retain completed work |
| `POST /api/v1/card-generation/batches/{id}/retry-media` | Requeue failed media only |
| `POST /api/v1/flashcards/{id}/media` | Add or resume media for an existing native card; optional `retry: true` |
| `GET /api/v1/flashcards` | Current profile's counts/library |
| `POST /api/v1/review-sessions` | Start or resume a session |
| `GET /api/v1/review-sessions/{id}` | Read the saved phase |
| `POST /api/v1/review-sessions/{id}/{action}` | Reveal, help, review, next, finish, undo, set aside |
| `POST /api/v1/cards/{id}/delete` | Remove from the active collection without erasing history |

Provider responses are saved before card publication. Batch request keys, item leases and stable content IDs prevent duplicate saves when refreshing or retrying. Review commands separately retain their existing revision/idempotency checks. JSON response format follows [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

Back up using `word-post backup /new/private/destination`, including the database and referenced native assets. Follow the [restore instructions](stage-1.md#backup-and-restore). Anki, Drive and legacy media have their own backup scope. To hide native features, disable `NATIVE_FLASHCARDS_ENABLED` without dropping tables or restoring old data over newer learning.

## Remaining work

The [Anki parity plan](flashcard-parity-plan.md) is now the next milestone: complete media and metadata, four recall ratings, timing, library controls and statistics before campaign/reward expansion. These are requirements, not implemented features.

The live pilot above validates generation and study persistence. Broader content-quality evaluation remains open. Next priorities are optional audio/images, better batch selection and retry controls, real-phone testing and optional native-to-Anki export. Historical Anki import, rewards/Elo, hosted accounts and Fly.io deployment are not part of this correction. The broader migration plan remains in [Anki-to-native migration](anki-to-native-migration.md); its original mandatory-review assumptions are superseded for individual use.

## Cloze and rating correction — 11 September 2026

The [cloze correction pass](cloze-and-four-ratings-2026-09-11.md) shows the generated contextual English translation on the cloze front, uses the database mnemonic for hints, and reveals the exact Russian form and complete translation, links to the lemma on OpenRussian, and implements all four FSRS ratings. The owner approved replacing the five recognition pilot cards with clozes using their existing media, keeping original review history and starting fresh cloze schedules.
