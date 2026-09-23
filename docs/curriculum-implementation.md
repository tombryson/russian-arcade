# Curriculum implementation status

This guide records the first implementation of the [curriculum uplift plan](curriculum-uplift-plan.md). It adds teaching and diagnostic evidence. It does not replace the published A1 journey or introduce a new level gate.

## Available learning sequence

Open **Curriculum → A1 → Places and Directions → Where and where to**. The direct route is `/curriculum/units/location-destination-v1`.

The unit contrasts location and destination with **в / на**. It includes six examples, four contextual questions, three typed-form prompts, three listening questions and an original Writing task. The examples distinguish movement within a place from movement towards it. Choosing the case from the presence of a movement verb alone is not enough.

Practice uses the existing activity player and saved-session store. It resumes unfinished work, saves hints with each answer and returns to the unit when finished. Completion uses the existing activity reward policy. There is no separate curriculum coin balance or schedule.

Typed-form practice uses a separately versioned pack. It accepts authored variants, including a noun alone or its full prepositional phrase where appropriate. Case, spacing, final punctuation and ё/е are normalised for comparison. The exact submitted text is retained. No model guesses whether an unrelated answer should count.

Listening practice uses three bundled Russian messages. Learners hear the recording before choosing an answer. The transcript stays hidden until requested or after the answer is checked. Hints and transcript use are saved separately. A browser playback receipt enables answering, but is not proof of attention or unaided understanding. Replaying the same recording does not remove earlier support.

Recordings are prepared once through the existing speech provider and configured random voice pool. Playback makes no AI call. A failed audio load offers replay or transcript support; a failed receipt save can be retried without replaying. Text hashes, audio hashes and durations bind each recording to its published question. Missing or changed recordings cannot be silently replaced.

The Writing task opens in the existing Writing workspace. Returning to it reopens the saved draft. Its diagnostic checks whether a friend can understand the message; the ordinary tutor feedback can also explain grammar. A return link leads back to the unit.

The Speaking link opens the existing directions scenario. New Fluent A1 directions sessions save one narrow criterion: asking where the required place is. Their review uses the original learner audio. A clear short question can satisfy that task even when there is too little speech for overall grammar or fluency scores. Support independence remains unverified; this is not a proficiency result. Older conversations and unmapped scenarios retain their current review path.

The public sample demo supports choice, typed-form and listening practice without an AI call. Original Writing is available in individual local profiles and hosted accounts. Optional household mode retains its existing separate Writing workspace, so this unit does not offer a child-owned Writing task there. Fluent Speaking retains its existing microphone, provider and spending requirements.

No vocabulary is inserted by opening the unit. Word capture, enrichment, mnemonics and native card generation retain their existing pipelines.

## Requirement mapping

`data/curriculum_requirement_map.json` relates the 110 older A1 targets to the 239 A1–B2 reference requirements. Each link records its scope, source and limitation. Related content does not count as equivalent assessment.

The [coverage inventory](curriculum-coverage.md) is generated from the map and published content. It lists gaps as well as candidate links. It distinguishes static authored tasks from runtime generation. Counts are not proficiency percentages, and no learner grades are transferred by the map.

Regenerate or check the inventory from the repository root:

```sh
python scripts/render_curriculum_coverage.py
python scripts/render_curriculum_coverage.py --check
```

## Saved task and result contracts

A new task can carry an immutable curriculum contract. It freezes the actual task, level, topic, requirement, response mode, rubric and permitted support. The server validates these against the reference catalogue. Hashes detect later changes; they are not authentication credentials.

Criterion reports attach to owned attempts. They must reference the saved contract and every expected criterion. Text evidence must quote an exact span of the submitted answer. Audio evidence requires a bounded interval in the original recording. Unknown criteria, invented mastery fields and incompatible response modes are rejected.

An uncertain result is `insufficient_evidence` with a null score. It is not an incorrect answer. Supported attempts retain their support record. One task cannot silently become independent evidence after a hint or model answer was shown.

The first adapters cover authored unit choices, controlled text, listening, Writing and the mapped Fluent Speaking situations. New A1–B2 Writing generation requests one or two explicit writing objectives and freezes their wording in the task. Older tasks keep their existing feedback path. See [Writing evidence](curriculum-writing-evidence.md) and [Speaking evidence](curriculum-speaking-evidence.md) for validation and failure behaviour.

