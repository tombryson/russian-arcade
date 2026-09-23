# Curriculum implementation status

This guide records the [curriculum uplift plan](curriculum-uplift-plan.md) implementation on `codex/curriculum-assessment-pilot`, updated 24 September 2026. It adds teaching and diagnostic evidence. It does not replace the published A1 journey or introduce a new level gate.

**Verification status:** focused checks pass for the new units, recording preparation, pilot lifecycle and import integrity. A fresh browser check passed native audio playback, replay, slower playback, answer submission and transcript support. Generated Comprehension also passed playback and saved-answer checks using a local test fixture. These checks verify operation, not pronunciation quality or marking accuracy. Full integration results are recorded in the change's pull request. No qualified human language review or learner trial is claimed.

The frontend suite passed 725 tests, followed by a successful typecheck and production build. A migration rehearsal on a private copy of the hosted database reached schema 54 with all existing rows unchanged across 99 tables, no foreign-key errors and a clean integrity check. Hosted SQLite backups and a volume snapshot were requested before deployment.

Two bounded live Writing checks used the existing configured model without changing it. A correct reply scored 10/10; a reply with four deliberate case/conjugation errors scored 7/10 and received the four corrections. Both retained credit for communicating the requested invitation. The two calls cost US$0.008856 in the isolated test ledger. This verifies those examples and report validation, not general marking reliability. Feedback specificity still needs improvement: a corrected example was useful, but its next-step sentence was generic.

The application is standalone. It marks selected responses and uses AI for written and spoken feedback. External language review is optional maintenance work on our content and rubrics; learners do not need a tutor, reviewer approval or an appointment.

## Available teaching units

Curriculum links to seven A1 units. Each has classified examples, contextual questions, typed-form practice and its own Writing task.

| Unit route | Focus | Choices / typed forms / listening items |
| --- | --- | --- |
| `/curriculum/units/location-destination-v1` | Where someone is, where they are going, and movement within a place | 4 / 3 / 3 |
| `/curriculum/units/possession-absence-v1` | Who has an item, who owns it and what is missing | 6 / 4 / 3 |
| `/curriculum/units/objects-recipients-v1` | A direct object, an animate object and a recipient | 6 / 4 / 0 |
| `/curriculum/units/time-routine-v1` | Days, times, conjugation and tense in daily routines | 6 / 5 / 0 |
| `/curriculum/units/noun-adjective-agreement-v1` | Gender, number and adjective agreement | 6 / 4 / 0 |
| `/curriculum/units/personal-reference-v1` | Personal pronouns and the people they refer to | 6 / 4 / 0 |
| `/curriculum/units/basic-motion-v1` | Walking or travelling by vehicle; one journey or a routine | 6 / 4 / 0 |

This pass adds 18 contextual questions and 12 typed prompts across the last three units. Each includes short reading tasks. Their examples teach specific contrasts; they are not comprehensive case tables or a complete A1 course. The four previously published unit files and issued contracts remain unchanged.

Six new listening packs contain 18 authored messages. Four new recordings were prepared before the existing ElevenLabs character allowance ran out. The possession pack is complete and available. The partially prepared objects pack and remaining packs stay hidden until all their recordings are verified. Two separate assessment recordings are also pending: 16 clips in total remain, requiring about 2,240 characters. The credentials work; the provider allowance needs renewal. No automatic paid retry runs.

Practice uses the existing activity player and saved-session store. It resumes unfinished work, saves hints with each answer and returns to the unit when finished. Completion uses the existing activity reward policy. There is no separate curriculum coin balance or schedule.

Typed-form practice uses a separately versioned pack. It accepts authored variants, including a noun alone or its full prepositional phrase where appropriate. Letter case, spacing, final punctuation and ё/е are normalised for comparison. The exact submitted text is retained. No model guesses whether an unrelated answer should count.

Available listening practice uses six bundled Russian messages. Learners hear the recording before choosing an answer. The transcript stays hidden until requested or after the answer is checked. Hints and transcript use are saved separately. A browser playback receipt enables answering, but is not proof of attention or unaided understanding. Replaying the same recording does not remove earlier support.

Recordings are prepared once through the existing speech provider and configured random voice pool. Playback makes no AI call. A failed audio load offers replay or transcript support; a failed receipt save can be retried without replaying. Text hashes, audio hashes and durations bind each recording to its published question. Missing or changed recordings cannot be silently replaced.

Each Writing task opens in the existing Writing workspace and resumes its own saved draft. Its criterion matches that unit's communicative task. AI feedback can explain grammar separately from communicative success. Suggested words do not restrict the learner to one exact answer. A return link leads back to the unit.

The location unit links to the existing directions scenario. Possession links to shopping, and routines to meeting people. These links do not pass unit-specific criteria into Speaking. Objects and recipients has no Speaking link because no existing scenario reliably elicits that task. New Fluent A1 directions sessions save one narrow criterion: asking where the required place is. Their review uses the original learner audio. A clear short question can satisfy that task even when there is too little speech for overall grammar or fluency scores. Support independence remains unverified; this is not a proficiency result. Older conversations and unmapped scenarios retain their current review path.

