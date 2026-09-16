# Lessons: audit and proposed direction

Reviewed 11 September 2026. This records the system before migration and the proposed direction. The review itself changed no application code, source lesson files, credentials or learner records. The subsequent first implementation is documented in [Lessons companion](lessons-companion.md); read that document for the current behavior and remaining work.

## Purpose

Lessons should connect work with a tutor to independent practice before and after the session. A learner should be able to bring an annotated document, continue where they stopped, understand what to practise next, and use the existing activities with that lesson's material.

The main product change is continuity. Generating more unrelated questions would not solve the current problem.

## What exists today

The implementation is Flask/Jinja/HTMX: `services/lesson_service.py`, the lesson handlers in `app.py`, `templates/lessons.html` and `templates/_lesson_content.html`. The current templates own the flow; the separate `static/js/Lesson.js` component is not referenced by this flow.

1. Enter a title and optional description, then upload a PDF and/or images.
2. Save one `lessons` row containing file paths, metadata and JSON arrays of questions and responses. The file bytes live on disk, not in SQLite.
3. Generate a chosen number of open-ended Russian writing questions, normally five.
4. Answer individual questions. The model returns a score out of 100 and 100-150 words of English feedback.
5. Return through the saved-lessons list to see the questions and submitted answers.

The running preview contains five saved lessons, 15 stored question objects across two lessons, and one saved response. It shares navigation and styling with the other activities, but the lesson service does not connect questions or results to vocabulary/forms, native review, learner evidence, Lingocoins or a completion state.

The effective preview settings remain `OPENAI_MODEL_VISION=gpt-5.2` for generation and `OPENAI_MODEL_HIGH=gpt-5.2` for marking, both with low reasoning. Lessons constructs its own OpenAI client. The newer story and flashcard settings do not apply to it. This review did not change any model settings.

## Findings that need attention

