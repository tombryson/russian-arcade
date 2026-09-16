# Native flashcards: parity with our Anki workflow

10 September 2026. This is the implementation plan requested after the first five-card pilot. It replaces the earlier two-button MVP target as the next flashcard milestone. **The first media and metadata migration pass is now implemented.** See [the implementation record](native-media-pass.md) for delivered features, verification and remaining work. Four ratings, timers and the larger library/scheduler changes remain planned.

**Owner correction and source audit, 10 September:** the [Russian flashcard audit](russian-flashcard-source-audit-2026-09-10.md) now defines the immediate corrective pass. Practice must select distinct stored forms and generate grammatically matching contexts, with required illustration, form audio and sentence audio. It identifies lemma-biased selection, missing source grammar, lost cloze meanings and overly broad sibling deferral. Repair those content/selection/readiness gaps before extending the reviewer. Earlier text-only or optional-media assumptions are superseded for completed generated cards; partial work remains saved and retryable.

## Why the native result is weaker

The first pass connected text generation to a durable scheduler, but omitted much of the existing learning experience. The old Anki pipeline builds a complete multimedia note; the initial native pipeline saved four text fields and rendered three basic card directions. The first migration pass now adds media and lexical metadata to that pipeline. Passing persistence tests did not establish feature parity.

The migration has two sources: our Python generators supply content, media and grammatical metadata; Anki supplies the reviewer, four recall ratings, timers, library operations and statistics. Both need an explicit equivalent in the application. A new model alone cannot provide those features.

Keep the user workflow automatic: choose words and card options, click Generate, then study. Editing, replacing media and correcting translations are available to the individual. No mandatory manual drafting, household split, PIN or approval stage. Randomly selected Russian voices are deliberate listening variety and must be preserved.

## Model change delivered now

`OPENAI_MODEL_FLASHCARDS=gpt-5.6-luna`, with low reasoning, now controls the shared native/Anki text generator. The requested provider-qualified name is `openai/gpt-5.6-luna`; the direct OpenAI SDK sends `gpt-5.6-luna`. This setting is separate from story, lesson/vision and lighter activity settings. Pictures still use GPT Image 2; Russian speech still uses ElevenLabs Multilingual v2 and the existing random voice pool. [Luna model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-luna).

Three unsaved live samples passed the structured-output and exact-word validation checks. They took approximately 5.9, 1.6 and 1.7 seconds. This confirms access and compatibility, not superior linguistic quality: “He’s somehow quiet today” is understandable but less natural than “For some reason, he’s quiet today.” Keep this example in quality evaluation. The five existing Astra cards and their schedules are retained.

**11 September:** [Cloze and four-rating correction](cloze-and-four-ratings-2026-09-11.md) delivers the contextual English translation on the cloze front, database mnemonic hints, dictionary links, all four ratings and conversion of the five pilot cards. Grammar/form selection, required-media readiness and timing remain open.

## Feature inventory and migration requirements

