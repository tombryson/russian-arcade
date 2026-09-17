# Activity and game audit

**Date:** 16 September 2026\
**Source reviewed:** private application repository, commit `d386008c`; corresponding public release `7ec50ade`.\
**Scope:** eight journey games, First steps, flashcards, reading, Word Jumble, translation, writing, Speaking and tutor lessons.

Anki generation is an accessory rather than a game. The old recorded-conversation flow and speech lab are retained under Speaking for history and diagnostics, so they are not scored as separate current activities. Journey destinations and the planned final letter are considered integration work, not additional completed games.

## Overall assessment

The application has a strong foundation for Russian practice. Speaking, Word Jumble, contextual flashcards, reading and tutor lessons have clear educational purposes. The connection between a lesson occurrence, its lemma, its grammatical form and later practice is particularly valuable.

The arcade games are less developed. Several change the visual presentation while asking essentially the same question: match a sentence to its meaning. They generally work as short exercises, but few offer enough decisions, variation or progression to sustain play. The postal theme does not always explain what the player is doing.

The next work should improve assessment validity, grammatical variety and the quality of each activity. Adding more game names would increase the maintenance burden before resolving these weaknesses.

## Method and limits

- Read the active generators, player components, persistence services, prompts, progression rules and supporting tests. Historical planning documents were treated as background, not proof of implementation.
- Inspected the public activity catalogue. Used a separate temporary database and test providers for local browser checks. Prepared seven game sessions; examined Directions, Detective and Missing Stamp in the browser, including an incorrect-answer flow and a narrow viewport.
- The browser fixtures used placeholder media. They establish layout and interaction behaviour, not the quality of generated pictures or speech.
- Ran **286 backend tests**, covering the journey games, Radio, Speaking, written activities, lessons, onboarding, skill progress and native flashcards. All passed. Ran the UI suite: **323 tests in 32 files**, all passed.
- Ran small offline probes of repeated game content and the rating formula. No paid generation or live speaking calls were made. Personal learning records and credentials were not changed.
- An initial test invocation included a nonexistent module name. The corrected run above completed cleanly; this was an audit command error, not an application failure.

Enjoyment and engagement scores are design judgements. They are not measurements from learner testing. This audit does not establish current provider latency, speech naturalness, image accuracy or long-term learning gains.

## Scores

**Correction, 16 September 2026:** the Directions scores have been withdrawn. Inspecting the learner's saved five-round session confirmed that the activity tests only three commands in sequences of one, two and three moves, then repeats. The earlier scores gave too much credit to a possible future game. The current standalone activity does not justify them. Passing persistence and interface tests does not establish worthwhile learning content.

Scores run from 1 to 10. Around 5 means useful but limited; 7 means solid; 9 means unusually strong. Originality concerns the learning interaction, rather than its illustrated theme. A familiar mechanic can still be excellent practice. Learning potential describes what the existing approach can support; it does not claim that every generated example meets that standard.

Enjoyment concerns the immediate experience. Engagement concerns reasons to return and sustain attention. Implementation covers the current code, interaction, failure handling and integration. AI-dependent activities have greater uncertainty because live provider quality was not retested.

| Activity | Originality | Enjoyment | Learning potential | Engagement | Implementation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Speaking | 7 | 8 | 9 | 8 | 7 |
| Word Jumble | 5 | 8 | 9 | 8 | 8 |
| Native flashcards | 3 | 6 | 9 | 8 | 7 |
| Read a story | 4 | 7 | 9 | 7 | 6 |
| Translate a sentence | 2 | 6 | 8 | 6 | 7 |
| Writing | 3 | 6 | 9 | 6 | 7 |
| Tutor lessons | 8 | 6 | 9 | 7 | 7 |
| First steps | 5 | 7 | 7 | 6 | 7 |
| Post Office Radio | 7 | 7 | 9 | 7 | 7 |
| A Letter Back | 5 | 6 | 8 | 6 | 7 |
| Follow the directions | — | — | — | — | — |
| Missing Stamp | 3 | 5 | 7 | 5 | 6 |
| Postcard Pairs | 3 | 5 | 6 | 4 | 7 |
| Pack the bag | 4 | 5 | 5 | 4 | 7 |
| Mailbox Sort | 3 | 4 | 6 | 4 | 7 |
| Lost Parcel Detective | 5 | 4 | 5 | 4 | 6 |

