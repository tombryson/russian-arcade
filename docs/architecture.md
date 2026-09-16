# Application architecture

The product runs as a local Flask application with legacy practice tools and opt-in Word Post household profiles. SQLite holds structured learning data; Google Drive is a deliberate capture channel, particularly on mobile. These are complementary stores, not competing implementations of the same data model.

## Boundaries

`app.create_app(config_overrides, service_overrides)` builds an independent application. It registers feature blueprints, the remaining practice routes, session handling, file-serving routes, and database commands. Creating an app prepares runtime directories but does not open the vocabulary database, authorize Drive, or initialize an AI client. There is no module-global running application.

`app.extensions['services']` owns that app's lazy services. Tests can inject feature/provider doubles by service class name. Read-only feature methods do not construct AI clients. Database schema changes are explicit CLI migrations; feature constructors no longer create or alter tables.

Routes validate request data and format HTML or JSON. Repositories hold some persistence queries. Feature services retain much of the domain logic and SQL; moving the remaining queries and routes is incremental work, not a completed reorganization. `models.database.connect_db` enables foreign keys, applies a connection timeout, and closes connections used as context managers. Request-scoped model connections close on Flask teardown.

## Learning data

- `words` identifies a lemma and part of speech; `forms` holds its inflections and grammatical tags.
- `saved_stories`, `writing_exercises`, `lessons`, `word_jumble_games`, and `sentences` retain feature-specific content/results.
- `word_jumble_drafts` stores explicitly saved composition drafts with optimistic revisions. `word_jumble_attempts` retains each checked answer with its scoring scale, rubric version, feedback language and structured advice; migration 006 preserves legacy feedback without guessing missing scales/dates. Sentence-building routes live in their own blueprint.
- `translation_drafts` and `translation_attempts` separate saved answers and checks from reference content in `sentences`. Migration 007 is additive: older translation answers were never stored, so no attempt history is fabricated. Translation routes use a dedicated repository; its provider service prepares sentence pairs, assessments and optional audio.
- `writing_details` adds authored Russian/English titles and English instructions to existing writing tasks. `writing_drafts` stores exact text with optimistic revisions; `writing_attempts` keeps checked versions separately. Migration 008 copies historical answers and any stored feedback without inventing draft/check dates or overwriting the original task rows. Writing now has its own blueprint and repository; the service only prepares tasks and feedback.
- `users`, `user_stories`, and `anki_cards` retain existing progress and Anki mappings.
- `schema_migrations` records explicit upgrades.
- `sync_runs` stores sync status and structured summaries, including failures and pending enrichment.
- `reward_events` prevents repeated sentence rewards using a unique user/reward key.

Sentence assessment awards progress at most once per saved sentence. The translation draft, assessment, reward event and user totals commit together under a write transaction; a failed write rolls back all four. Revision checks before and after assessment prevent stale tabs or in-flight requests from overwriting newer drafts. Existing saved sentences are marked as legacy events during the earlier reward migration, without guessing historic award amounts or changing totals. Translation still uses the legacy local user (ID 1); household content approval, learner identity and canonical activity/reward adapters remain separate migration work.

Migration 004 adds household settings/access, independent `learning_profiles`, immutable `learning_content_versions`, lexical/asset references, `learning_sessions`, canonical `activity_attempts`, retry responses, word evidence and an append-only reward ledger. `app.extensions['learning']` owns these provider-free services. Their short transactions check the selected learner and persist all effects together. The [Stage 1 guide](word-post/stage-1.md) describes the concrete schema/API boundary and remaining native-review work.

## Interface direction

The owner-approved next experience is [Word Post](word-post/README.md). Its first foundation now lives in `flask_vocab_app/ui`: Preact/TypeScript built by Vite and served at `/post/` through a dedicated Flask blueprint/template. That document owns its entire DOM and loads only bundled local assets; navigation to existing grown-up pages is a full document navigation. The preview has sample in-memory state and no learning API or database writes.

The first release is local to one household; Anki is optional for grown-ups; authored/AI-drafted child content requires adult approval. Stage 1 implements learner, content-version, attempt, access and local-asset boundaries behind `WORD_POST_HOUSEHOLD_ENABLED`; the child preview has not yet been connected to these APIs. Native review and provider jobs in the [target architecture](word-post/technical-architecture.md) remain next/later work. See the [implementation record](word-post/implementation-progress.md).

The next usable slice is now [native flashcards and FSRS review](word-post/native-flashcards.md), followed by child adaptations of the existing games. [Progression](word-post/progression.md) separates recall scheduling, task difficulty and Lingocoin rewards. [Storage preparation](word-post/storage-and-hosting.md) retains SQLite for live transactions and uses local files, later Tigris objects, for media/backups.

The working frontend is Jinja/HTMX with Preact components, maintained inside `flask_vocab_app/`. The dormant duplicate backend and incomplete Astro/Preact port have been removed and archived outside the repository; see [retired port](retired-port.md). Future interface work starts from the active application. Any later frontend replacement must be justified by current product needs and preserve complete learning workflows against this backend.

Composition and translation share `static/js/activity_editor.js` for explicit saves, check feedback, draft guards, revision handling and HTMX history. Jinja owns their forms and libraries. Translation preparation and optional audio use the bounded `translation.js` enhancement; the old Preact sentence table has been retired. Loading an existing sentence works without AI; generating or assessing requires the configured provider. Optional audio cannot invalidate a saved assessment.

Writing uses that same editor and preparation enhancement. Its additional `writing_tools.js` owns the word counter and optional, temporary focus timer; neither determines grades or blocks saving. Generated writing tasks are stored before navigation, and assessment receives authoritative task content loaded by ID. A draft and its successful assessment commit together after a second revision check. Writing retains its existing ten-point scale and has no legacy reward award path; household approval, learner-specific attempts and progression still require an adapter.

Multiple UI capture paths remain supported. Captured status, structured-library status, and Anki review status should eventually be explicit in the UI. The immediate sync behavior is documented in `synchronization.md`.
