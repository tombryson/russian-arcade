# Game quality improvement plan

Status: steps 1–4 implemented and verified on `codex/game-quality-pass`. Steps 5–6 remain planned.

Based on the [16 September 2026 game audit](game-audit-2026-09-16.md).

## Implementation notes — 16 September 2026

This pass changes the existing activities. It does not introduce another game framework.

- **Scoring:** new journey-game results use `game-evidence-v2`. The chance baseline follows each game’s actual scoring rule, including partial credit. Previously answered content, hints and transcripts are excluded from fresh skill evidence. Existing `practice-elo-v1` results retain their original calculation.
- **Difficulty:** games currently use an uncalibrated task rating of 1000. Word difficulty remains a content filter. It is not a measured task difficulty or a TORFL placement.
- **Corrections:** learners can retry an incorrect answer or review missed items after finishing. First answers remain unchanged. Migration 034 adds a separate correction history. Refreshing restores the current review; retries add no coins or skill evidence.
- **Word forms:** native generation considers the profile’s previous selections and the frequency of stored forms. It favours useful inflections over repeated dictionary forms. Explicit case filters and selected lesson occurrences still take precedence. Rare forms remain in the database.
- **Missing Stamp:** a small set of reviewed case and conjugation patterns supports grammar questions. Other questions test contextual vocabulary. The player identifies the objective and shows a short explanation after checking.
- **Follow-up cards:** learners can choose words from a completed game. The generator keeps their original sentences and reuses existing native cards and media where possible.
- **Presentation:** game controls use the selected interface language. Reading requests feedback in that language. Directions renders its built-in landmarks. Narrow layouts keep the check action within reach and preserve space for answer controls.
- **Public demo:** Directions, Pack the Bag, Postcard Pairs and Missing Stamp have prepared samples. They use bundled text and illustrations, without provider calls. The catalogue identifies other games as requiring a local installation. Visitor isolation and request limits remain in place.

### Limits of this pass

Morphological checks cannot prove that every alternative is semantically impossible. Grammar questions therefore use a narrow set of supported constructions. Vocabulary questions also use the English sentence cue. Broader grammar coverage needs reviewed examples.

The new rating rule reduces unsupported gains; it does not validate the rating as a proficiency measure. Repeated content is treated conservatively, including a whole matching round when any constituent was seen before.

Public samples demonstrate the controls with authored introductory material. They do not replace normal vocabulary-driven games. Sample audio is not advertised. The normal media pipeline is unchanged.

No paid model calls or human speech evaluations were made for this pass. Detective’s premise, Directions’ destinations, Pack the Bag’s content fit and longer-session variety still need the work in step 5. Radio and Speaking quality still need the evaluations in step 6.

### Verification

- Full backend suite: **703 tests passed**. After the final answer-timing fix, **54 relevant regression tests passed**, plus a focused whole-word grammar test.
- UI suite: **330 tests passed** across 32 files. Type checking and the production build passed.
- Browser checks covered a wrong answer, correction, refresh, keyboard operation, hints, completion, missed-item review, Russian controls and a 390 px layout. These used a temporary database and provider doubles.
- Public-demo tests completed all four advertised samples with network access blocked. Profile isolation and unavailable generation routes were checked.
- The 5052 preview database moved from schema 33 to 34 with an automatic backup. All rows in its 88 existing data tables matched the backup. SQLite integrity and foreign-key checks passed.
- The default database was initially selected by mistake, then restored from its automatic backup. Its restored SQL contents matched the backup. The preview uses its separate database and runtime settings.

The development preview is running at `http://127.0.0.1:5052/post/`. This pass has not been deployed to Fly.io or copied into the public repository.

## Objective

Improve the activities already available. The first pass should make practice more useful, progress more trustworthy and the experience easier to follow. It should also remove the public demo's blocked routes.

Keep Flask, Preact and the existing database. Extend the shared services where several activities have the same problem. Keep each activity's interaction and content requirements separate.

## Scope and order

Deliver the work in the following order, with a working application after each step. Steps 1–4 form the first release. Steps 5–6 follow once that release has been reviewed.