## Highest-priority findings

### 1. Multiple-choice results can overstate skill progress

**Priority: high. Confirmed in the rating code and an offline calculation.**

The rating formula is `R += 24 × (score − expected)`. Expected performance follows an Elo curve. Journey games derive task difficulty largely from vocabulary difficulty, without modelling the chance of selecting a correct answer.

For a learner at 1000:

| Task rating | Expected score used by the application | Expected rating change from random four-choice guessing |
| --- | ---: | ---: |
| 1000 | 50.0% | −6.0 |
| 1200 | 24.0% | +0.2 |
| 1400 | 9.1% | +3.8 |
| 1600 | 3.1% | +5.3 |

These are mathematical expectations, not observed learner behaviour. They show that selecting harder vocabulary can produce positive expected progress without comprehension.

There is another source of inflated evidence. Games repeat their small content pool within a session. Earlier feedback may already have shown the answers used in later rounds. The current evidence filter excludes explicit hints and transcripts, but does not exclude content revealed by earlier rounds.

**Recommendation:** retain completion rewards. For skill estimates, account for the response format and chance performance, and distinguish first encounters from supported repetition. Establish a small set of reviewed benchmark tasks before tuning the rating scale. Repeating material is valuable practice; it should not repeatedly count as independent assessment.

**Acceptance:** chance-level performance should not produce positive expected skill growth. Feedback-assisted repeats should not be counted as fresh evidence. Hints should remain available without losing participation rewards.

Evidence: [skill progress](../../flask_vocab_app/services/skill_progress.py), especially `freeze_evidence` and `snapshot`; [game rounds](../../flask_vocab_app/services/journey_vocabulary_games.py).

### 2. Native generation underuses the Russian form model

**Priority: high. Confirmed selection behaviour.**

The vocabulary database can represent declined and conjugated forms. However, native batch selection orders forms by whether they equal the lemma, then takes the first row. Without a case filter, this favours the dictionary form. Words are also selected in ID order rather than by a coverage or learning objective.

The journey-game vocabulary adapter is better here: it considers stored forms, avoids recently used material and can preserve exact lesson occurrences. These two selection policies do not offer consistent practice.

**Recommendation:** keep the existing lemma/form relationships and contextual translations. Select native cards across useful forms, guided by an explicit objective and prior coverage. Preserve the source form for lesson selections. Add selection controls only where they serve a real study choice, such as practising a case or a tense.

**Acceptance:** a normal batch should not default repeatedly to dictionary forms. Records should retain the precise form and grammatical reading used in each example. Homographs and equivalent spellings must not be collapsed into a single assumed meaning or case.

Evidence: [native selection](../../flask_vocab_app/services/card_generation.py), `select`; [game vocabulary selection](../../flask_vocab_app/services/journey_vocabulary.py), `select_examples`.

### 3. Wrong answers end the attempt without corrective practice

**Priority: high for learning design. Confirmed in browser and shared player code.**

The game saves the first answer, shows the solution, and enables Next round. It does not let the learner repair that answer in the same round. In Directions, even Undo and Start over become disabled after checking. “Let’s take another look” therefore means looking at an explanation, not doing the task again.

Keeping the first answer immutable is a good assessment decision. It does not require making the practice interaction immutable.

**Recommendation:** save the first result for evidence, then allow a short correction attempt. Offer a focused review of missed items at the end. Do not add rating evidence or extra coins for these supported repeats.

Evidence: [game player](../../flask_vocab_app/ui/src/JourneyGames.tsx), `interactionBlocked` and feedback rendering; [commands](../../flask_vocab_app/services/journey_games.py), `session_command`.

### 4. The public demo advertises games it cannot start

**Priority: high for the published visitor experience. Confirmed by catalogue and endpoint policy.**

The public catalogue displays eight games and their unlock instructions. First steps can introduce those games. However, the public endpoint allowlist permits the game catalogue but excludes starting and reading game sessions. This also excludes Directions, which needs no generated pictures or text.

This is an intentional restriction at the server, but the catalogue and completion screens do not consistently reflect it. A successful introductory lesson can lead to a blocked activity.

