# Describe the scene

## Purpose

Describe the scene replaces Postcard Pairs in the activity catalogue. The learner chooses Russian words and endings to describe a simple illustration and a short situation. Each question tests a specific grammatical distinction.

Postcard Pairs could often be solved by recognising one noun in each unrelated sentence. The new activity holds the scene and surrounding vocabulary steady. Its alternatives differ in the feature being practised: a preposition, case ending, motion verb, agreement or participant role. Existing Postcard Pairs sessions remain readable and playable.

## Practice sets

| Set | What the learner chooses | What the question must establish |
|---|---|---|
| Location | A spatial preposition and the noun form it requires | Where the subject is relative to the named object |
| Motion | The verb form that fits the journey | Travel on foot or by transport, a current trip or habit, and the relevant stage of the journey |
| Position and placement | A verb describing a position or placing something | Whether the object is already there or somebody is putting it there |
| Agreement | The adjective form matching its noun | The noun's gender and case in the sentence |
| Who does what | The noun forms identifying the participants | Which person acts and which person receives the action |
| Mixed practice | Questions from several sets | The same evidence as each individual set |

The first question bank contains 52 authored questions. The activity offers five or ten questions. Choice banks retain their authored order. Learners can change their selection before checking. Every blank must be filled before submission.

A photo cannot establish that a trip happens every day, or that an arrival has just been completed. The short situation supplies those facts. It must not leave the learner guessing what the illustration was intended to mean.

## Content rules

- Write and check the sentence, correct forms, alternatives and explanation together.
- Keep the surrounding wording natural. Use Russian choices even when the interface language is English.
- Test the noun ending as a separate choice where that is the objective. Do not silently correct it when a preposition is chosen.
- Use a caption to resolve genuine visual ambiguity. Do not disguise a vocabulary test as a grammar exercise.
- Avoid rejecting a reasonable alternative. Either include it as an accepted answer or make the situation specific enough to distinguish the intended response.
- Keep grammar explanations short and in the interface language. Russian examples remain in Cyrillic.
- Vary words and situations beyond the introductory lessons. Familiar vocabulary can support a question; it must not limit the whole curriculum to the learner's saved word list.

The first release uses authored question sets. It does not ask a model to invent and mark its own grammar questions during play. Automated checks can validate answer contracts and possible word forms. They do not prove that a sentence is natural or that an illustration is unambiguous.

## Interaction and feedback

The scene and situation appear beside a sentence with visible blanks. A labelled bank of buttons fills each blank. Selected buttons remain visible so learners can reconsider their choices before checking.

Feedback distinguishes the parts of an answer. A learner who chooses the right spatial relation and the wrong ending should see which decision was right and why the ending needs to change. The correct sentence becomes available after checking. Local installations can then request its Russian recording through the existing speech service; the public demo does not offer these unbundled recordings. Full-answer audio must not be accessible before the attempt through a guessed audio key.

The existing correction and missed-question review flows retain the first answer. Completing practice uses the normal participation reward rules. Rechecking a sentence or replaying a correction must not create another reward. The activity is guided practice, not certification of a CEFR level or spontaneous writing ability.

## Implementation

The new game has the stable ID `scene-builder`. Its saved question payload includes the scene identifier, bilingual situation, sentence segments and ordered slots. Each slot owns its allowed choices. Answer IDs are validated on the server against those slots.

The activity uses the existing `journey_game_sessions` storage for ownership, frozen questions, first attempts, hints and completion. It uses the existing correction records and reward ledger. It does not need a separate vocabulary database or a database migration.

Bundled illustrations load immediately. Reusing a cat, table and book allows consistent spatial scenes without generating another picture for every round. The asset prompts and output files are recorded in [the artwork notes](scene-builder-artwork.md).

Completed contextual examples can use the existing explicit vocabulary and native-card actions. These actions preserve the Russian sentence, surface form and contextual meaning. They do not introduce a universal English translation field on the lemma table or alter Anki progress.

## Verification

The automated checks cover slot validation, saved attempts, corrections, profile ownership, answer-audio access, public-demo restrictions and lemma/form resolution for every authored card target. Browser checks cover desktop and mobile layouts, separate component feedback and retry navigation. These checks do not replace a Russian tutor’s review of the curriculum.

## Remaining work

- Expand the reviewed question bank after observing real learner errors.
- Let suitable tutor-lesson vocabulary populate reviewed grammatical patterns. The first release does not automatically transform arbitrary lesson sentences into validated grammar questions.
- Add an optional typed or spoken answer after button-based practice. Recognition and sentence construction should not be presented as proof of unaided recall.
- Add a listening-led variant with prompts that supply the situation without speaking the answer.
- Review alternative answers and illustrations with a Russian tutor before using the results for skill-rating changes.

## Language references

[Direction and location](https://www.pelister.org/russian/tutorials/0061.html) explains the accusative/prepositional contrast with `в` and `на`. [OpenRussian's verbs of motion reference](https://en.openrussian.org/grammar/verbs-of-motion) describes travel mode, directionality and motion prefixes. These are reference aids; each exercise still needs contextual review.
