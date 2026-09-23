# Curriculum validation

## Current status

The application has seven authored A1 teaching units and an opt-in diagnostic pilot covering five skills. They work without a tutor. Human review is optional editorial quality assurance for the maintainers, not a prerequisite for using the app or receiving feedback.

The examples and answer keys remain provisional. No independent human review or learner trial is recorded. The pilot does not award a level, unlock activities or claim to be a TORFL examination.

| Unit | Focus | Contextual choices | Typed forms | Listening available |
| --- | --- | ---: | ---: | ---: |
| Where and where to | Location, destination and movement within a place | 4 | 3 | 3 clips |
| Possession and absence | Available items, missing items and ownership | 6 | 4 | 3 clips |
| Objects and recipients | Direct objects, animate objects and recipients | 6 | 4 | Not yet |
| Time and daily routines | Days, times, conjugation and tense | 6 | 5 | Not yet |
| Describing clothes and objects | Adjective agreement with nouns | 6 | 4 | Not yet |
| Referring to people | Personal and possessive pronouns | 6 | 4 | Not yet |
| Walking and travelling | Walking, transport and repeated journeys | 6 | 4 | Not yet |

Each unit has classified examples, a dedicated reading page and an original Writing task. Typed tasks test a specified form. They accept selected fuller phrases and ignore outer whitespace, case and final punctuation. They do not claim to accept every paraphrase or measure independent writing.

These units do not cover the whole A1 grammar system. Supplied infinitives in motion tasks test conjugation; separate choices test the distinction between movement types. Speaking links open existing scenarios. They do not establish that those scenarios assess the unit's exact criteria.

There are seven authored three-item listening packs. Location and possession are fully recorded and available. One objects-and-recipients clip is prepared, but its incomplete pack remains unavailable. The other packs and both pilot recordings are pending. No listening button appears for an incomplete pack. The four earlier published unit sources remain unchanged.

## Diagnostic pilot

The pilot is accessible from Curriculum and the profile's course section. A learner can save work, change skill, return later and retry an individual skill. Original writing and speaking recordings are saved before feedback is requested. A failed review can be retried explicitly without resubmitting the response.

| Skill | Sample per form | Interpretation |
| --- | --- | --- |
| Language use | Six contextual choices | Specified forms in these sentences |
| Reading | One passage and three questions | Meaning, reference and sequence in that passage |
| Listening | One recording and three questions | Information heard in that recording |
| Writing | One personal message | Communicative purpose and requested details |
| Speaking | One original recorded reply | Personal information and intelligibility in a short monologue |

Each skill has two authored forms. They have not been calibrated or shown to be equally difficult. Retrying a previously seen form preserves prior feedback as assistance. Hints and transcripts are recorded. Listening playback is a delivery receipt, not proof of attention. The speaking task does not assess dialogue or turn-taking.

Feedback is specific to the saved response. Unclear or unavailable evidence remains unscored. There is no aggregate pass mark. New pilot sessions require both verified listening recordings; existing saved work remains accessible while media is being prepared. This is a media-readiness check, not a human-review requirement.

## Automated checks

Run from the repository root:

```sh
PYTHONPATH=flask_vocab_app python -m unittest \
  tests.test_curriculum_unit_expansion \
  tests.test_curriculum_unit_a1_expansion \
  tests.test_curriculum_review_packet \
  tests.test_curriculum_review_ingest \
  tests.test_assessment_pilot_review_packet \
  tests.test_assessment_pilot \
  tests.test_assessment_pilot_integrity
python scripts/prepare_curriculum_review.py --check
python scripts/prepare_assessment_pilot_review.py --check
```

The checks verify content identities, reference IDs, accepted forms, ownership, original response storage and grounded reports. They exercise the application without paid model calls. They test hidden answers, transcript assistance, missing audio, stale forms, duplicate requests and explicit review retries. Passing tests shows that the software follows its declared rules; it does not validate those rules as a proficiency assessment.

The current unit fixture contains 120 authored cases: 84 controlled-form cases and 36 Writing cases. It includes valid alternatives, wrong forms, incomplete messages, empty evaluator input and model-answer use. Empty Writing drafts remain blocked in the live form. The fixture tests the evaluator's treatment of insufficient evidence.

## Optional review packets

Export a separate packet for each review round:

```sh
python scripts/prepare_curriculum_review.py --output-dir /tmp/arcade-units-review
python scripts/prepare_assessment_pilot_review.py --output-dir /tmp/arcade-pilot-review
```

Each directory contains:

- `reviewer.json`: source material, prompts, criteria and blank review fields. Unit sample responses use neutral case IDs.
- `author-key.json`: provisional keys and explanations. Keep this file separate until initial ratings are complete.
- `manifest.json`: source hashes, recording inventory and review limitations.
- `audio/`: available recordings. Missing clips are marked as unprepared in the reviewer file.

The pilot packet includes both forms of all five skills. It contains no real learner recordings or responses. The unit packet includes all seven listening sources, even where recordings are still pending. Neither exporter accesses learner data, credentials or a provider. Exports refuse to overwrite edited reviews or changed recordings.

Source hashes pin the material under review. Corrections to published tasks need a new content version so saved attempts retain their original prompts and keys. Issue a new review fixture when content changes; do not replace hashes merely to silence a check.

## Review submissions and disputed items

A reviewer fills a copy of `reviewer.json`. Record a name or identifier, qualification, ISO date and `kind: "human"`. Internal model work uses `kind: "internal_model"`; it does not count as human review. These are declared identities, not externally verified credentials.

```sh
python scripts/review_curriculum_packet.py \
  --packet-dir /tmp/arcade-units-review \
  --review /path/to/completed-review.json \
  --output /tmp/arcade-review-report.json
```

The importer checks the source pins, original prompts, responses, keys and bundled audio before accepting review fields. One completed human rating is recorded. A second rating is useful for comparing marking; it is not mandatory for every item. Missing ratings, disputed keys, new alternatives and content concerns remain explicit in the report.

For disputed items, collect a second independent rating. The report includes an adjudication template for a separate assessor. An adjudication is bound to the exact packet and submitted reviews; it cannot silently replace different work. Accept, revise and exclude decisions remain separate. Revised or excluded material needs a follow-up content change. The tool never changes learner records, grants a level or blocks a learner.

## Review criteria

A Russian-as-a-foreign-language teacher or assessor can examine:

1. Natural Russian and accurate English explanations.
2. Correct grammatical classification and necessary prerequisites.
3. Enough context for the intended choice, including plausible alternative answers.
4. Reasonable accepted forms and rejected forms.
5. Alignment between the cited requirement and the response the task actually elicits.
6. Brief, useful feedback after an error.
7. Clear, natural recordings and an appropriate listening pace.

For Writing, judge communication separately from grammar. `У меня нет вода` still communicates the missing item, although `воды` is the required form. Keep the learner's original response when recording a correction. Supported work can be correct without becoming independent evidence.

Use `satisfied`, `partial`, `not_satisfied` and `insufficient_evidence` for the stated criterion. Do not infer a whole proficiency level from one choice or short response.

After a reviewed dataset exists, a separate provider evaluation can compare model reports against it. Record model identity, prompt version, task hash, original response, assistance and full report. Count false passes, false failures, unsupported claims and abstentions separately. Keep related task variants out of both the tuning and evaluation sets. No such calibrated provider evaluation is included here.

## Browser playback checks

On 24 September 2026, a fresh Codex in-app browser tab played the authored location clip through its native controls to the end: duration 7.476825 seconds, no media error. The receipt unlocked answers. Replay and 0.75× playback worked. Saving and advancing restored the listening requirement for the next question. Explicit transcript use was marked as assistance.

A generated Comprehension test fixture also played a real bundled MP3, unlocked response fields, saved five responses and restored them after reload. Generation and marking were mocked. This checks playback, transport and saved state, not provider accuracy or the linguistic quality of generated content. Keyboard Space operated the native player.

No human pronunciation assessment or microphone trial is claimed by these checks. Speech-error evaluation needs consented original recordings containing known correct forms, mistakes, restarts and ambiguity. Compare the audio, literal transcription and feedback to detect silent autocorrection. Synthetic speech is useful for transport tests but cannot establish recognition accuracy for real learners.

## Future assessment validation

Learner trials should examine task clarity, rejected valid answers, useful corrections, saved work and keyboard/mobile use. A consequential level gate would need reviewed keys, resolved ambiguity, enough independent tasks per requirement and tested marking behaviour. These are future validation criteria, not dependencies for today's standalone practice and diagnostic feedback.