**Recommendation:** make availability explicit before the learner invests time. Offer a prepared, playable sample for selected games, or clearly label the installation requirement. Enabling a sample game requires the same ownership and request-limit checks as the existing demo; do not open all generation endpoints.

Evidence: [public demo policy](../../flask_vocab_app/public_demo.py), `READ_ENDPOINTS` and `WRITE_ENDPOINTS`; [game catalogue](../../flask_vocab_app/ui/src/JourneyGames.tsx), `GameCard` and `GameUnlocks`.

## Journey games

### Post Office Radio

**Verdict: retain as a leading listening activity.**

The active standalone implementation now generates one coherent programme and four comprehension questions. It does not generate eight pictures. Questions and answers are in Russian, the programme remains available during the quiz, and revealing the transcript changes how listening evidence is treated.

The generator requests 110–140 words. Validation accepts 100–155 words and a spoken recording of 35–100 seconds. A short three-note station ident frames the recording. This is a plausible foundation for a radio exercise, although an ident alone does not establish natural broadcasting style.

Each question must cite an exact passage from the script. That helps trace the answer, but it does not prove that the chosen answer is entailed or that the other answers are unambiguously wrong. Those remain content-quality risks.

The player waits for the recording's end event before opening questions, unless the transcript is revealed. This could frustrate someone who has understood enough, and seeking to the end is not proof of listening. Completion of playback should not be treated as mastery.

**Improve:** prepare a small bank of reviewed programmes with genuinely different formats and topics. Include a main-idea question and distinct detail questions. Let learners review missed answers against the relevant part of the recording. Measure actual preparation time before changing the generation architecture. Keep pictures out of this activity.

New words can be saved. The direct game-to-flashcards action is currently withheld for Radio, leaving a weaker continuation than the other vocabulary games.

Evidence: [programme generation](../../flask_vocab_app/services/radio_broadcast.py), [player](../../flask_vocab_app/ui/src/RadioBroadcast.tsx), [Radio flow tests](../../flask_vocab_app/tests/test_radio_game_flows.py).

### A Letter Back

**Verdict: useful listening reconstruction; its title overstates the task.**

The learner hears a sentence and rebuilds the recorded wording using shuffled tiles. The full English translation supplies context. Identical tiles are treated as interchangeable, which avoids unfair scoring based on invisible identifiers.

This is not yet writing a reply to a letter. Sentences longer than five words are split into two-word chunks at fixed positions. Those chunks can expose much of the structure before the learner has understood it. Capitalisation and punctuation also reveal parts of the answer.

Exact order is appropriate when the instruction is to reproduce a recording. It would be inappropriate to apply that rule to an open Russian writing task, where other word orders can be valid.

**Improve:** use meaningful phrase boundaries. Gradually move from phrase tiles to word tiles, then optional dictation. Keep that progression separate from task scoring. Either explain the activity as rebuilding a received message, or add a genuine reply stage that accepts valid alternatives.

Evidence: [round construction](../../flask_vocab_app/services/journey_vocabulary_games.py), `letter-back`; [tile board](../../flask_vocab_app/ui/src/GameBoards.tsx), `LetterBackBoard`; [equivalence tests](../../flask_vocab_app/tests/test_journey_game_answer_equivalence.py).

### Follow the directions

**Corrected verdict: a three-command introductory drill, insufficient as a standalone game.**

Left and right are relative to Barsik's heading. The map shows the planned route and the correct route after feedback. It opens without AI generation, making it a useful inexpensive activity.

Standalone rounds currently use only left, right and straight. Route length cycles through one, two and three moves. Five or ten rounds do not introduce richer route language or a longer-term objective. The learner's inspected session used «Налево», «Прямо. Направо», «Налево. Направо. Направо», «Прямо» and «Прямо. Прямо». There is no named recipient, required destination or delivery outcome. The generator does not use the learner's vocabulary, despite the saved options saying `source: vocabulary`.

At the time of the original audit, the player omitted the builder's post-office and market illustrations. The quality pass fixed their rendering. They still have no role in the instructions or success condition. Making them visible did not fix the activity's central problem.