These reports are diagnostic. They do not award a TORFL level, change a course pass or convert Elo into proficiency. Exact evidence validates attribution; it does not by itself prove that an AI judgement is linguistically correct.

## Storage and migration

Migration `048` adds explicit release, target-catalogue and content identities to focused course practice. Historical attempts continue using their saved identities. Old submission receipts remain replayable.

Migration `049` adds two tables:

| Table | Purpose |
| --- | --- |
| `activity_task_contracts` | Frozen criteria for an owned, existing task. |
| `activity_criterion_reports` | Immutable criterion judgements for its saved attempts, with support and response hashes. |

Migration `050` adds `learning_item_support`, keyed by session and question. It records playback, transcript and hint receipts for listening items. The existing activity attempt stores the answer. Its criterion report must agree with those receipts and the frozen audio identity. Previous choice and typed-form packs, contracts and cached responses remain unchanged.

These tables extend the existing task stores. They do not replace `words`, `forms`, activity attempts, course observations, coin events or FSRS schedules. Writing results, criterion reports and existing rewards commit together after the task revision is checked again. A failed review cannot leave a partial new grade.

Account import remaps typed task and attempt references when numeric IDs collide. It preserves contract and report payloads. A payload that would require rewriting embedded identities is rejected for explicit review instead of being altered through string substitution.

Speaking reports bind the contiguous learner recording, including pauses, to its saved chunk metadata and hashes. Review rechecks those files before committing. An import containing these reports requires `--local-audio-root`; it verifies the source recordings and assembled audio before producing an artifact. Copying the verified media remains a separate migration step.

The migration audit covers the new tables and the older course records. Use a copied database to rehearse an upgrade. The existing migration runner creates a SQLite backup before upgrading and checks foreign keys before commit. No existing forms are regenerated and no `.env` changes are needed.

## Course release routing

The existing course API still defaults to the learner's current enrolment. An explicit `release_id` reads a published release without switching enrolment. `band` must agree with that release.

New links include release identity. Old attempt-ID bookmarks still load the original saved attempt. A historical course can be inspected, but starting new preparation for it requires that it be the active enrolment. Unknown versions fail rather than loading today's questions into an old attempt.

Neither published A1 catalogue was changed in this build. Existing passes and earned A2 access remain governed by their original release.

## Morphology

New form imports retain additional case, gender, animacy and part-of-speech tags, including short forms, participles and gerunds. Targeted form selection applies requested constraints before the existing rarity and rotation rules. It returns no match when the requested contrast is unavailable.

This is a forward import and selection change. It does not rewrite personal annotations or regenerate the existing form table. A reviewed backfill remains separate. Morphological case tags also do not identify a grammatical function on their own: accusative object and accusative destination need different task context.

## Remaining work

| Package | Current state | Remaining acceptance work |
| --- | --- | --- |
| CU-01: mapping and coverage | Implemented, model reviewed | Qualified linguistic review of the crosswalk. |
| CU-02: contracts | Implemented | Reuse and evaluate the contracts in additional activity adapters. |
| CU-03: release identity | Implemented for retained releases | Validate each future release before publication. |
| CU-04: morphology | Forward import and constrained selection implemented | Reviewed backfill of older incomplete tags. |
| CU-05: first teaching sequence | Teaching, choices, typed forms, listening, Writing and mapped Speaking implemented | Learner and linguistic validation across the sequence. |
| CU-08: Writing | Diagnostic integration implemented | Human comparison of judgement quality and level demands. |
| CU-09: Speaking | Narrow A1 directions diagnostic implemented | Broader scenario mapping and real acoustic/linguistic validation. |
| CU-06, CU-07 | Not complete | Comprehension and Translation/Word Jumble criterion adapters; typed unit practice is only the first production case. |
| CU-10 onward | Planned | Full authored A1 coverage, five-domain pilot, validated gates, then later levels. |

The next pass should add criterion-level evidence to generated Comprehension, then validate the complete teaching sequence before expanding it. A full A1–B2 reference catalogue is already present; a complete, validated A1–B2 course is not.