| Finding | Evidence and effect | Priority |
| --- | --- | --- |
| The PDF reader misses the supplied lesson | Running the actual `extract_pdf_text` method against the 20-page Siberia PDF returns only 213 characters: the first-page objectives and three audio labels. The substantive pages are image-based; handwriting is held in ink annotations. Neither is supplied as PDF page images to the current model call. | First |
| Extraction destroys structure and can conceal failure | `sanitize_text` removes newlines and some quotation marks, then caps PDF text at 10,000 characters. Extraction exceptions become an `Error: ...` string that generation can treat as lesson material. Only the first two separately uploaded images are used. | First |
| Saved file links are broken in this preview | All five generated attachment URLs return 404. All five original files still exist under the legacy upload directory. Relative paths are routed to the preview upload root; the absolute-path row also produces a malformed static URL. This is a reference/serving problem, not evidence of deleted files. | First |
| An older question format is incompatible | One saved lesson has ten `{question, answer}` objects, but the template/service expect `{id, prompt}`. Its rendered page repeats empty `answer-`/`response-` IDs; it cannot submit these as normal identified tasks. Preserve these older objects during conversion, including their reference answers. | First |
| Marking lacks the source | The marker receives the question, submitted answer, title and description. It does not receive the relevant PDF passage, images, an answer rubric or previous attempts. It therefore cannot reliably assess factual comprehension or progress. | First |
| Generated grammatical instruction can be wrong | A saved task asks for prepositional-case time expressions and gives `утром`, `днём` as examples. These are not prepositional-case examples; their adverbial use relates to instrumental forms. A task needs linguistic validation before its answer is graded. [Linguistic analysis](https://journals.rcsi.science/1605-7880/article/view/267055). | First |
| Repeated generation has no stable task identity | Model-provided IDs are appended without uniqueness or schema validation. Reused IDs could attach feedback to the wrong question. Existing JSON arrays are updated by read/append/write, which is also vulnerable to concurrent lost updates. | Foundation |
| Feedback handling is inconsistent | Marking interpolates provider text into HTML directly; errors also use raw interpolation. English feedback is hard-coded regardless of UI language. There is no draft autosave or clear next task. | Foundation |
| Backup coverage is incomplete for Lessons | The current learning backup includes the SQLite rows but explicitly excludes legacy uploads. A database restore alone cannot restore these source documents. | Foundation |

The page leads with upload paths and generation controls, followed by a long list of answer boxes. A one-option task-type selector adds no useful choice. Saved lessons show raw timestamps, and loading a lesson through HTMX does not update the URL. Existing tests cover route rendering and feedback targets, not real PDF extraction, historical question conversion or marking quality.

## What the supplied lesson actually offers

All 20 pages were visually reviewed, including the handwritten annotations. This is a qualitative content assessment, not a grade of the learner's proficiency. Rendered annotations are visible, although Poppler emitted stream warnings; a production importer must check rendered coverage rather than treat a successful process exit as proof of complete extraction.

| Pages | Material | Useful learning objective |
| --- | --- | --- |
| 1-5 | Objectives, travel conversation and introductory cultural material | Understand the topic and discuss what is new or what someone plans to do. |
| 6-8 | Plural prepositional nouns, adjectives and pronouns; transformations and personal sentences | Produce an entire agreeing phrase, and distinguish location from the topic of a conversation. |
| 9-13 | Readings on Evenki and Buryats, illustrations, vocabulary notes and comprehension questions | Explain relationships in the reading, using relevant vocabulary in complete phrases. |
| 14-17 | `свой` contrasted with other possessives; changes of subject and referent | Identify whose person/object is meant, then select and inflect the possessive appropriately. |
| 18-20 | Yakutia reading, vocabulary and closing questions | Summarise the reading and answer a new question without copying the passage. |

The handwritten work includes translations, endings, arrows linking pronouns to subjects, crosses and homework-like marks. These are valuable observations. They are not automatically evidence of an independently correct answer, an error, authorship or completion. A cross in a substitution task can mean that substitution is disallowed; it need not mean the learner was wrong. A blank can mean unattempted, discussed orally or answered elsewhere.

For example, page 16 makes a distinction that cannot be captured by translating `свой` as a single English word: the speaker's car remains the speaker's when Sasha becomes the subject. Replacing the possessive mechanically changes the owner. The page also changes subjects inside a family narrative and direct speech. Good follow-up work must test reference and meaning as well as endings.

The source refers to audio 9, 10 and 11, but this PDF has no embedded file attachments and its annotation inventory has no audio/link objects. The pictured players are not available recordings. If original tracks are supplied, attach them; otherwise offer clearly labelled generated readings of extracted text. Do not invent the contents of an unavailable recording or grade listening comprehension against it.

Cultural statements should be presented as claims in the reading. Any new factual enrichment, especially current statistics or generalisations about peoples, needs its own sourcing rather than being silently copied into an authoritative answer key.

## A proposed learner experience

The library opens with **Continue lesson**, a human title, last activity and a short next step. **Add lesson** and **Upload updated notes** are ordinary user actions. The document remains available throughout. Generation settings and files sit under Materials/Options; they are not the main learning screen. This does not require a new adult/child split or approval gate.

| Stage | Example for this lesson |
| --- | --- |
| Prepare | A brief introduction to the subject, a few useful words selected against actual review history, and a quick reminder of singular prepositional forms. Let the learner skip material they know. |
| Read / work with tutor | Original pages beside optional explanations, help with a phrase, and an explicit bookmark such as “We reached page 13.” On mobile, switch between the page and the exercise. |
| Practise | A short, varied set built around two or three objectives: phrase transformations, contextual possessive choices, reading questions and one personal response. |
| Check understanding | A short mixed recap using fresh examples: two form tasks, two reference/meaning tasks, one comprehension question and a short written or spoken response. This is a proposed design, not a validated exam. |
| Review later | Offer selected contextual clozes and a short return to objectives that remain difficult. Keep existing card schedules intact. |

Illustrative new exercises, not transcriptions of handwritten answers:

- Supply the plural phrase in a complete context: “Мы говорили о ___.” Given `мой новый друг`, the intended phrase is `моих новых друзьях`.
- Establish the owner explicitly: “У Анны есть машина. Анна едет на ___ машине.” Then change the subject to Boris and ask for the form that still means Anna's car. Discuss why the reference changes.
- Ask why the reading describes people moving with their animals, rather than only asking the learner to list names.
- Ask for a short comparison with the learner's own life, using a target phrase naturally.

Feedback should identify the specific form or meaning at issue, give a short explanation and allow a retry. Keep comprehension, grammar and assistance separate. Accept valid alternative answers; a grammatical sentence that changes the intended owner is a different issue from an incorrect ending. Evidence from one exercise should update that objective cautiously, not label a whole case system “mastered”.

## Remembering the lesson across uploads

Keep SQLite and the existing vocabulary model. Add lesson structure alongside the old table, then adapt old records without removing their history.

| Record | Purpose |
| --- | --- |
| Lesson | Stable identity, title and optional tutor/course context. |
| Source revision | Original file reference, content hash, parent revision and upload time. Original bytes remain intact. |
| Page/section extraction | Source page and region, printed material, annotations, uncertainty and extraction version. |
| Objective and task version | What is practised, exact source evidence, question, acceptable answers/rubric and model/prompt version. |
| Attempt and progress | Learner's original response, separate corrections, assistance, outcome, bookmark and timestamps. Existing profile identity can be reused. |
| Vocabulary occurrence | Actual surface phrase in its sentence, optional `word_id`/`form_id`, contextual interpretation and source location. |

These are conceptual records, not a mandate for one table per bullet. Stable identities, attempts and joins benefit from relational constraints; a validated extraction document can remain versioned JSON initially.

- An identical file hash reopens the existing revision instead of duplicating it.
- An updated file attached to the lesson becomes a new revision. Keep earlier answers and task versions.
- For an independent upload, suggest a match using content and page structure. A title/filename alone cannot safely identify the lesson; ask which lesson to update when ambiguous.
- Compare both base page content and annotation layers. Match page content/regions as well as page numbers, since pages may be inserted or reordered.
- Show the detected changes and propose follow-up practice. Do not infer mastery from changed handwriting, a checkmark or upload time.
- Store source assets under portable identifiers and include them in the existing checksum-based backup. Local files now, object storage later; SQLite stores references and learning records.

## Integration with the existing application

The database already has useful overlap with this PDF, including `народ`, `свой`, `друг`, `современный`, `страна`, `язык`, `жить` and `кожа`. These are exact spot-checked matches, not a complete vocabulary coverage estimate. A lemma's presence in the library does not establish the learner's knowledge of it or any particular form.

- **Vocabulary:** link occurrences to the existing lemma/form structure. Preserve the sentence and contextual English explanation at the occurrence/task/card level. No compulsory English translation column on `words` is needed. The database's `свой` rows also demonstrate why matching must allow uncertainty: some form tags omit case. Do not assign a case from spelling alone or silently rewrite the word tables during lesson import.
- **Flashcards:** offer a small generated set of contextual clozes from the lesson, with exact target forms, full sentence translations, optional mnemonic hints, pictures and word/sentence audio. Reuse native review and its Again/Hard/Good/Easy scheduler. Extend the generator to accept lesson passages and provenance; its current vocabulary-selection entry point does not already do this. Do not add every encountered word or reset existing schedules. Anki export remains optional.
- **Reading and writing:** pass a selected passage/objective into the existing activity services and retain a link back to the lesson. Avoid independent copies that lose their source and attempt history.
- **Conversation:** build a scenario based on the reading, or a short oral retelling. The current conversation scenarios need an adapter for lesson context. Keep original speech, uncertain transcription and proposed grammatical corrections distinct; the live conversation activity does not yet provide verified speech-based grading.
- **Progress and coins:** use the existing learner identity and reward ledger, with a lesson completion adapter. The current generic reward helper is tied to activity attempts and daily content rewards; a lesson policy needs its own explicit completion eligibility. Reward completing a bounded session and working through feedback, with a stable eligibility key that survives document reuploads. Do not award coins for uploading or regenerating tasks, and do not equate an AI percentage with calibrated Elo.

## AI processing and quality

OpenAI's current file-input interface can supply both PDF text and page images to a vision-capable model. That addresses the principal limitation here. For this annotated file, explicitly rendered page images provide a way to verify that ink and handwriting reached the analysis stage. [Official OpenAI file-input documentation](https://developers.openai.com/api/docs/guides/file-inputs).

Use separate steps: extract source evidence; derive objectives; generate exercises; validate their grammatical and contextual correctness; assess attempts against the appropriate passage and rubric. Cache the source analysis and reprocess changed pages/regions, not the entire PDF after each answer. Persist jobs with progress and retry support so processing does not depend on one long browser request. Files are lesson data, not instructions that can override application rules.

Use schema-constrained results with application-assigned identifiers and explicit unknown/illegible fields. Schema validation ensures a usable format, not truth or correct Russian. [Official OpenAI structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs).

Choose a dedicated lesson model setting when implementing, and evaluate candidates on this annotated PDF and known grammatical test cases. A model change alone will not fix missing source content or bad task design. Do not silently change the application's other model settings.

## Suggested migration order

1. **Repair the current module.** Resolve portable upload references; recover the older question format with stable IDs; escape feedback; reject failed/empty extraction; add realistic regression fixtures and upload-inclusive backups.
2. **Build one complete lesson workflow.** Use this PDF as a private acceptance fixture: annotated page ingestion, stable lesson/revisions, a bookmark, three clear objectives, a short practice set and source-grounded feedback. Add the return-upload flow at this stage, not after creating more content.
3. **Connect recap and review.** Add the mixed final check, persistent attempts, optional lesson clozes with full media, and one-time completion rewards. Reuse the existing services while extending their input contracts explicitly.
4. **Add richer preparation and speaking.** Personalised pre-reading, original/generated audio, lesson conversation scenarios, cumulative review and tutor summaries.

Acceptance checks include: complete source-page coverage; visible handwriting retained; uncertainty not converted to learner mistakes; identical reuploads deduplicated; revised/reordered pages retaining stable progress; old attempts unchanged by regeneration; valid Russian alternatives accepted; wrong pronoun reference distinguished from inflection error; existing card schedules preserved; duplicate completion requests issuing one reward; and backup/restore reopening both source files and attempts.

Useful later additions include a short brief for the next tutor session, a personal index of recurring mistakes with evidence, a searchable notebook of explanations, questions to ask the tutor, offline preparation packs, dictation from verified text, and cumulative checks spanning several lessons. Any tutor brief should be previewed or exported by the user; the module need not send messages or create a separate tutor account.