**Replace the standalone exercise:** build a small delivery task around a named recipient, a reachable destination and directions that refer to the actual map. For example: «От почты идите прямо до моста. Перед мостом поверните налево. Дом Анны — второй справа». The map must support that exact instruction. The learner follows the route and chooses the destination; feedback explains the first misunderstood instruction. A one-command example can remain an optional controls tutorial.

Acceptance requires playing a complete delivery: the language must determine the route and destination, a wrong interpretation must produce understandable feedback, and a second delivery must require a different linguistic decision. More rounds, longer random arrow sequences and decorative landmarks do not meet this requirement. Review the playable example before extending this design to other games.

The [Directions redesign specification](directions-game-redesign.md) provides the proposed replacement and its implementation requirements.

Evidence: [route builder](../../flask_vocab_app/services/journey_vocabulary_games.py), `build_routes`; [map player](../../flask_vocab_app/ui/src/JourneyGames.tsx), `MapBoard`.

### Missing Stamp

**Verdict: a useful cloze presentation that needs better distractors.**

The sentence and full English translation provide context. The missing form is not exposed through answer audio before checking. These are sound choices.

The alternatives usually come from other vocabulary entries. In the browser fixture, the exercise was:

> Я говорю с … .\
> I am talking to the teacher.\
> учителем / сестре / подарки / деревом

Recognising “teacher” is enough to choose the answer. The learner does not have to distinguish учитель, учителя and учителем. The existing form database is not being used to construct that grammatical contrast.

**Improve:** decide whether each item tests meaning or form. For form practice, draw plausible alternatives from the same lemma and require context that distinguishes the intended construction. Validate the entire phrase. Do not mark another grammatically and semantically acceptable form wrong simply because it differs from a stored answer. Add a brief explanation tied to the sentence after reveal.

Evidence: [cloze construction](../../flask_vocab_app/services/journey_vocabulary_games.py), `missing-stamp`; [cloze board](../../flask_vocab_app/ui/src/GameBoards.tsx), `ClozeBoard`.

### Postcard Pairs

**Verdict: retain as a short recognition exercise.**

Matching several sentences to pictures requires attention across the set. Learners can revise their matches before checking. The code gives partial credit and rejects identical saved picture assets or duplicate example text within a choice set.

With four prepared examples, rounds select groups of up to three. Repeated rounds quickly become remembering the same matches. New asset IDs do not prove that two generated pictures are visually distinguishable.

**Improve:** keep sessions short and use contrasting scenes: who did what, to whom, where or with what. Have a content review check that each picture supports its sentence and differs in the feature being tested. Reserve pictures for meanings they can communicate clearly. Use the learner's actual errors to choose a follow-up exercise.

Evidence: [choice construction](../../flask_vocab_app/services/journey_vocabulary_games.py), `_others` and `pairs`; [matching board](../../flask_vocab_app/ui/src/GameBoards.tsx), `PairsBoard`.

### Pack the bag

**Verdict: suitable for the introduction; weak as an unrestricted vocabulary game.**

The bag makes concrete nouns approachable. Selecting and removing objects gives an immediate visual response. Some rounds ask for two items, which adds a small memory demand.

The unrestricted version can ask the learner to pack a picture of a whole event, person or abstract concept. This is mechanically valid but weakens the explanation for the activity. “Packing picture cards” preserves the software template at the expense of the narrative.

**Improve:** choose material appropriate to a packing task. Ask learners to prepare for a journey, visit or weather condition, using requests that introduce quantity, possession or negation. Let other activities handle abstract vocabulary. Keep four visible choices; improve what those choices mean rather than adding more pictures.

Evidence: [packing rounds](../../flask_vocab_app/services/journey_vocabulary_games.py), `pack-bag`; [bag board](../../flask_vocab_app/ui/src/JourneyGames.tsx), `BagBoard`.

### Mailbox Sort

**Verdict: dependable matching practice with little identity of its own.**

It matches full Russian messages to contextual English meanings. This correctly avoids assigning a universal English definition to each lemma. Assignments are editable before checking and feedback shows the proper groupings.

The interaction is close to Postcard Pairs, with English labels replacing pictures. Mailboxes do not add a meaningful decision. Repetition is especially noticeable when the same three messages return in new positions.