The public sample demo supports choice, typed-form and listening practice without an AI call. Original Writing is available in individual local profiles and hosted accounts. Optional household mode retains its existing separate Writing workspace, so these units do not offer child-owned Writing tasks there. Fluent Speaking retains its existing microphone, provider and spending requirements.

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

The adapters cover authored unit choices, controlled text and listening; generated Comprehension, Translation and Writing; selected Word Jumble demands; and the mapped Fluent Speaking situations. New A1–B2 Writing generation requests one or two explicit writing objectives and freezes their wording in the task. Older tasks retain their original feedback path. See [Comprehension evidence](curriculum-comprehension-evidence.md), [Writing evidence](curriculum-writing-evidence.md) and [Speaking evidence](curriculum-speaking-evidence.md) for their validation and failure behaviour.

## Generated Comprehension

New A1–B2 tasks offer reading or listening practice. Both retain the open-answer workflow. Four source-based questions carry narrow criteria; the personal-reflection question receives ordinary feedback without a reading or listening claim. These application response modes remain distinct from the source exam's selection format.

Listening hides the transcript, word payload, revealing title and image until the learner requests the text. Its questions bind the original recording's hash and byte size. Owned playback verifies those bytes. Answer checking requires a playback receipt or an explicit transcript disclosure. A pasted source starts with transcript support already recorded.

New reading and listening tasks record word-translation and hint exposure. Listening also records playback and transcript exposure. A receipt is saved before returning the supported content. Each answer check retains the exact receipt IDs available then. Additional question versions inherit earlier support; they cannot restore a claim of unaided work. Old task payloads and reports keep their original policy.

If generation produces no recording, the saved task offers a transcript fallback. It can give ordinary comprehension feedback, but listening criteria must remain `insufficient_evidence`. If an existing recording changes or disappears, playback is blocked and the transcript route remains explicitly supported. A browser receipt is not proof of attention or an exam condition.

Question versions and answer history remain saved. Duplicate checks reuse feedback, and additional questions cannot overwrite earlier evidence. These controls prevent known disclosure paths from being ignored; they do not establish human-validated listening accuracy or independent proficiency.

## Translation and Word Jumble

New A1–B2 Translation generation selects one language-use requirement and cites exact excerpts from the English source and Russian reference. The task and focus are frozen before an answer. The reference remains one possible translation, not the required wording. Marking instructions accept natural alternatives; a correct answer that does not demonstrate the chosen feature should leave that criterion unscored, rather than fail the answer.

Word Jumble maps only an explicit visible demand. Its A2 instruction can provide a narrow time/reason observation; B1 can provide cause/consequence; B2 can provide conditional comparison. These may refer to an earlier-level requirement. The unrestricted A1 task and older unscoped games do not acquire a grammar criterion merely because the learner used Russian words.

Both adapters retain tutor feedback and exact submitted text. The criterion report is an additional observation, not a new overall score or proficiency claim. Prior feedback is saved as model-answer support. Translation also records when Phrasebook exposes the reference, preserving whether this happened before or after earlier attempts. Failed criterion validation rolls back the new check and its rewards. Legacy duplicates keep their existing contracts or lack of contract; new criteria are not attached retrospectively.

These reports are diagnostic. They do not award a TORFL level, change a course pass or convert Elo into proficiency. Exact evidence validates attribution; it does not by itself prove that an AI judgement is linguistically correct.

## Five-domain assessment pilot

Curriculum and Profile link to `#assessment`. The pilot samples language use, reading, listening, writing and speaking. Each domain has two authored forms. A form contains six language-use questions, three reading questions, three listening questions, one written message and one recorded personal introduction. This small sample is not a complete A1 examination.

Learners can save and resume each component. Selected answers are marked automatically. Writing and Speaking use the existing AI services and spending controls. Each domain shows its own result and feedback; no aggregate pass threshold, coins, Elo or course unlock is added. The spoken introduction tests personal information and intelligibility. It does not claim to test interaction with another speaker.

The server freezes the questions, criteria, source text and recording identity before answering. Hints, transcript access and playback are recorded separately. Original written responses and microphone uploads are retained. Spoken feedback uses an untrimmed audio copy, preserving pauses. A model transcript is an interpretation of that audio, not a replacement for it.

Feedback failure preserves the response and offers an explicit retry. Duplicate requests reuse the saved submission. An older browser tab cannot submit against a replacement form. A review interrupted by a process crash becomes retryable after its lease expires. Opening or refreshing a page does not call a paid model.

Retakes select only the requested components and keep earlier attempts. The alternate form is used where available; repeated material remains labelled as repeated. The forms are authored alternatives, not psychometrically equated exams.