| Step | Work | Activities affected | Relative effort |
| --- | --- | --- | --- |
| 1 | Preserve first attempts and correct skill evidence | All journey games and the progress bar | Medium |
| 2 | Select useful Russian forms and improve distractors | Flashcards, Missing Stamp and vocabulary-driven games | Medium–large |
| 3 | Allow corrections and add a useful completion screen | All journey games | Medium |
| 4 | Make navigation, language, layout and demo availability consistent | Journey games, Reading feedback and the public demo | Medium |
| 5 | Improve weak game mechanics and content variety | Detective, Directions, Pack the Bag and matching games | Medium–large |
| 6 | Evaluate AI content and connect follow-up practice | Speaking, Radio, Writing, Reading and tutor lessons | Large, incremental |

## 1. First attempts and skill evidence

Extend the saved round record to distinguish the first answer from later practice. Record which contextual item was tested, the response format, assistance used and whether an earlier round had revealed the answer. The server derives these properties from the frozen task and recorded actions.

Keep first answers immutable. Store correction attempts separately. Existing sessions must remain readable and resumable.

Update the journey-game rating policy to account for guessing. A four-choice question, a matching exercise and a constructed answer need different assumptions. Use the actual scoring rule when calculating chance performance; partial-credit matching cannot use the same baseline as a single choice.

Do not treat vocabulary difficulty alone as an established task difficulty. Use conservative task assumptions, document them and check them against reviewed examples. Count supported repetition as practice, rather than a new independent assessment.

Version the new policy. Retain historical receipts and replay their original rules when calculating progress. Merely changing the current policy identifier would risk dropping older evidence. New exclusions must not silently reset existing progress.

**Acceptance:** simulated guessing has no positive expected rating gain across supported question formats and difficulty settings. Previously revealed answers and correction attempts add no fresh skill evidence. Completion coins retain their existing rules. Old progress survives the policy change.

Primary code: [skill evidence](../../flask_vocab_app/services/skill_progress.py), [game sessions](../../flask_vocab_app/services/journey_games.py).

## 2. Russian forms and fair choices

Replace the native card selector's preference for the dictionary form with selection across useful stored forms. Respect the requested case, part of speech and other filters. Reuse the existing treatment of uncommon forms and participles where applicable. Consider recent coverage without confusing a saved word with a mastered word.

Keep the exact surface form when a learner selects a word from a lesson. Preserve its lemma relationship, grammatical interpretation, sentence and source. A form with several possible grammatical readings must be interpreted in its sentence.

For Missing Stamp, distinguish two objectives:

- Vocabulary questions ask which word fits the meaning. Use plausible alternatives with comparable grammatical roles.
- Grammar questions ask which form fits the sentence. Use alternatives from the relevant lemma where there is one defensible answer.

Do not accept a question just because the generator produced the requested JSON. Check that the blank matches the intended occurrence, options are distinct and an alternative cannot also complete the sentence naturally. Reject uncertain generated items. Begin with a small reviewed set of case, conjugation and agreement examples.

Keep English translations attached to contextual examples. This work does not require a single translation field on each lemma.

**Acceptance:** ordinary batches include useful declined and conjugated forms when available. Explicit filters and lesson selections are preserved. Reviewed grammar questions test grammar rather than unrelated vocabulary. Cards retain their required pictures and audio.

Primary code: [card selection](../../flask_vocab_app/services/card_generation.py), [game vocabulary](../../flask_vocab_app/services/journey_vocabulary.py), [round construction](../../flask_vocab_app/services/journey_vocabulary_games.py).

## 3. Corrections and completion

After an incorrect answer, show a short explanation and offer **Try again** or **Continue**. Reopen the relevant controls for the correction attempt. Make clear that the original result is saved. Do not force a learner to repeat an item before leaving.

At completion, show the first-attempt result, the coins actually earned and a **Practise missed items** option when useful. Start with the same items as supported practice. Transfer questions using new sentences can follow later, once their content quality is established.

Where the activity already supports flashcard generation, allow the learner to choose useful items from the review. Preserve the existing automatic generation workflow. Saving a word and creating a card remain explicit actions.

Keep explanations specific and readable. A brief reason for the correct form is more useful than a paragraph of terminology. Preserve the encouraging tutor style in Word Jumble. Native flashcards keep their existing Again, Hard, Good and Easy workflow.

**Acceptance:** a wrong answer can be repaired without restarting. Refreshes and duplicate submissions preserve the first result and the current practice state. Retrying does not award extra coins or rating evidence. A perfect session does not show an empty missed-item action.