**Improve:** make the destination matter. Sort messages according to the request, recipient, purpose or required response. Start with English support where useful, then offer Russian labels appropriate to the learner. If that distinct task is not worth developing, treat this as a matching variant rather than a major standalone game.

Evidence: [sorting rounds](../../flask_vocab_app/services/journey_vocabulary_games.py), `mailbox-sort`; [mailbox board](../../flask_vocab_app/ui/src/GameBoards.tsx), `MailSortBoard`.

### Lost Parcel Detective

**Verdict: needs the most substantial redesign.**

The four options combine two pictures with two routes. Both clues are needed, which is a real improvement over a one-clue match. However, the picture sentence and route are independently selected. An arbitrary statement such as “We can see the sea” is not evidence about a missing parcel.

There is no developing case, investigation or inference across rounds. The player performs two recognition tasks. The duplicate pictures are intentional combinations, but they can look like accidental duplication when the story does not explain them.

The current desktop layout is much wider than the earlier narrow screenshot. The remaining weakness is mainly the activity itself. On a narrow viewport, the clues, lower choices and check action require substantial scrolling.

**Improve:** author a small set of genuine delivery mysteries. Each clue should rule out a plausible option, and the final choice should resolve a stated problem. Use contextual distinctions such as owner, contents, location and destination. Four clear options remain enough. Test a few complete cases before building another generator.

Evidence: [detective construction](../../flask_vocab_app/services/journey_vocabulary_games.py), `detective`; [evidence board](../../flask_vocab_app/ui/src/GameBoards.tsx), `DetectiveBoard`.

## Core learning activities

### Speaking

**Verdict: one of the strongest reasons to use the application.**

It has five scenario families: café, shops, directions, station and meeting people. The base catalogue has 16 situation seeds, including eight café variants and two in each other family. Authored level data adds A1/A2 learning requirements. B1/B2 are not a complete implemented curriculum.

The same saved situation informs the interface, agent and reviewer. Scenario selection avoids recent repetition. The agent has a natural-ending mechanism and Russian-only role instructions. Grammar, fluency and task completion are assessed separately. The independent reviewer receives learner audio rather than relying on a potentially corrected live transcript.

These are substantial implementation strengths. They do not prove reliable assessment. Prompt instructions and quoted evidence can still be based on a misheard ending. The repository's earlier synthetic speech experiments explicitly record transcription variation and recommend human recordings next.

**Improve:** run a reviewed human-audio evaluation set with correct speech, wrong cases, wrong conjugations, self-correction, hesitation and mixed-language attempts. Check false corrections as carefully as missed errors. Test endings and interruptions on actual calls. Broaden the less-developed scenario families before adding many more categories. Connect one clear correction to optional follow-up practice.

Evidence: [assessment](../../flask_vocab_app/services/speaking_assessment.py), [ending logic](../../flask_vocab_app/services/speaking_lifecycle.py), [catalogue](../../flask_vocab_app/data/speaking_catalogue.json), [level contracts](../../flask_vocab_app/data/speaking_levels.json), [previous speech experiment](speech-preservation-results-20260911.md).

### Word Jumble

**Verdict: the best existing balance of freedom, challenge and tutor feedback.**

The learner creates an original sentence from three, four or five words. The feedback prompt recognises the idea, allows natural inflections and limits necessary corrections. It explicitly avoids pedantic correction of a missing final full stop. Additional words are generated when the chosen vocabulary pool is insufficient.

Draft revisions protect against stale submissions. Feedback quotes must match the answer. Failed assessment does not become a grade. These are useful protections around a motivating task.

The level system is approximate. Saved words are sampled by local difficulty, without ensuring that a full set combines well. The AI sees the topic and target words, but teacher-quality correctness still needs evaluated examples. Additional vocabulary is requested only when the saved pool is short, so discovery is less consistent than in the newer games.

**Improve:** keep the open task and personal commentary. Offer a few meaningful challenge styles, such as a short message or a humorous event, without prescribing the answer. Use accepted corrections for a later practice item. Make it easy to save an unfamiliar target word. Preserve the distinction between an error and an optional stylistic suggestion.