New sessions remain unavailable until both authored listening recordings have been prepared and verified. Existing sessions remain readable. This media-readiness check is unrelated to external review. Local profiles and signed-in accounts can use the pilot; the shared sample demo does not start production assessments.

## Storage and migration

Migration `048` adds explicit release, target-catalogue and content identities to focused course practice. Historical attempts continue using their saved identities. Old submission receipts remain replayable.

Migration `049` adds two tables:

| Table | Purpose |
| --- | --- |
| `activity_task_contracts` | Frozen criteria for an owned, existing task. |
| `activity_criterion_reports` | Immutable criterion judgements for its saved attempts, with support and response hashes. |

Migration `050` adds `learning_item_support`, keyed by session and question. It records playback, transcript and hint receipts for listening items. The existing activity attempt stores the answer. Its criterion report must agree with those receipts and the frozen audio identity. Previous choice and typed-form packs, contracts and cached responses remain unchanged.

Migration `051` adds `comprehension_tasks` and `comprehension_attempts`. New stories are saved before answering; each question set and successful check is retained. Existing story rows and media are untouched by the migration. Account import validates the new history and clears only temporary in-flight check leases in its output artifact.

Migration `052` adds `comprehension_support_receipts` and the receipt IDs captured by each attempt. It preserves transcript, translation, hint and playback disclosures, including their inheritance by later question sets. Listening payloads contain the recording identity; a copied database alone does not copy its media files.

Migration `053` adds criterion report and support fields to Translation and Word Jumble attempts. `translation_reference_views` records when a scoped translation's reference was shown in Phrasebook. Shared evidence validation checks those records against the owned original task and answer. Legacy attempts retain null fields.

Migration `054` adds six tables for the diagnostic pilot: `assessment_pilot_sessions`, `assessment_pilot_components`, `assessment_pilot_support`, `assessment_pilot_submissions`, `assessment_pilot_reviews` and `assessment_pilot_requests`. They retain frozen forms, drafts, support, original responses, review state and duplicate-request receipts. The account importer verifies this history and its private recordings before copying it. Full provider feedback and model/prompt/rubric provenance remain attached to the saved review.

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

## Review and evaluation

[Curriculum validation](curriculum-validation.md) documents the optional maintenance review workflow. `scripts/prepare_curriculum_review.py` exports versioned material with provisional answer keys separate from blank review fields. The expanded packet covers seven units and 120 authored cases; the earlier packet remains reproducible. Pilot material is exported separately so reviewers can inspect both assessment forms.

The packet includes recoverable case and conjugation mistakes, partial communication, valid alternatives, empty evaluator input and model-answer support. Review ingestion records content fingerprints and distinguishes human review from internal model review. One completed review can be recorded; comparing two raters and resolving disagreements are separate operations. No completed human ratings, real learner recordings or measurements of model-marking accuracy are claimed. These tools are for improving the product and do not require learners to use a tutor.

## Remaining work

| Package | Current state | Remaining acceptance work |
| --- | --- | --- |
| CU-01: mapping and coverage | Versioned reference map and generated inventory | Qualified review of the crosswalk and source interpretation. |
| CU-02: contracts | Shared validation and owned task/report storage across more adapters | Judgement-quality evaluation and remaining activity integrations. |
| CU-03: release identity | Routing and preservation for retained releases | Rehearse each future release and its new component types. |
| CU-04: morphology | Forward import and constrained selection | Reviewed backfill of older incomplete tags. |
| CU-05: teaching sequences | Seven A1 units; location and possession include prepared listening | Finish pending recordings; extend transfer tasks and evaluate teaching quality. |
| CU-06: Comprehension | Generated reading/listening contracts, disclosure receipts and successful browser playback | Audio quality, question validity and marking evaluation. |
| CU-07: controlled production | Typed units plus narrow Translation/Word Jumble reports | Validate natural alternatives and whether each generated focus is actually elicited. |
| CU-08: Writing | Diagnostic integration | Human comparison of judgement quality and level demands. |
| CU-09: Speaking | Narrow A1 directions diagnostic | Broader scenario mapping and real acoustic/linguistic validation. |
| CU-10: A1 coverage | Seven units and an explicit gap inventory | Remaining teaching, lexical planning and balanced task coverage. |
| CU-11–14: assessment and release | Resumable five-domain diagnostic pilot, original-response storage and component retakes | Two pilot recordings, production quality evaluation, learner trials and a justified policy before any new proficiency gate. |
| CU-15–17: A2–B2 courses | References and ordinary practice exist | Full reviewed teaching, assessment, regions and retry routes for each level. |

Next, finish the recordings when provider allowance is available, evaluate the pilot with real consenting learners, and expand the remaining A1 teaching from the gap inventory. Internal review has already corrected an ambiguous food answer, an unsuitable reading criterion and a speaking task that claimed interaction without a conversation. External review can improve confidence in the content; it is not a prerequisite for standalone use. A full A1–B2 reference catalogue is present; a complete, validated A1–B2 course is not.
