# Curriculum validation

## Current status

The application has four authored A1 teaching units. They are practice material, not validated examinations. Their Russian examples and provisional answer keys still need review by a qualified teacher or assessor. No human review or learner trial is recorded in this package.

| Unit | Focus | Contextual choices | Typed forms | Listening |
| --- | --- | ---: | ---: | ---: |
| Where and where to | Location, destination and movement within a place | 4 | 3 | 3 prepared clips |
| Possession and absence | An available item, a missing item and its owner | 6 | 4 | Not prepared |
| Objects and recipients | Direct objects, animate objects and recipients | 6 | 4 | Not prepared |
| Time and daily routines | Days, times, conjugation and tense | 6 | 5 | Not prepared |

Each unit has classified examples and its own original Writing task. Short reading questions require information from a supplied context. Typed tasks test a specified form; they are not free-writing tests. Their accepted variants include selected fuller phrases and ignore outer whitespace, letter case and final punctuation. This does not mean that all possible paraphrases are accepted.

The three new units add 18 contextual choices and 13 typed tasks. They do not cover the whole A1 case or verb system. For example, the object unit does not teach all plural animate forms; the routine unit does not assess every tense or aspect pair.

Speaking links open existing activities. They do not carry the unit's task or criteria into a conversation. Possession links to shopping; routines link to meeting people. The objects-and-recipients unit has no Speaking link because no current scenario reliably elicits its specific task.

New units have no listening buttons until their recordings are prepared and registered. A written transcript alone is not listening material. The earlier location unit retains its original published content, contracts and recordings.

## Automated checks

Run from the repository root:

```sh
PYTHONPATH=flask_vocab_app python -m unittest \
  tests.test_curriculum_unit_expansion \
  tests.test_curriculum_review_packet \
  tests.test_curriculum_units \
  tests.test_curriculum_unit_listening
python scripts/prepare_curriculum_review.py --check
```

These checks verify content identities, reference IDs, accepted-form matching, session ownership and saved evidence. They exercise the real application routes without a model call. They check that answers are hidden before a response, retries do not duplicate records, and unavailable audio cannot start a session. Unit practice does not write words into the vocabulary database or award a curriculum pass.

The reviewer fixture has 66 authored cases: 48 controlled-form cases and 18 Writing cases. It includes wrong cases, wrong conjugations, valid alternatives, incomplete messages, empty evaluator input and use of a model answer. An empty Writing draft remains blocked by the live form; its fixture tests the assessment concept of insufficient evidence.

A passing test shows that software follows its declared key. It does not prove the key is linguistically sound. The Writing expectations are author hypotheses. The offline script does not call a grader, measure model accuracy or certify a learner's level.

## Review packet

Generate a separate packet for each review round:

```sh
python scripts/prepare_curriculum_review.py --output-dir /tmp/russian-arcade-a1-review
```

The directory contains:

- `reviewer.json`: examples, prompts, reference requirements, learner responses and blank review fields. Case IDs do not reveal their expected outcome.
- `author-key.json`: the provisional keys and rationale. Keep this separate until initial ratings are complete.
- `manifest.json`: content hashes, fixture identity and the limits of this review.

The exporter reads source files only. It does not open a learner database, use credentials or contact a provider. Repeated exports are identical. It refuses to overwrite a completed or edited review file.

Unit hashes pin the exact material under review. If a published unit needs correction, retain the old version for saved attempts and create a new unit version. Issue a new fixture version and review the changed cases. Do not update a hash merely to silence a failed check.

## Language and task review

Use a qualified Russian-as-a-foreign-language teacher or assessor. Record their role, date and the content hashes. Do not describe a model pass as a human review.

Review the examples first, then each question and its distractors:

1. Is the Russian natural, and does the English explanation preserve its meaning?
2. Is the grammatical distinction correctly classified? Is its prerequisite knowledge taught or stated?
3. Does the prompt supply enough context for one intended choice? Could another option be valid in ordinary Russian?
4. Does a typed task accept reasonable ways to give the requested form? Are any accepted variants actually wrong in context?
5. Does the cited requirement match what the learner does? A reading answer cannot establish listening or spontaneous speaking ability.
6. Is the explanation short, accurate and useful after a wrong answer?

Record disagreements with examples. Rework ambiguous items before release as assessment material. A second assessor should resolve disputed keys independently; do not hide disagreement in an average score.

## Rubric review

Rate the Writing cases before reading the author key. Judge the requested communication and grammar separately. A message can fulfil its purpose while containing a recoverable case error. The fixture includes `У меня нет вода` for that reason: the missing item remains clear, while `воды` is the required correction.

Use the existing criterion outcomes consistently:

| Outcome | Meaning for these tasks |
| --- | --- |
| Satisfied | The requested information and communicative purpose are clear. |
| Partial | Relevant information is supplied, but an important part is missing or contradictory. |
| Not satisfied | The response provides evidence but does not fulfil the criterion. |
| Insufficient evidence | There is not enough observable response to judge it. |

Supported work may still answer the task correctly. It must not become independent evidence. Record model-answer use separately from the quality of the resulting text. Keep the original response when noting errors; do not replace it with a corrected version before assessment.

After human labels are agreed, a separate model-evaluation run can compare provider reports against them. Record the model, prompt version, task hash, response, support and full report. Count false passes, false failures, unsupported claims, invalid reports and abstentions separately. Split related variants between development and evaluation sets by task family to avoid testing a paraphrase of the same example used for tuning. No such provider run is included here.

## Listening and speaking review

The location unit's three recordings have file and transcript hashes. File checks do not establish natural pronunciation or suitable listening difficulty. Review every recording in a browser, including slower playback, replay, hint and transcript behaviour. Confirm that the answer is not shown before listening.

For future recordings of the new units, author the message and question together. Record only after its intended meaning and answer are reviewed. Register the final audio hash and duration before exposing the listening control.

Speech-error evaluation needs original audio with known wording. Record consented speakers saying both correct and deliberately incorrect forms. Include recoverable mistakes, restarts and ambiguity. Compare the audio, raw transcription and assessor report; check whether transcription silently repairs an error. Synthetic speech can test transport and playback, but cannot establish how a real learner's pronunciation will be handled. This package contains no new speech samples or completed fluency validation.

## Learner trial and release decision

Run the revised units with learners near the intended level. Observe whether they understand the task, distinguish the forms, use hints and return to their saved work. Record unclear prompts, accepted answers that were rejected and corrections they cannot act on. Test keyboard use, narrow screens and Cyrillic entry as part of the same session.

Before these tasks can support a level gate, the release record needs reviewed keys, resolved ambiguity, enough independent tasks per requirement, human-checked rubric behaviour and learner evidence. Document remaining gaps explicitly. One correct choice, one memorised form or one successful unit is not an A1 pass.