Evidence: [Word Jumble service](../../flask_vocab_app/services/word_jumble_service.py), [feedback contract](../../flask_vocab_app/contracts/sentence_feedback.py), [feedback presentation](../../flask_vocab_app/templates/_word_jumble_feedback.html).

### Native flashcards

**Verdict: retain as the main retention system; improve selection before adding more controls.**

The native player already has contextual clozes, English support, optional hints, answer-side dictionary links, images and audio, four ratings, timing, keyboard shortcuts, immediate advancement and undo. FSRS provides scheduling. Card content, review history and learner state are separate.

The main weakness is the selection of forms described above. A technically complete player cannot compensate for narrow or weak examples. Ratings are self-assessments, which is appropriate for flashcards; they should not be presented as independent grammatical assessment. Recorded response time is not itself evidence of understanding.

**Improve:** vary forms and contexts deliberately, keep audio and pictures reliable, and make problematic cards easy to revise or set aside. Reuse exact lesson occurrences where suitable. Validate that full sentence translations preserve tense, negation, aspect where relevant and the intended reading. Anki can remain the optional export workflow.

Evidence: [native player](../../flask_vocab_app/ui/src/NativeReview.tsx), [review service](../../flask_vocab_app/services/native_review.py), [FSRS boundary](../../flask_vocab_app/services/review_scheduler.py), [generation](../../flask_vocab_app/services/card_generation.py).

### Read a story

**Verdict: high learning value, with an older assessment path that needs attention.**

Reading connects text, optional speech and pictures, comprehension answers and vocabulary capture. Generated bilingual titles improve the library. Clicking unfamiliar words is a natural way to grow the vocabulary collection.

The answer assessor still uses a free-form JSON prompt and manual response cleanup, unlike the stricter written-activity contracts. It explicitly requests English feedback even when the interface is Russian. It also mixes comprehension with language correctness in one score, then contributes that score to reading progress. A learner can understand the story but lose reading credit for an imperfect written answer.

**Improve:** distinguish understanding from the quality of the learner's Russian response. Use the selected interface language and the same concise tutor style as Word Jumble. Add varied question types where useful, including main idea, inference and sequence. Preserve the original story and previous attempts when new questions are generated.

Evidence: [reading assessment](../../flask_vocab_app/services/comprehension_service.py), `_evaluate_answers`; [story presentation](../../flask_vocab_app/templates/_comprehension_content.html); [reading skill evidence](../../flask_vocab_app/services/skill_progress.py).

### Translate a sentence

**Verdict: useful deliberate practice with limited originality.**

The prompt allows synonyms, natural word order and ё/е variants. The reference is explicitly one possible translation. Drafts and attempts are stored separately, and provider failures do not create marks.

The task remains isolated English-to-Russian translation. Its feedback is a short strength, next step and example, rather than Word Jumble's richer commentary and targeted corrections. Sentences are generated from a topic and level; the generator does not currently receive the learner's saved vocabulary or lesson examples.

**Improve:** select sentences around a clear learning need, such as a recent case mistake or a useful lesson construction. Keep multiple valid answers acceptable. Let learners choose a short related set. Avoid treating punctuation and spelling as equal proxies for grammatical control.

Evidence: [translation service](../../flask_vocab_app/services/sentence_service.py), [translation storage](../../flask_vocab_app/repositories/translation_repository.py).

### Writing

**Verdict: strong educational purpose, but less inviting than Word Jumble.**

Prompts specify a purpose and a manageable length of roughly 30 or 100 words. Word targets are guidance rather than a pass/fail minimum. Assessment considers purpose, vocabulary, grammar and clarity. It should not rewrite the entire submission.

The interaction is still largely generate, write, check. The three difficulty names map to A1, A2 and B1, while other activities use different meanings for similar names. Topic selection is not the same as grounding the writing task in a tutor lesson or recent reading.

**Improve:** give the writing a clear recipient or purpose and a small choice of prompts. Show progress between the learner's drafts. Reuse a recent story, lesson or conversation as the starting point. Keep corrections selective, with optional detail available when wanted.

Evidence: [writing service](../../flask_vocab_app/services/writing_service.py), [writing repository](../../flask_vocab_app/repositories/writing_repository.py).

### Tutor lessons

**Verdict: the most distinctive integration opportunity in the application.**

