# Word Post priorities: native review, shared games and progression

**16 September mixed-vocabulary correction:** the eight [journey game mechanics](journey-games.md) combine familiar SQLite or selected tutor-lesson words with useful new vocabulary. First steps unlocks the mechanics; it does not restrict their vocabulary. Picture games prepare four examples, text games do not wait for pictures, and Radio is a coherent roughly one-minute programme with four comprehension questions. Learners explicitly save newly encountered words. Contextual-example games retain an explicit native-card handoff, and skill observations remain provisional. See [the resource and discovery policy](mixed-vocabulary-and-radio.md). Whole-PDF automatic game generation and calibrated adaptive difficulty remain further work.

**15 September initial pass (superseded for new games):** the eight mechanics first shipped with three-round First steps packs, lesson discoveries, saved answers and common rewards. These old sessions remain readable; new starts use the vocabulary-backed flow above.

**11 September live activity:** [Live conversation](live-conversation.md) now runs separately with GPT-Live over WebRTC, server-side recording and MAI notes. The existing record-and-send game remains available. Real learner calibration, audio-supported assessment and a future transport/variant setting remain open.

**11 September speaking pilot:** the owner requested implementation and model tests for scenario conversation. The [conversation pilot](conversation-pilot.md) now adds microphone/file input, a café exchange, saved audio, provisional text coaching and a three-way transcription lab. [Live experiment results](speech-preservation-results-20260911.md) record preserved and changed grammatical errors. Acoustic verification, calibrated fluency/grammar scores and reward integration remain open.

**10 September owner direction:** finish the [native flashcard parity milestone](flashcard-parity-plan.md) before advancing Lingocoins/campaign work. The first text-only player is a working first pass, not parity with the Anki experience. This expands order 1 to media, automatic metadata, four ratings, timing, library controls and statistics.

Status: owner direction recorded 8 September 2026; ordering, effort and detailed policies below define the programme. Implementation status is recorded separately below. Source initially reviewed at `a4be0db2`.

Implementation update: [Stage 1](stage-1.md) now delivers the shared foundation in order 0. The [native flashcards MVP](native-flashcards-mvp.md) delivers order 1 for a local pilot, including automatic generation and individual editing. Remaining rows describe planned work; their estimates are not a record of elapsed implementation time.

**9 September flashcard audit:** [Anki-to-native migration](anki-to-native-migration.md) refines WP-17 into content/contracts (F0), a durable reviewer (F1), library/queue controls (F2) and native preparation (F3). It records actual legacy content coverage, filter defects and the required extensions to the implemented session/content schema. The owner chose **a separate native schedule with Anki untouched**; historical review import is no longer a first-release dependency. The audit, plan and first native reviewer are implemented. Bulk imports, provider jobs, advanced controls and Anki Link remain open.

**9 September correction and refinement:** the [experience review](experience-review.md) corrected the entry, labels and task flow. The owner subsequently requested a stronger welcome and coherent tiered exploration. The [Barsik journey brief](barsik-journey.md) now governs that narrative: welcome and spacious choices are implemented; the owner has approved earned-coin world unlocks and an exam-style final letter. Orders 5a/5b define the campaign and assessment work, starting with a small complete test journey. Native review remains first. Postal game names below are historical working titles, not required UI labels; Moon Picnic and the passport do not return.

**Implementation:** [First media and metadata migration pass](native-media-pass.md) is delivered. Next: four ratings, interval previews, faster review/undo and timing.

## Decisions and scope

The owner has confirmed that native flashcards should be the default, with **Anki Link** as an optional route using the existing generation/export capabilities. Existing games are suitable candidates for children: their current placement in the older interface is not an audience restriction. Extend Lingocoins and the ELO concept across activities, while distinguishing encouragement, memory and difficulty selection.

The owner reconfirmed **local first; prepare for Fly.io**. Object storage is a future media/backup destination. Hosting does not block the first native deck. Individual use is the default. Adult approval and restricted profiles apply only to opt-in household mode. The approved Word Post design remains the presentation direction.

This file owns the current priority order. It supersedes the earlier “persistent Moon Picnic first; native scheduling later” order in the initial migration proposal. The [delivery plan](delivery-plan.md) retains stable work-package IDs and release gates. Detailed requirements live in [native flashcards](native-flashcards.md), [progression](progression.md) and [storage/hosting](storage-and-hosting.md).

## Ordered backlog

Priority reflects user value, risk and dependencies; ease describes incremental work **after** the listed prerequisites. S = roughly 1–3 focused engineering days, M = 3–6, L = 6–12. Ranges include appropriate tests/documentation, exclude content review and real-device observation, and are estimates rather than commitments. Shared foundations are counted once, not once per game. Re-estimate after the first persistent deck.