Primary code: [session commands](../../flask_vocab_app/services/journey_games.py), [player](../../flask_vocab_app/ui/src/JourneyGames.tsx), [boards](../../flask_vocab_app/ui/src/GameBoards.tsx).

## 4. Consistent presentation and public availability

Use the existing language mechanism for journey-game instructions, controls and feedback. Pass the chosen interface language through Reading assessment as well. Russian learning content remains Russian.

Keep the active prompt, choices and check action close together on narrow screens. Use a compact action area where needed, with enough clearance that it never covers an answer. Verify keyboard operation, visible focus and feedback announcements. Screen-reader alternatives must remain understandable; removing descriptive labels is not an accessibility fix.

Render Directions' existing landmarks, which are currently skipped unless they have image URLs. Treat a meaningful destination and route objective as separate content work in step 5.

Make the catalogue describe what the current installation can actually run. Enable the free Directions sample and a small set of prepared sample games in the public demo. Use bundled media and frozen content, with profile ownership and request limits. Keep paid generation disabled. Unavailable activities must explain this before the visitor starts an unlock sequence.

Introduce consistent descriptions of practice difficulty without automatically relabelling internal word-difficulty numbers as A1 or A2. Preserve existing options while activity-specific level mappings are reviewed. A practice label must not imply TORFL certification.

**Acceptance:** advertised demo samples can be completed without API keys. Other visitors cannot read or alter their sessions. English and Russian interfaces have translated controls. At narrow and desktop widths, the question and action remain easy to find and use.

## 5. Mechanics and variety

**Priority correction, 16 September:** start with Directions. The learner's review showed that the first pass left its central learning task inadequate. Rendering landmarks and adding retries were insufficient. The [corrected audit](game-audit-2026-09-16.md#follow-the-directions) defines the minimum delivery task. Review one complete playable delivery before expanding the other mechanics. Treat technical reliability and learning value as separate acceptance criteria.

The [Directions redesign specification](directions-game-redesign.md) expands this into a complete neighbourhood mission, character encounters, route validation, contextual language, integration and a staged implementation plan.

Four pictures remain sufficient for a choice set. Reuse media when it still fits the sentence, and vary the language and task. Do not stretch four examples into ten supposedly independent assessments. Until more valid items are available, offer a shorter session or identify later rounds as review.

Give Directions a reachable destination and a reason to follow the route. Build Detective around an actual delivery problem, with clues that narrow down a recipient or place. Limit Pack the Bag to objects and situations where packing makes sense. Review whether Pairs and Mailbox Sort serve sufficiently different objectives before expanding both.

These changes need a small playable example and content review for each mechanic. Shared layout improvements alone will not make them enjoyable.

## 6. AI evaluation and follow-up practice

For Speaking, test human recordings containing correct speech, wrong endings, wrong conjugations, hesitation and self-correction. Measure false corrections as well as missed errors. Synthetic recordings can supplement this set but cannot establish how reliably real learner speech is assessed.

For Radio, review complete programmes and their questions together. Check naturalness, duration, audibility and whether each answer is supported by the recording. Keep its listening-comprehension format and avoid adding picture generation.

Then connect confirmed mistakes and selected lesson material to a small number of useful follow-up activities. Start with existing contextual examples and source references. Do not automatically turn uncertain speech recognition or an unreviewed AI correction into a permanent learning record.

## Delivery and verification

Use a new `codex/` branch in the active development checkout. Keep the original private repository and clean public repository histories separate.

Make database changes additive. Back up the development database before applying them. Support existing sessions and retain learner history, vocabulary, media and review schedules. Leave environment files and credentials untouched.

Use a separate test database and provider doubles for routine checks. Add meaningful tests for rating behaviour, answer exposure, correction state, form selection, demo boundaries and language selection. Reuse the existing regression suites. Run small, cost-bounded provider checks only where generated content or real audio needs validation; report their limits separately.

Before merging, play through a correct answer, an incorrect answer, a hint, a correction, a refresh and a completed session. Check both interface languages, keyboard use, narrow layouts and the public-demo configuration. Compare saved progress and coins before and after the pass.

The first release is complete when steps 1–4 meet their acceptance criteria. It should deliver better practice and fewer dead ends. Claims about greater enjoyment or learning effectiveness still require learner feedback.