Versioned uploads, page references, annotations, learning objectives, resumable exercises, OCR corrections and manually selected flashcard words make real tutor material reusable. Source quotations are checked against extracted pages. Earlier versions and learner answers remain available.

The current planner requires exactly three objectives and six tasks, with two tasks per objective. That is manageable, but a fixed structure can underserve a substantial document or overbuild a short one. Tasks use phrase, meaning, reading and writing formats. This is not yet a complete pre-reading, exercise, conversation and final-assessment programme.

Lessons already feed selected words into cards and games. Broader lesson-based Speaking and standalone Writing integration remains incomplete. OCR uncertainty also remains a content limitation, despite the correction workflow.

**Improve:** choose the amount and type of practice from the material and the learner's selected objective. Add a clear continuation into another activity while retaining the lesson sentence, page and revision. Have a short end-of-lesson recap identify what was practised and what to revisit. Keep the learner's selections authoritative.

Evidence: [lesson companion](../../flask_vocab_app/services/lesson_companion.py), `validate_plan`; [lesson AI contracts](../../flask_vocab_app/services/lesson_ai.py); [selected occurrences](../../flask_vocab_app/services/lesson_selection.py).

### First steps

**Verdict: a coherent introduction, not yet a repeatable curriculum.**

Five lessons now teach words and phrases before asking the learner to use them. They introduce the letter, bag, map, directions and requests for help. Completion saves progress and introduces related games. This is much clearer than disconnected tutorial screens.

Most tasks are short recognition exercises. The chapter does not yet lead into a developed sequence of later authored chapters and the final letter. Experienced learners also have to complete introductory prerequisites to unlock the games.

**Improve:** make the end of the introduction clearly hand over to suitable practice. Preserve game discovery for new learners, while providing a direct entry path for someone who already knows this material. Revisit introductory language later in a different context instead of extending the same tiny vocabulary indefinitely.

Evidence: [authored content](../../flask_vocab_app/data/first_steps.json), [First steps service](../../flask_vocab_app/services/first_steps.py), [unlocks](../../flask_vocab_app/services/journey_games.py).

## Shared implementation and integration

### Strengths worth preserving

- **Contextual data:** lesson words and native examples retain their lemma, surface form, meaning in context and provenance. The game pipeline does not require a single English definition on the lemma record.
- **Mixed vocabulary:** picture games currently prepare three familiar examples plus one discovery. Other example games prepare four familiar examples plus one discovery. Sparse pools are supplemented. Standalone practice is not restricted to the introductory words.
- **Appropriate media:** pictures are required for three picture games; letter reconstruction requires sentence audio; Directions needs neither; Radio has its own programme workflow.
- **Recoverable work:** preparation stages are saved, existing media can be reused, retries preserve successful work, and ownership is checked around saves.
- **Reliable persistence:** frozen sessions, duplicate-request handling, profile boundaries, reward deduplication and recovery from interrupted saves have substantial test coverage.
- **Separate rewards:** completion can earn coins despite mistakes or hints. Supported answers are generally excluded from skill evidence. The rating issues above require refinement, not removal of this distinction.

### Gaps across the activity collection

**Difficulty is inconsistent.** Speaking has authored A1/A2 tasks. Translation uses 1–5 mapped to A1–C1. Writing maps beginner/intermediate/advanced to A1/A2/B1. Word Jumble uses easy/intermediate/expert with approximate bands. Journey games expose 1–8 vocabulary difficulty. A learner cannot reliably predict the challenge from these labels. Use a shared practice-level vocabulary with activity-specific learning objectives; do not simply rename numeric values as certified levels.

**The games select variety rather than adapt to errors.** Recent vocabulary avoidance is useful, but it is not a model of what someone needs to practise. Four pictures are sufficient for one choice set. The problem is repeating the same associations across many rounds without a new sentence, constraint or retrieval demand. Ten rounds currently reuse four or five prepared examples. Increase variation through language and decisions before increasing media count.

**The language switch is incomplete.** The journey-game components contain English-only instructions, buttons and feedback. Reading assessment also explicitly requests English. This differs from bilingual Speaking, flashcards and much of the written interface.

