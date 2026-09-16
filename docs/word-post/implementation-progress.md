# Word Post implementation record

Updated 9 September 2026. This file distinguishes shipped behaviour from target architecture. The rebuilt Russian Arcade entry is at `/post/`; existing activities and integrations remain at their original routes. Earlier preview records below are historical.

## 9 September approved campaign and final-letter brief

Formalised the owner-approved narrative in [Barsik's journey](barsik-journey.md): a small letter, a big adventure; one delivery to the learner; earned Lingocoins unlock worlds; the ending asks the learner to decipher a Russian letter using practised language. The brief defines chapter continuity, language coverage, marking, assistance, retries and acceptance requirements BJ-01–05 / FL-01–06. Curriculum, thresholds and assessment calibration are still proposals.

The hero now uses the agreed supporting line, “Help him find the way, one Russian word at a time.” Programme decisions, progression and backlog are reconciled with this direction. This checkpoint changes documentation and copy only: it does not implement campaign records, unlocks, a rewarding tutorial or an exam, and makes no database/provider/reward changes.

## 9 September correction: automatic individual flashcards

The owner rejected compulsory household roles/PINs, grown-up approval and manual-first card preparation. The default flow is now **select settings → Generate → Study**, with optional editing/deletion by the individual. Household mode is explicitly opt-in. The preceding MVP record below is historical and does not define current access or authoring requirements.

Migration 010 stores generation batches and per-word progress. The existing OpenAI service now produces structured card text; generation uses the vocabulary/type/difficulty/case/topic filters and saves cards directly for individual study. Case selection reads grammatical JSON values. The editor opens only when requested; saved batch responses survive refresh, and one failed card does not discard the others. A durable local personal profile reuses the existing scheduler/history without setup or PIN. Old profiles, drafts and Anki schedules remain intact.

Verification: **180 Python tests and 55 UI tests pass**; TypeScript and the separate production build pass. Added coverage exercises personal access, opt-in household draft handling, CSRF, generation retries/concurrency/recovery, exact forms, partial failure, edit/delete, malformed topic metadata and the structured provider contract. The review response no longer exposes a cloze answer through its title.

Browser testing used three synthetic vocabulary words and a deterministic provider on a separate database at port 5053. Generate two cards → Study → Reveal → Remember → Undo → Refresh → Finish → Edit/Save → Delete completed without PIN or approval. The 360px generation fixture had no horizontal overflow; inputs/selects were 50px tall. This is desktop browser inspection, not real-device testing. The API key remains unset, so no live generation or AI-quality result is claimed. Native automatic generation currently produces text cards; image/audio adaptation remains separate work.

The real-vocabulary preview at port 5052 now runs in individual mode. Its pre-change database/assets backup is under ignored `instance/native-flashcards-mvp/before-personal-mode`. All ten previous drafts are preserved and all 17,557 rows across 20 canonical legacy tables still match. The canonical database remains schema 8; only the isolated preview was migrated to 10. See the [current operating guide](native-flashcards-mvp.md).

## 9 September native flashcards MVP

Built on `codex/native-flashcards-mvp` from `0cf2afe1`. The owner clarified that the absence of a universal English meaning was deliberate. Cards now teach a reviewed use of a word: a Russian context, prompt, contextual answer and optional explanation. Grown-ups can prepare, correct, approve, discard and retire cards; learners can flag confusing meanings without recording a failed recall. The [MVP operating guide](native-flashcards-mvp.md) describes the product and recovery workflow.

Migration 009 adds card projections, per-learner FSRS state, review sessions/occurrences, append-only scheduling events and reversals, and card reports. It extends the existing content/session/attempt/access contracts. The UI supplies overview, search/selection, browsing/history, basic/cloze recall, hints, Again/Good, durable save/resume and immediate undo. FSRS is pinned to 6.3.2. Native schedules are independent of Anki; no native coin rewards or Elo are claimed.

Verification: **166 Python tests pass**, including **28 native workflow tests**; **51 UI tests pass**; TypeScript and the separate production build pass. Browser checks used synthetic approved content for reveal/grade/undo/reload, cloze, report, history, restore and English/Russian language switching. The mobile review was inspected in a 360px test frame; desktop inspection included the grown-up editor. A learner-language access defect and a mobile header wrapping defect found during inspection were corrected. This is not a real-device or child pilot.

The running preview at port 5052 uses a separate database, runtime directories and build under ignored `instance/native-flashcards-mvp/`. Ten contextual drafts reference copied vocabulary; none was approved or practised. All **17,557 rows across 20 legacy tables** match the original, including vocabulary/forms, Anki metadata and old activity history. A verified backup restored all ten drafts with integrity/FK checks. Automated tests separately cover restore of native review/reversal history and assets. The canonical database remains schema 8 and the original port-5050 app remains in place. No provider, Anki, Drive or Fly write was needed.

This delivers F1 and parts of F0/F2/F3. The legacy import/selector repair, durable AI/media jobs, fuller queue controls, review rewards, approved-native Anki export and hosted deployment remain open. The UI review queue is the next place for the owner to refine and approve content before learner use.

## 9 September native flashcard audit and migration plan

Inspected the running Anki tools, active generation/formatting/sync paths, historical Python exporters and the shared learning schema at `79c7a62b`. Read the canonical schema-8 database and old tab-separated export without modifying either. The [focused migration plan](anki-to-native-migration.md) records 1,233 words, 16,049 forms, 192 local Anki metadata rows and 533 legacy export rows; these are distinct from the 117 word-generation counter. Candidate export matching covers 432 distinct current word IDs, subject to content/media review. A JSON-aware nominative query finds 1,048 forms while the current whitespace-sensitive selector finds zero.

The owner confirmed that native practice starts its own schedule and Anki stays untouched. The plan defines the native overview/player/library, selection/counting rules, FSRS integration, v2 content and session extensions, safe undo, reward claims, preparation jobs and later Anki Link. Updated requirements, backlog, architecture and progression now share that decision and implementation boundary.

This is a documentation change, not a native-review release. No profile/content was imported or published, no provider was called to generate cards, no database migration ran and no Anki collection or schedule changed. No local AnkiConnect listener was present during inspection. Native learning tables remain empty in the inspected local dataset. Validation for this change consists of read-only code/data inspection, upstream documentation review, local Markdown-link checks and whitespace/diff checks; application tests were not rerun for this documentation-only update.

## 9 September first-delivery tutorial

The owner requested shorter hero copy and the return of the yellow **Your first delivery · a little adventure** card. The hero now uses the suggested wording verbatim: “Barsik has a letter for you. But to deliver it, he has a whole world yet to explore.” The card is titled **Hello, Barsik!** and opens `#first-delivery`.

The new three-step interface tutorial introduces Lingocoins, demonstrates the greeting `привет` with answer choices/hints/corrections, and leads into the activity list or the required learner/material setup. The detailed coin explanation matches the current `practice-participation-v1` policy: 3 coins per distinct activity/study day, capped at 12 activity coins/day; hints and incorrect answers do not remove eligibility. These are learner-profile rules, not a rewrite of legacy scoring.

The tutorial is explicitly a replayable warm-up. It does not submit learning attempts, publish curriculum, award coins or mark the letter delivered. Refresh/replay starts it again. Existing profile selection, approved activity start/resume, database records and reward logic remain unchanged. The ordinary activity choices still sit below the hero and remain accessible through navigation.

Verification: **14 UI tests pass**, covering tutorial entry/direct links, keyboard focus, both answer outcomes, hints, replay, absence of tutorial writes/rewards, setup handoff and existing practice recovery. TypeScript and the production build pass. Browser inspection covered the delivery card, expanded coin rules, hint/correction/completion flow and handoff to real activities, plus tutorial layout at actual CSS widths of **910px and 354px** without horizontal overflow. No live curriculum generation or real learner practice was performed. Temporary viewport overrides were reset after inspection. The Python backend was not changed; its earlier verification remains recorded below.

## 9 September welcome and narrative refinement

The owner accepted the rebuilt activity flow and requested a more spacious version of the original hero, plus a coherent narrative that can grow through learning tiers.

- Restored the three-line “A small word. A BIG adventure.” composition and large original illustration. Barsik greets the learner in Russian and English. The introductory copy explains that his first letter is an invitation to explore and learn Russian together.
- Gave **Choose what to practise** its own section below the first desktop viewport. The welcome link moves there and focuses its heading; normal Home/Activities/My words navigation remains directly available. Phone layouts stack naturally without fixed-height clipping.
- Removed the redundant general status strip and separate vocabulary banner. Existing-workspace choices are reading, creative sentence practice and vocabulary, with all activities one link away. Household mode retains real approved content, setup and resume actions, with learner identity beside the activities.
- Added the [Barsik journey brief](barsik-journey.md) and reconciled the design, progression, architecture and backlog documents with the owner's latest direction. A future delivery names its sender, recipient, purpose and outcome; chapter position stays distinct from FSRS, skill estimates and participation rewards. No passport, fake level state or story-only gate is introduced.

Verification: **12 UI tests pass**, including welcome-anchor focus/navigation, real activity routes, household isolation/start/resume and existing practice recovery checks. TypeScript and the production build pass. Browser inspection covered the hero and practice section at actual CSS widths of **910px and 354px**, with no horizontal overflow, the working anchor/focus transition and the household's unselected-learner state. No browser warnings/errors were observed in the inspected home flow. Temporary viewport overrides were reset. This is desktop browser inspection, not real-device or child usability validation.

This change modifies presentation and migration requirements only. The Python backend, database schema, real vocabulary and approved content are unchanged; the earlier 71-test Python result belongs to the preceding backend checkpoint. A playable campaign, tier unlocks and native FSRS review remain upcoming. The production build is served by the existing local app at `http://127.0.0.1:5050/post/`.

## 9 September interface rebuild

Implemented on `codex/russian-arcade-rebuild` following the owner's acceptance of the experience correction and explicit removal of the passport.

- Replaced the fictional delivery flow with Home, Activities and My words. Renamed the cat Barsik (Барсик); retained the illustration and visual palette. Removed the sample adventure, passport, stamp component and temporary achievement state.
- Added direct entries into existing reading, creative sentence composition, translation, writing and lesson routes. The same local font/token build now styles the Flask workspace, which has a clear route back to Home. Old forms and HTMX continue to own their interactions.
- Connected household mode to the existing approved-content/session APIs: selected learner, real activity start/resume, answer/hint submission, corrections, completion and recent vocabulary evidence. Errors retain a retryable command ID; expired access clears the active task. Returning from another browser tab reloads learner context.
- Included the original question in saved corrections, so refresh does not separate an answer from its task. Native spaced-repetition flashcards remain upcoming; existing Anki tools are labelled accurately. No production data/schema migration or provider call is part of this UI rebuild.
- Removed passport awards from the future schema, progression and delivery requirements. Historical artwork/reference files retain their original names and checksums; the production derivative is now `barsik.webp`.

Verification: **71 Python tests and 11 UI tests pass**, TypeScript and the production Vite build pass. Browser inspection covered the shared home, reading entry, saved creative sentence game and phone-width layout; the home and loaded game had no horizontal overflow at the checked narrow width. An isolated synthetic activity exercised learner selection, saved correction and reload through the real HTTP API. No live AI grading, child usability study or real-device audio validation was performed.

The first Python run was interrupted by the host's full disk; subsequent verification completed successfully. Logs are under ignored `instance/word-post-stage-1/rebuild-*`. Production vocabulary was not used for practice testing. The existing legacy activity routes still require grown-up access in household mode: their child content/assessment adapters are not completed by restyling. The new player currently handles approved choice questions, not FSRS review or open-ended AI marking.

## 9 September experience review

Reviewed the running original generator, a saved composition game and a saved comprehension story, and completed the new preview sequence. The owner rejects the new flow and copy while retaining its visual strengths. The [experience review](experience-review.md) records specific failures, a recommended task-based structure and the revised migration gate. Programme/design documents now distinguish visual approval from product assumptions. This review checkpoint changes documentation only; the site still displays the criticised preview. Earlier test results establish engineering behaviour, not learning coherence.

## Stage 1 shared learning foundation delivered

Implemented on `codex/word-post-stage-1`, branching from requirements checkpoint `1efe1c33`. The [Stage 1 guide](stage-1.md) documents setup, exact API contracts, backups and limitations.

- Additive migration 004; household PIN/access, explicit learner selection, draft approval and immutable content, server-owned attempts/revisions, reward ledger, lexical references and local assets.
- Household controls at `/post/household`, with shared access enforcement across new and legacy routes. Selecting a child ends grown-up access in the same browser; other-profile sessions and private content stay inaccessible.
- A deterministic choice adapter proves persistence, assisted evidence, atomic completion and retry handling. The native card scheduler and connection of the child preview to these services remain Stage 2 and later work.
- Starter basic/cloze cards are drafts requiring adult review. Setup preserves legacy user 1 as explicitly labelled archived history; new learners receive no copied balance or learning evidence.
- New media/database backup and restore path; existing Drive/Anki workflows and personal rows preserved.

The actual personal database was opened read-only and backed up to `~/.local/share/russian_vocab/backups/20260908-230905-stage-1-rehearsal`. Only the copy was upgraded to schema 4. All **17,540 rows across 12 legacy data tables** matched exactly, integrity passed and no foreign-key errors were found. The original remains on schema 3; earlier media backups remain available.

The isolated inspection instance runs at `http://127.0.0.1:5051/post/household` with separate database/session/media directories under ignored `instance/word-post-stage-1/`. It contains synthetic learners and an unapproved starter draft. Browser checks verified unlock, draft inspection, profile selection and legacy-route rejection in learner mode; desktop and narrow phone layouts were inspected without horizontal overflow. These checks do not replace a real-device or child pilot.

| Stage 1 verification | Result |
|---|---|
| Python regression suite with production assets required | **69 tests pass**, including 24 new foundation/migration/access/restore tests |
| UI suite | **5 tests pass**, including the new legacy CSRF adapter check |
| TypeScript and production asset build | Passed on Node 24.20.0 |
| Database and asset recovery | Completed session, correction, balance and image recovered in a fresh app; incomplete backup detected |
| Browser console | No warnings/errors observed in the tested household flow |

The local Python run is recorded in ignored `instance/word-post-stage-1/python-verification.log`. Expected provider-failure and missing-build fixtures log errors/warnings during tests; the suite completes successfully without external connections.

## Recoverable Git baseline

Work started on `codex/word-post-migration` after reviewing the previously staged removals and uncommitted source. The baseline was split into three local commits:

| Commit | Scope |
|---|---|
| `38fa6e96` | Stop tracking environments, caches, credentials, personal/runtime data; retire the archived failed port |
| `1e87096d` | Existing Flask/app-factory, migrations, sync and isolated-test foundation; replace credential literals in historical utilities with environment lookups |
| `241a6fd2` | Word Post migration plan, approved concept and artwork |

The pre-commit recovery checkpoint is at `~/.local/share/russian_vocab/backups/20260908-211128-git-checkpoint`. It preserves the original index, working patch and source copies. It is private because historical source contained credentials. Removing those literals from current source does not remove them from Git history; the previously committed keys still need rotation. No history rewrite or push was performed.

## Database and media restore rehearsal

`~/.local/share/russian_vocab/backups/20260908-211705-pre-word-post` contains a consistent SQLite backup made with SQLite's backup API, a restored copy, application media, uploads and a verification manifest. The source database was opened read-only.

- All **13 application tables** were checked in the restored copy, with integrity/foreign-key checks and row fingerprints.
- **108 media/upload files** were copied and checked against source hashes.
- After preview implementation and browser testing, every row in all 13 live tables still matched the restored baseline. All **1,233 words** remain intact; SQLite quick check passed.
- The backup covers the application database/media/uploads. It does not back up the remote Drive file or external Anki collection.

The existing owner and legacy progress remain legacy data. Attribution to new learner profiles is still an explicit future migration decision; this change creates no profiles and awards no real stamps.

## Build and design foundation delivered

WP-02 is implemented. WP-03 has its initial working catalogue; the remaining acceptance checks below are still open.

- Pinned Node 24 runtime, npm lockfile, Preact, TypeScript and Vite build under `flask_vocab_app/ui/`.
- Flask manifest integration, separate HTML document and `/post/assets/` boundary. The preview does not load Bootstrap, HTMX, legacy Preact islands or CDN fonts/scripts.
- `WORD_POST_ENABLED` rollback switch, gated `/post/catalogue`, configurable build directory, no-cache entry HTML and cached hashed assets. Missing/invalid builds have a 503 recovery page; a script-load failure leaves a usable HTML fallback.
- Canonical tokens moved into the UI package and compiled into CSS. Local Golos Text/Unbounded fonts, Latin/Cyrillic coverage and unmodified OFL licences are packaged with the build.
- Approved Misha art preserved and compressed to a **135,942-byte WebP**. No base64 artwork or host-only design helper is needed.
- The approved composition is implemented with the home ticket, letter, supportive feedback, word choice, removable sentence tiles, preview pocket and passport, and full-page links to existing adult tools.
- Catalogue fixtures cover resume, long Russian text/stress marks, hints, correct/wrong feedback, unavailable audio, saving/retry, empty/unavailable adventures, completion and partial capture. Fixture buttons do not submit real work.
- CI now installs/builds/tests the UI before running Python tests against the production manifest and assets.

The Moon Picnic sample is an interface demonstration. It uses a supplied model sentence rather than claiming other Russian word orders are wrong. It holds state only in browser memory, and the page explicitly says progress resets on refresh. No new schema, learning API, provider call, Drive/Anki write or root-entry cutover is included.

## Verification evidence

| Check | Result |
|---|---|
| Clean npm lockfile install and production build | Passed on Node 24.20.0; TypeScript checking included |
| Component interactions | 4 tests pass: hints, wrong answers, sentence rearrangement, duplicate taps, focus, navigation, reset semantics and replacement of the server loading fallback |
| Python suite | 45 tests pass, including all 38 previous tests and 7 new route/asset tests; external socket connections blocked in app tests |
| Production assets | Manifest, every built asset and both font licences served through Flask; child HTML/CSS contain no external asset URLs/imports; strict same-origin CSP |
| Browser flow | Letter → hint/wrong answer → word → keyboard sentence building → completion → Passport; reload returns to the honest empty state |
| Browser console | No warnings/errors observed during the tested flow |
| Layout | No horizontal document overflow at 320, 360, 390, 768, 1024 and 1440px on the home; 320px letter/sentence/catalogue checked; light/dark appearance reviewed |
| Asset budgets | Initial JS + CSS approximately 13 KB gzip; illustration 136 KB; six WOFF2 files total approximately 71 KB, excluding WOFF fallback alternatives |
| Data preservation | All 13 tables unchanged against restored baseline after implementation checks |

These are desktop browser checks at emulated widths, not a real-phone performance or child usability study. VoiceOver, 200% text zoom, reduced-motion user testing, real mobile Safari/audio, and the reference-phone timing budget remain open. The CSS includes focus styling, 48px child targets and a reduced-motion rule, but those alone are not an accessibility certification. G1 is not yet fully signed off; G2–G4 remain open.

## Next implementation boundary

Stage 1 provides the minimum shared identity, approved-content, attempt, reward and local-asset contracts. Correct the entry, task labels and learning sequence under the experience-review gate, then deliver WP-17 native FSRS review: per-card identity/state, queue policy, reveal/Again/Good, durable history and safe undo. The [product backlog](product-backlog.md) owns the order; [native requirements](native-flashcards.md) define the remaining acceptance criteria. Adapted existing games follow on those same records; Moon Picnic is no longer required. Confirm the provisional age/reading range before the pilot collection.

Drive capture and SQLite remain complementary. Existing import/reverse-export behaviour is preserved. The planned disposable-file concurrency investigation and capture receipts remain necessary before changing sync semantics.

## Run and recover this foundation

Follow [development commands](../development.md#word-post-ui). Build assets before starting Flask. The current local preview uses `http://127.0.0.1:5050/post/`; the catalogue is available when `WORD_POST_CATALOGUE_ENABLED=1` is set.

To disable the child preview, set `WORD_POST_ENABLED=false` and restart Flask. The old `/` entry and data remain available, subject to household access when enabled. The preview itself creates no new learning records, but Stage 1 APIs do: preserve their expanded database and asset store. Keep `WORD_POST_HOUSEHOLD_ENABLED` enabled when reverting presentation; disabling it restores the unprotected legacy development mode. Never restore the database merely to roll back a visual/build change.

For future distributed releases, keep a release-specific manifest and retain previous hashed asset files for open tabs during rollout. `WORD_POST_DIST_DIR` makes selecting a prepared build possible; full release packaging and asset-retention automation remain future work. Development `vite build` output is disposable and should not be treated as an atomic hosted deployment mechanism.