| Order | Priority | Deliverable | Ease / effort | Prerequisite and reason |
|---|---|---|---|---|
| 0 | P0, required | Shared learner context, approved content, attempts, local asset IDs and atomic reward ledger | L | WP-04/05/06 plus the minimum of WP-18/21. Prevents each game inventing a different account, save or reward system. Keep this to the first deck's needs. |
| 1 | P0, first usable slice | **Clear practice entry and native flashcards** | L; re-estimate corrected UI scope | WP-17 after order 0, with the experience-review gate. Basic and cloze cards, reveal, Again/Good, due queue, save/resume and undo. Clear purpose, literal controls and continuity with existing activities. |
| 2 | P1 | **Lingocoins across completed practice**, with a simple balance/history | S–M | WP-18 after native review. Reuse the ledger from order 0; reward participation consistently across games. Supply the earned total needed for campaign unlocks; cosmetics can follow. |
| 3 | P1 | **Sentence Post**: prepared sentence tiles and translation choices | S–M | WP-07 and WP-13a after order 0. The preview already supplies much of the interaction; approved answers and persistent attempts are the remaining boundary. |
| 4 | P1, quick win | **Postcard Pairs / Mailbox Sort** | S each | WP-20a after native card content exists. Reuse reviewed words, art and feedback components; two small modes, not two independent engines. |
| 5 | P1 | **Story Mail**: migrate reading/listening and comprehension | M | WP-13b after approved story import. Reuse the existing story/audio/question capabilities, with independent child answers and an initially deterministic question set. |
| 5a | P1, approved direction | **Barsik campaign: one letter, saved scenes and earned-coin world unlocks** | Re-estimate after the content brief | After common rewards and needed activity adapters (orders 1, 2, 3 and 5). Write the pilot ending and language map first; prove the post office and one unlock before expanding the worlds. Requirements BJ-01–05. |
| 5b | P1, approved direction | **The final letter: vocabulary-based comprehension assessment** | Re-estimate with the pilot rubric | Develop alongside 5a using a small seeded journey; do not wait for all worlds. Covered language, saved answers/support, stable marking, a story ending and meaningful retries. Requirements FL-01–06. |
| 6 | P1 | **Anki Link**: optional export of approved native cards | M, plus job/reconciliation foundation if absent | WP-12 after WP-17 and minimum WP-09. Reuse the exporter behind a durable operation; native learning must continue if Anki is closed. |
| 7 | P2 | **Mailbag Mix**: adapt the existing creative word-jumble game | M | WP-13c after common attempts and feedback policy. Preserve its actual “make a sentence with these words” mechanic; provide scaffolding or adult feedback first. |
| 8 | P2 | **Little Letters**: short writing and replies | M | WP-13d after common attempts; WP-09 for AI feedback drafts. Child scope starts with a phrase or 1–3 sentences, with saving and useful follow-up. |
| 9 | P2 | **Lesson Expeditions**: play activities from grown-up materials | M–L | WP-13e after publication/asset protection. Upload/PDF processing stays with grown-ups; children receive approved activities made from those materials. |
| 10 | P2, evidence first | **Elo-style difficulty selection** | L | WP-19 after several comparable task sets and real attempt data. Start in shadow mode; authored levels remain the fallback. No global proficiency claim. |
| 11 | P3 for deployment | **Fly.io household release and Tigris media** | M–L | WP-21 hosting portion after local learning works and hosting is requested. Prepare storage interfaces in order 0; complete authentication, restore and deployment checks before exposure. |

The first deliverable comprises **orders 0 and 1**, not the whole table. Its shared foundations then make the smaller games and progression work substantially cheaper. The native deck comes before Anki Link. Existing Anki history remains in Anki; native review starts independently. The MVP covers F1 and part of F0/F2/F3. Pilot automatic generation and native study while preparing the campaign's letter, language map and reward integration.

Known capture correctness work (WP-S1/WP-10) remains high priority within the existing library workflow. Before expanding Drive writers, prove stale-preview and concurrent-edit behaviour on disposable data. New games are not a reason to postpone or silently change that contract.

## What we can reuse from the existing application

| Existing feature | Actual behaviour observed | Child adaptation / main migration cost |
|---|---|---|
| Flashcard generator | Creates cloze sentences, translations, mnemonics and media, then sends notes directly to Anki and increments generation counters | Generate and save native cards for the individual; review/approval is optional household behaviour before optional export. Generation counts are not mastery. |
| Sentence practice | Generates or accepts Russian sentences, assesses English translations with AI, saves score/audio and can award coins | Prepared translation choices are a quick first mode. Open translation retains its identity but needs a controlled feedback path and versioned attempts. A tile-builder is a related new mode. |
| Comprehension | Stories, questions, images/audio and free-text answer assessment; content and previous answers are currently mixed | Preserve story preparation; publish reviewed versions; separate each child's answers. Do not serve another learner's saved answers as story content. |
| Word jumble | Selects 3–5 vocabulary words and asks the learner to compose a meaningful Russian sentence; AI grades it | This is **creative composition**, not a letter scramble or tile-reordering game. Preserve it as Mailbag Mix; guided sentence frames can precede open writing. |
| Writing | Generates tasks with required words; currently expects longer writing and uses a countdown in its interface | Turn the activity into a short letter; save drafts, offer sentence starters and remove the mandatory countdown. Keep longer practice available by choice. |
| Lessons | Grown-up PDF/image uploads, generated open-ended prompts and response assessment | Separate preparation from play. Children can play the approved prompts without seeing upload/provider controls or private source documents. |