**Media preparation precedes play.** A missing required picture can hold the whole prepared game at its loading screen. Staged recovery is good, but the experience still depends on sequential provider work. Use reviewed ready-to-play material for immediate entry, and prepare new material separately. Evaluate actual latency and cost before introducing worker infrastructure.

**A saved word is not a mastered word.** Familiar material is largely derived from the shared vocabulary library, not each learner's demonstrated knowledge. This distinction matters in households and for words added but never studied. Keep vocabulary capture and learner knowledge separate.

**Completions could lead somewhere more useful.** Most games prioritise returning to vocabulary or the lesson, playing again or opening Activities. They do not produce a focused review of errors or a reasoned next task. A small continuation based on the attempt would connect the existing features better.

**Accessibility needs task-specific review.** Picture buttons often expose the full English sentence as their accessible name. This avoids unnamed images, but creates a text-matching variant for screen-reader users. Do not remove those labels. Design an equivalent task deliberately and account for the different evidence. The JSX currently provides mostly standard button interactions; dedicated screen-reader and keyboard playtesting is still needed.

**Responsive work should focus on task continuity.** The desktop game shell now uses the available width. On narrow layouts, large cards can separate the instructions from the controls. Keep the current task and check action readily accessible without obscuring choices. A short completion recap and correction pass matter more than making every surface larger.

**The test suite verifies contracts more than content quality.** Test media and provider doubles establish ownership, persistence and state transitions. They cannot establish that an image depicts a distinction, a Russian sentence is natural, a distractor is fair or a voice sounds convincing. Add reviewed content examples and learner sessions alongside automated checks.

**Maintenance is becoming harder.** Several player files compress substantial logic and markup into very long lines. Assessment and preparation patterns differ across activities. Format and separate those responsibilities as the relevant features are improved. Flask and Preact are adequate for these interactions; this audit found no reason to replace the stack.

## Recommended order of work

| Order | Work | Expected benefit | Relative effort |
| --- | --- | --- | --- |
| 1 | Correct chance and repeated-answer handling in skill evidence | More trustworthy progress across games | Medium |
| 2 | Improve native form selection and Missing Stamp distractors | Directly strengthens Russian case and conjugation practice | Medium–large |
| 3 | Add correction attempts and a missed-item review | Better learning from every existing game | Medium |
| 4 | Resolve public-demo availability and add prepared samples | Visitors can complete the experience advertised | Small–medium |
| 5 | Standardise feedback language, practice-level descriptions and completion actions | Less confusion when switching activities | Medium |
| 6 | Evaluate Speaking with human recordings; review Radio programmes and questions | Better confidence in the strongest AI activities | Medium–large |
| 7 | Redesign Detective and narrow Pack the Bag to suitable tasks | More coherent and enjoyable games | Medium–large |
| 8 | Connect lesson objectives and recent mistakes to subsequent practice | A richer application without adding disconnected activities | Large, incremental |

Do the missing-landmark rendering fix alongside the next Directions pass. Improve mobile task continuity alongside the shared correction workflow. Keep Postcard Pairs and Mailbox Sort modest until they demonstrate distinct value.

## Evaluation criteria for the next pass

Use a small set of independently reviewed material and playtest it with learners at different starting points. Record where people hesitate, misunderstand instructions or leave, rather than treating completion alone as enjoyment.

- **Task clarity:** can someone explain what they are trying to do after reading the opening instruction?
- **Meaningful choices:** can the learner answer from a visual or formatting shortcut without understanding the intended Russian distinction?
- **Content validity:** is the sentence natural, the translation contextual, the picture relevant and the correct answer defensible?
- **Recovery:** can a learner understand and repair a mistake without restarting or losing work?
- **Variety:** does a second session offer a new challenge rather than the same associations in another order?
- **Learning transfer:** can the learner use the form in a new sentence or understand it in a new recording?
- **Technical reliability:** measure preparation time, failed stages, interrupted saves, replay behaviour and device-specific audio failures.
- **Assessment restraint:** hints, answer exposure, guesses and ambiguous audio must not become strong claims about proficiency.

The most valuable direction is a connected sequence: encounter useful Russian, understand it, use it, receive specific feedback and revisit it later. The existing data model and core activities can support that sequence. The next improvements should make it visible to the learner.