| Area | Existing Anki workflow | Native state | Required migration |
|---|---|---|---|
| Complete card content | Russian form, sentence/cloze, meaning, sentence translation, mnemonic and dictionary link | Generated text, contextual English meaning and mnemonic, inflected answer, full example translation on reveal, OpenRussian lemma links, mnemonic and lexical metadata; reusable note model still pending | One generated content record with all fields; clear front/back layouts and optional notes |
| Russian speech | Sentence scripts and active service generate speech with varied voices; older word script uses pronunciation recordings | Automatic word/example MP3s, replay, speed controls and stored random voice selection | Automatic word/sentence recordings, replay, playback speed and optional autoplay; record selected voice |
| Memory picture | Generated illustration tied to the sentence | Automatic image generation, saved assets and a dedicated illustration area | Generate/import image once, persist locally, place on the chosen side and allow replacement |
| Media storage | MP3/PNG files in Anki media directories | Hash-based local assets; validated images, MP3 and WAV, independent of Anki paths | Validate MP3 output, register assets and attach roles; stop depending on Anki paths |
| Card variants | Basic and cloze notes, with Anki templates handling presentation | Russian → English, English → Russian and one-blank Russian cloze | Match these first; add listening and typed recall using shared content; optional reversed cards |
| Recall ratings | Again, Hard, Good, Easy with next interval displayed | Again/Hard/Good/Easy in UI, API, SQL history and FSRS; hint use recorded separately | Four rating shortcuts delivered; next-interval previews and smoother review transitions remain |
| Timing | Per-answer recorded time and optional visible timer | Event timestamps, but no active recall duration | Measure recall and answer-reading time; pause correctly; expose useful statistics |
| Tags | Exported POS, case, tense, mood, difficulty and topics | Source POS, grammar, difficulty and all topics carried to card versions and shown as readable tags | Carry and index metadata automatically, with editable user tags |
| Library | Search, sorting, selection, tags, deck operations, card information | Search, direction/topic/state/deck/POS/case/difficulty filters; due/alphabetic/difficulty sorting; limited history | Faceted browser, meaningful sorts, saved searches, bulk operations and full card information |
| Organisation | Notes create related cards; decks and tags organise them | Stable card/version IDs, but each generated item becomes a one-card content pack | Separate user collections/decks from content packs and generated note identity |
| Scheduling | Configurable limits, learning/relearning, bury/suspend and custom study | FSRS, due queue, sibling spacing, fixed five-new limit, session sizes and suspension | User/deck settings, explicit bury/unbury and cram mode |
| Statistics | Review counts, study time, answer distribution, intervals and memory measures | Basic counts and latest 50 reviews | Aggregates, time/recall trends, workload forecast and difficult-card lists |
| Corrections | Edit during study, flag/bury/suspend, change media | Separate editor and report-to-suspend flow; no ordinary flag | Edit and return to study; distinguish flag, bury, suspend and delete |
| Export/import | Scripts construct Anki notes and external files | Old generator remains; saved native cards have no Anki Link exporter | Export the same saved content/media/tags without regeneration; optional content import later |
| Reliability | Anki persists collection and review history | Transactional history, resumable text/media stages, stored voice selection, undo and asset backups | Extend the same guarantees to media jobs, timing and bulk operations |

## 1. A complete automatic content and media pipeline