Inspection references: [flashcards](../../flask_vocab_app/services/flashcard_service.py), [sentences](../../flask_vocab_app/services/sentence_service.py), [comprehension](../../flask_vocab_app/services/comprehension_service.py), [word jumble](../../flask_vocab_app/services/word_jumble_service.py), [writing](../../flask_vocab_app/services/writing_service.py), [lessons](../../flask_vocab_app/services/lesson_service.py). This was code inspection; no live AI generation or child usability study was performed.

The initial audit found a word-jumble score/display mismatch, corrected in the [9 September activity uplift](activity-audit.md). Story reward marking and the remaining legacy reward paths still require attention when child adapters are built. New adapters use typed outcomes and a shared transaction instead of copying old persistence paths. The reuse table above records the original audit; subsequent activity improvements are tracked in that uplift record.

## Game mechanics and further extensions

The mechanics below are now implemented as vocabulary-backed activities; their original effort estimates are retained for the planning record. Open composition, independent recall variants and automatic curriculum adaptation remain separate extensions.

| Idea | What the child does | Reuses / measures | Size |
|---|---|---|---|
| **Postcard Pairs** | Matches contextual Russian messages with pictures | Saved examples and images; recognition | S |
| **Mailbox Sort** | Matches Russian messages to mailboxes labelled with their English meanings | Contextual translations and deterministic matching; reading evidence | S |
| **Pack the bag** | Reads or hears messages and packs matching picture cards | Vocabulary examples, prepared audio and images; recognition | S–M |
| **Follow the directions** | Follows relative Russian directions on a street map | Varied routes and optional recorded instructions; no generated picture set | S–M |
| **Missing Stamp** | Supplies the missing word in a short message, initially with choices and later from memory | Cloze cards; choice-based support and independent recall recorded separately | S–M |
| **Post Office Radio** | Listens to a roughly one-minute Russian programme and answers four comprehension questions | One programme recording, plausible answer choices and supporting quotations; optional transcript and new-word saving | M |
| **Lost Parcel Detective** | Combines a contextual picture clue and a route clue to identify a delivery | Saved examples and routes; comprehension and inference | M |
| **A Letter Back** | Rebuilds the Russian recording with word or phrase tiles and English context | Contextual audio; supported listening/reconstruction. Open writing remains in the existing activities. | M |

The next refinement is content quality and variety across real lesson/vocabulary pools: preserve grammatical forms, reject unclear examples, improve ambiguous image choices and evaluate provisional skill signals. Continue using the existing contextual preparation, media and attempt records rather than creating another source of vocabulary truth.

## One learning system behind every game

All games submit the same core attempt envelope: authorised learner, session, published activity version, submission ID, response, recorded support use, assessment policy and server outcome. Adapters own their content and grading rules; persistence, rewards, asset access and progress history remain shared.

| Signal | Purpose | What may update it |
|---|---|---|
| FSRS memory state | Decide when a particular recall card returns | Qualified recall reviews of that card, with the defined assistance policy |
| Skill/difficulty estimate | Choose an appropriate next challenge | Comparable, assessed task evidence; initially observed without controlling selection |
| Lingocoins | Recognise completed practice and unlock campaign worlds | Server-verified eligible earnings; spending does not relock destinations |
| Final letter | Demonstrate comprehension of a new message using practised language | Saved answers and support assessed against the pinned letter rubric |

A game can add word evidence without scheduling a card. Matching after seeing an answer, copying a sentence and independently recalling a word must remain distinguishable. The reward is for engaging with learning; honest “I forgot” answers must not be financially worse than “I remembered”.

## First native release acceptance

Generate a small deck (approximately 5–10 cards) for individual study; separately verify opt-in household approval. Complete a session, reload and restart the server, then confirm the due state/history survives. Test two profiles, two tabs, repeat submissions, an incorrect answer, assistance, undo and a missing optional asset. Run with AI/Drive/Anki unavailable. Preserve every existing lexical ID, legacy record and external mapping.

This release must demonstrate durable learning and a recoverable database, not only card animation. The [native requirements](native-flashcards.md#acceptance-tests) define the detailed checks.

## Remaining product refinements

Local-first delivery, native-first review, optional Anki Link, independent native scheduling and shared child games are confirmed. Age/reading range is still provisional; confirm it when reviewing the pilot content set. Earned-coin world unlocks and the final-letter assessment are approved directions. Coin amounts/thresholds, letter length, rubric and skill display language remain recommendations to refine during implementation. Preserve the old collection/history; the owner's separate-schedule choice does not authorize resetting Anki.