Use a generated **note** as the reusable content record: selected lexical ID, exact form, Russian example, English meaning and example translation, mnemonic, image, word audio, sentence audio, tags and provenance. A note may supply several cards; each card retains its own schedule. Anki’s note/card distinction is useful here because recognition and production should not share one memory state. [Notes and card types](https://docs.ankiweb.net/getting-started.html#notes--fields).

Implement sequential preparation with independently retryable stages:

1. Select exact lexical forms and grammatical targets, with varied or focused coverage, and snapshot the selection and metadata.
2. Generate and validate contextual text using Luna low, retaining both target meaning and sentence translation; validate grammatical use as well as spelling and use bounded corrective retries for failed validation.
3. Select a Russian voice randomly from the configured pool and save that choice for this job.
4. Generate the requested audio and image from that saved text.
5. Validate/store each asset and publish the completed card bundle.

A network retry reuses the selected voice and completed stages. An explicit “new voice” or “new picture” action creates a new variant. Offer word audio and sentence audio separately; sentence context helps disambiguate pronunciation and stress. English speech can remain an optional setting from the older basic-card workflow. Never invent stress marks by blindly rewriting lexical forms.

The generation screen should show counts for ready cards, work in progress and failed media. The sentence illustration, target-form audio and sentence audio are required for a completed generated card. If one fails, retain text and completed assets as recoverable work and expose “Retry audio/image”; do not mark it ready for study. Generation must continue independently of the open page. Do not regenerate successful stages. Study of completed saved cards must not require OpenAI, ElevenLabs, Yandex or Anki to be reachable.

**Concrete storage work:** extend `LocalAssetStore._media_type()` to decode/validate bounded MP3s, record MIME type and duration, and use the existing hash-based storage and asset references. The current four-asset cap must be reviewed for image + word audio + sentence audio + optional English audio/variants. Avoid overwriting `word{ID}_form{ID}.mp3` when different examples exist. Store provider/model/voice/settings, source text hash, prompt version and generation timestamp separately from the public card text. Existing media can be reused only when its text/context matches.

Presentation defaults should fit the activity: recognition can show the Russian word, context and memory picture with replay; production and cloze should reveal answer-bearing Russian audio on the back or as explicit help. Listening cards use audio as their prompt. Allow the individual to choose image placement and autoplay rather than enforcing one pedagogy. Keep original Cyrillic, ё and proper punctuation; display the complete example translation on the answer side.

## 2. Four ratings and an efficient player

Make **Again · Hard · Good · Easy** the normal reviewer controls. An optional two-button preference can remain available to anyone. Hard means recalled with difficulty; it is not a substitute for a failed recall. Display an approximate next interval on each button. Use Space to reveal, keys 1–4 for ratings and a clear replay shortcut. [Anki rating behaviour](https://docs.ankiweb.net/studying.html#answer-buttons).

This requires changes to `ReviewScheduler`, request validation, the `review_events.rating` SQL constraint, review types, translated copy, keyboard handling and tests. The installed FSRS library already supports all four ratings. Apply a forward migration that preserves every old rating, state, command, reversal and trigger. Old Again and Good records keep their meanings; no rescheduling of the whole collection merely to add buttons.

After rating, move to the next card without the current compulsory feedback-page/Continue cycle. Keep a visible “Undo” action and brief saved feedback. Extend undo to work after the next ungraded card has appeared, with conflict protection when another review has already changed the relevant state. Pausing, resuming, refreshing and finishing must preserve the exact phase.

Review the current automatic assisted→Again override as part of this change. Proposed behaviour: record help use separately and let the individual choose an honest rating; ordinary prompt playback is not a failed answer. Document any resulting scheduling-policy change rather than silently changing historical ratings.

## 3. Timer and response-time analysis

Add an optional on-screen timer and record timing regardless of whether it is visible. Store:

- active time from a ready prompt to answer reveal;
- active time from reveal to rating;
- total answer time, interruptions, help and audio replay indicators;
- timing source/version and whether the duration was capped or incomplete.

Start once content is ready, use a monotonic browser clock, and exclude hidden-tab time, explicit pauses and network waits. Persist acknowledged timing segments by occurrence ID so refreshes and retries do not double-count. Bound client values on the server; never subtract session timestamps and call the entire interval recall time. Missing historical durations remain null.

Anki records time from showing a question until rating and caps unusually long answers, with 60 seconds as its documented default. **Timing does not determine its schedule.** Preserve that distinction: show response-time trends without automatically converting a slow answer into Hard/Again. [Anki timers](https://docs.ankiweb.net/deck-options.html#timers).

Show median recall time and recent trend per card and comparable activity type, along with total active study minutes and cards/minute. Separate reading, typing and listening; mark helped/interrupted attempts. A useful future view is “correct but slow,” not an unsupported global fluency score. The installed FSRS `review_card` accepts `review_duration`; record total milliseconds there while keeping phase-level timing in our own history.

## 4. Metadata, tagging, ranking and library controls

The lexical store already has much of the needed information. Copy trusted metadata automatically; use the model for language content, not to invent identifiers or overwrite grammatical classifications.

| Metadata | Source and treatment |
|---|---|
| Lemma, exact form, word/form IDs | Existing vocabulary and forms; stable links |
| Part of speech | Preserve source POS and provide a normalised display/filter value |
| Case, number, gender, animacy, tense, person, mood, aspect | Available form tags; store unknown as unknown |
| Topics | Carry all source topics, not only the topic selected in a generation filter |
| Lexical/form difficulty | Preserve both where available; separate from FSRS memory difficulty |
| Card type, direction and modality | Generated card specification; basic/cloze/listening/typed are distinguishable |
| Collection, batch and custom tags | User organisation; independent from immutable content packs |
| Origin and generation details | Source import, model, prompt version, voice/image provenance, dates |
| Learning measures | Due date, state, interval, reviews, lapses, last rating, active time, FSRS difficulty/stability/retrievability |

Persist a versioned metadata snapshot and an indexed filter projection. Normalise aliases such as `instr`/`ablt` and `prep`/`loct`. Keep user tags independent of derived grammatical facets. Metadata changes should not reset a card’s memory schedule. Projecting current lexical metadata should not rewrite what was recorded with older review events.

Support combinations such as **Noun + Genitive + Food + Due** with accurate counts, a visible clear-filters action and saved searches. Provide sorting by due date, recently added, alphabetic order, lexical difficulty, lapses, last studied and response time. Show the chosen sort explicitly. Paging and indexed server queries should replace loading every card and performing per-card membership queries as the library grows. [Anki browsing](https://docs.ankiweb.net/browsing.html), [searching](https://docs.ankiweb.net/searching.html).

Add bulk tag/untag, move to collection, suspend/restore, bury/unbury, flag, regenerate selected media and export. A flag means “look at this later”; bury means “tomorrow”; suspend means “until restored.” These must not all become the existing report-and-suspend action. Allow explicit schedule reset with a reviewable summary and preserved history.

## 5. Deck settings, statistics and custom practice

Replace the fixed five-new-cards policy with personal/deck options for new-card and review limits, learning/relearning steps, desired retention, ordering and sibling spacing. Persist scheduler policy/version with reviews, as the existing code already does. Keep due practice and custom browsing distinct: sorting the library should not secretly alter the due queue.

Add a clear custom-practice choice: ordinary scheduled study or practice without rescheduling. A saved search can create a temporary session without moving content between decks. Preserve original deck membership and memory state in non-rescheduling mode. [Filtered study](https://docs.ankiweb.net/filtered-decks.html).

Statistics should show ratings, workload, effective reviews after undo, lapses, time spent, intervals, retention and card difficulty/stability. Distinguish unique cards, words, review attempts and generated cards. Keep lexical level, recall difficulty and future activity Elo separate. Optimising personal FSRS parameters can follow enough real review data; it is not needed for the first complete player. [Anki statistics](https://docs.ankiweb.net/stats.html).

## 6. Import, Anki Link and storage portability

Export the saved native note, card templates, media and tags rather than making new provider calls. Store external note IDs separately from card IDs, check the destination note type/fields and use an outbox with stable native identifiers and reconciliation. A timeout after a successful Anki write must not create a duplicate on retry. Export remains optional when Anki is closed.

Content import from existing exports/Anki should preview matches and missing media and preserve provenance. The owner’s decision remains: independent native schedules, with Anki history untouched. Do not seed native mastery from old generation counters or infer exact word identity from English translation.

Keep SQLite for structured records and review events, and local asset storage now. Later use Fly-compatible object storage for media/backup blobs through the asset boundary; the live transactional SQLite database is not an object-store blob. Restore tests must include referenced media and active sessions. Hosted accounts, multi-device conflict handling and offline queues are separate delivery work.

## Delivery sequence and acceptance

These are ordered deliverables, not claims that the whole Anki ecosystem can be reproduced in one patch.

| Order | Deliverable | Acceptance gate | Relative effort |
|---|---|---|---|
| 1 | Correct form-based generation, grammar data and complete media | Distinct form selection and focused forms practice; additive grammar repair; context validates the selected analysis; target meaning retained; every ready generated card has a picture and both recordings; IDs/history preserved | Medium–large |
| 2 | Four ratings and faster review interaction | All four ratings produce valid schedules; interval previews; no compulsory Continue; undo/restart/duplicate tests pass | Medium |
| 3 | Accurate timer and useful card history | Hidden tabs, media loading, pause/resume and retry excluded/handled; ratings stay user-selected | Medium |
| 4 | Indexed library, collections, saved filters and batch operations | Compound facets and sorts match SQL counts; metadata edits preserve schedules; existing cards are backfilled | Medium–large |
| 5 | Deck settings, custom practice and statistics | Configurable policy; non-rescheduling mode leaves due dates unchanged; aggregates reconcile with history | Medium–large |
| 6 | Anki Link and optional content import | Same text/media/tags exported; retries deduplicate; native study works without Anki | Medium–large |

Within order 1, follow the [source audit's corrective sequence](russian-flashcard-source-audit-2026-09-10.md): repair form selection and grammar coverage, restore the contextual generation contract, enforce complete media readiness, and make presentation/sibling behaviour support forms practice. The pilot's successful media enrichment did not complete that gate. Do not reorder Lingocoins or campaign work ahead of this parity milestone. Then connect complete native practice and existing games to rewards and Barsik’s journey. Wider Anki features—arbitrary template scripting, image occlusion, shared-deck discovery, add-ons and complete AnkiWeb-compatible sync—are outside this first parity target and should be assessed separately.

## Migration hazards and checks

- **Audio validation:** the migration now accepts decoded MP3; keep malformed/truncated and bounded-duration checks. Test real decodable provider output, malformed/truncated files, size limits and mobile playback.
- **Missing facets:** the migration now preserves available source metadata. Older cards gain it when enriched; records without lexical metadata remain unclassified. Backfill from lexical links/batch snapshots; surface unmatched records instead of guessing.
- **History loss:** extending SQLite rating constraints requires careful table migration with foreign keys and append-only triggers restored. Test on a copied database containing old reviews, undo records and an active session.
- **Unexpected schedule reset:** classify media/tag/presentation changes separately from changing the tested answer. Preview content corrections that require a new memory objective.
- **Duplicate cost or media:** persist provider results, selected voice and per-stage job IDs; retries reuse successful output. Changing a model does not regenerate existing cards automatically.
- **Meaning drift:** evaluate polysemy, case agreement, idioms, ё/stress and ordinary English on fixed samples. Keep corrections simple and individual. Neither Luna nor a strict JSON schema guarantees good wording.
- **Timing distortion:** test hidden tabs, clock changes, long pauses, rapid taps, audio playback, lost requests and two tabs. Preserve measured/estimated/unknown distinctions.
- **False completion claims:** functional tests establish behaviour; separately inspect finished cards and listen to Russian audio. Use copies for synthetic study so testing does not consume the user’s new-card allowance.

## Code map

Generation and metadata: `services/card_generation.py`, `services/openai_service.py`, `utils/formatters.py`, `models/words.py`, `models/forms.py`.

Media: `services/card_media.py`, `services/card_metadata.py`, `migrations/011_card_media.sql`, `ui/src/CardDetails.tsx`, `services/elevenlabs_service.py`, `services/flashcard_service.py`, `services/learning_assets.py`, `ui/src/NativeReview.tsx`; reference the three `scripts/vocab_to_anki-card*.py` workflows and pronunciation helpers.

Reviewer: `services/native_review.py`, `services/review_scheduler.py`, `blueprints/native_review.py`, `ui/src/NativeReview.tsx`, `ui/src/review-types.ts` and `migrations/009_native_flashcards.sql`.

Library/content: `repositories/card_repository.py`, `contracts/flashcards.py`, `services/card_authoring.py`, `services/learning_content.py`, `ui/src/GenerateCards.tsx`.

Tests: `tests/test_card_media.py`, `tests/test_native_flashcards.py`, `tests/test_personal_flashcards.py`, `tests/test_provider_upgrade.py`, `ui/src/NativeReview.test.tsx`, `ui/src/GenerateCards.test.tsx`. Extend these with real asset fixtures, migration preservation tests and four-rating/timer/library coverage. Provider smoke tests remain separate from deterministic CI.
