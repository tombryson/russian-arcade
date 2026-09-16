# Experience review and migration correction

9 September 2026. Based on inspection of the running original app at port 5050, the new preview at port 5051, implementation source and migration documents. This is an expert review with owner feedback, not a child usability study. No live AI generation or assessment was requested during inspection.

## Decision boundary

**Current approved direction, 9 September:** [Barsik's campaign](barsik-journey.md) now follows one letter addressed to the learner, through worlds unlocked with earned Lingocoins, ending in a comprehension assessment of the letter using practised Russian. This supersedes earlier invitation, side-delivery and cosmetic-only progression proposals below. Individual access is the default; household approval/PIN controls are optional. The following audit records the earlier interface correction.

Follow-up: the owner accepted the correction, requested the rebuild and explicitly removed the passport. The cat is now named Barsik (Барсик). The exact former visual reference remains historical.

**Later refinement, 9 September:** the owner likes the rebuilt flow and requests the original stronger hero plus a coherent, tiered delivery story. The [Barsik journey brief](barsik-journey.md) now defines that direction: an opening invitation addressed to the learner, followed by deliveries to named characters. Restore the welcome and space the practice choices below it; keep conventional navigation and real learning state. Earlier recommendations here to minimise or omit the narrative are superseded by that refinement. The passport stays removed.

**Latest copy/tutorial refinement:** the owner rejects the lengthy invitation summary and prefers a direct hook: Barsik has a letter for the learner, but a world still to cross before delivering it. The restored first-delivery card now opens a short Lingocoin and practice tutorial. This supersedes the invitation-at-your-door premise above. Completing the tutorial prepares the learner; it does not mean the letter arrived or coins were earned. The journey brief records the current contract.

At the initial review, the owner retained the new visual elements, illustration and theme, and rejected the incoherent story, wording and flow. Earlier documents incorrectly broadened visual approval into approval of postal navigation. The later narrative request above provides explicit direction for a coherent story; it does not restore those confusing labels or the old sample adventure. The detailed chapter brief remains a proposal to build and review.

The product is a household Russian-learning application: learners build vocabulary, remember it through review, and use it in reading, sentence and writing activities. Grown-ups add and review suitable material and manage integrations. This purpose must be apparent on screen without a character backstory.

Retain the original application's useful activities as the functional baseline. Retain the new visual system and shared learning infrastructure. Native flashcards remain the first new learning capability, with optional Anki Link; local-first delivery, complementary Drive/SQLite workflows and adult content approval remain confirmed.

## What the actual screens show

| Area | Original application | New preview | Required correction |
|---|---|---|---|
| Entry and navigation | Flashcards, Comprehension, Writing, Lessons, Word Jumble, Sentences, Vocab List and Phrasebook are discoverable | Your post, Word pocket and Passport hide the existing activity choices | Use recognisable learning destinations and maintain a feature-parity inventory |
| Starting practice | The generator exposes many filters; saved stories and games are available | A marketing-style hero introduces an undefined delivery, followed by one sample activity | Prioritise a real start/resume action; make other available activities easy to choose |
| Reading | The inspected saved story follows Anna and her dog: a walk, a found ball, a new toy. Questions concern that story | Moon Picnic mixes receiving a letter, packing someone else's apple, writing “I am taking an apple” and completing a delivery | Establish one task and speaker; each action must advance it and the ending must resolve it |
| Sentence work | A saved Word Jumble game explicitly asks for a sentence using supplied vocabulary | The learner copies a displayed sentence but the completion implies a successful fictional mission | Preserve composition as a game; label copying as supported practice and distinguish it from recall |
| Preparation | Topic/level filters, creation controls and saved items share the same screens | Almost all useful original tools sit behind “For grown-ups” | Separate preparing material from practising it; children and adults can use the same activity types |
| Continuity | Saved content and the real vocabulary library exist | Sample progress lives in component memory; Word pocket/Passport depend on finishing this sample | Connect learner-specific content, attempts and progress; do not substitute sample stamps for real continuity |
| Visual character | Uneven layout, dense configuration, inconsistent hierarchy | Strong illustration, bold type, distinctive paper/ticket treatment and palette | Apply those visual strengths to useful controls and reading surfaces |

This does not establish that every old workflow is flawless. For example, saved-story labels expose record IDs and duplicated metadata; “Word Jumble” does not clearly describe its creative composition mechanic. Improve these specific frictions while preserving the useful task.

## Recommended product structure

Use **Russian Arcade** as the working app label, with the plain description **Learn and practise Russian**. A permanent rename is unnecessary for this correction. Word Post can remain an internal migration directory/route name; it is not a requirement for the learner-facing brand.

Use three main destinations: **Home**, **Activities**, **My words**. Keep the learner/profile entry visible, with **My progress** there and a short, factual session summary on Home. Grown-up controls remain a separate entry. Test this structure with the intended household before treating it as settled.

- **Home:** continue an unfinished session when one exists; otherwise offer word review when due or a short introduction to an approved set. State what will happen before Start. Show only real counts and available actions. Keep “Choose an activity” visible.
- **Activities:** Flashcards; Read a story; Sentence practice; Make a sentence (the existing creative Word Jumble); Writing; Lessons. Use a short description and actual available content. Do not add placeholder games or locked worlds. The next release must identify which activities are already usable and which still belong to the existing workspace.
- **My words:** the learner's approved vocabulary with meanings, available pronunciation and examples. Allow words encountered in reading to lead into review. Distinguish words seen, practised and recalled; do not infer mastery from one correct choice.
- **My progress:** real practice history and supported/independent evidence. Lingocoins can recognise participation later; Elo-style selection remains an implementation detail until useful, defensible evidence exists.

Show a single recommended start without removing choice. Offer topic and length when they help someone choose practice; keep sound, replay, hints and text support within reach. Move generation/provider settings, batch sizes, sync, approval and export into preparation tools. Grammar help remains available to learners who need it. Adult learners retain longer and more advanced practice.

For a new learner with no approved material, explain the actual prerequisite and offer the grown-up setup path. The later owner-requested welcome now introduces Barsik and links to a separate practice section. Returning learners can use Activities directly; a future compact return view needs real session state. An invitation addressed to the reader is story content, not a claim that a static hero was personalised from their learning history.

## Barsik and the visual theme

Recommended role: **Barsik is the cat who helps you practise Russian.** A brief introduction is sufficient. Barsik can demonstrate a word, offer a useful hint or participate in an optional story. Essential instructions come from the interface and remain understandable without the character. Establish a consistent character reference if future content needs one; no new lore is needed for the main app.

Keep the cut-paper illustration, warm paper, cobalt/ink/tomato/yellow colours, bold headings, readable Cyrillic and occasional perforated edges. Make the main ticket an actual practice invitation. Let illustrated objects relate to a topic or provide atmosphere without implying functionality. Put readable tasks ahead of promotional prose and shorten the hero for repeat use.

Retire Moon Picnic as the default learning journey. An optional story could later use a picnic or mail delivery if it establishes who is doing what, why the learner is involved, and what changes after their action. Its language objective, instructions and outcome must agree. Fantasy is compatible with coherent cause and effect; a paragraph of backstory cannot repair an unrelated exercise.

## Concrete first flow: native word review

Illustrative copy, not a claim that this feature is already implemented:

1. **Home:** “Practise your Russian words.” A real approved set has a title, description and **Start practice** action. Returning learners see actual due review or resume state.
2. **Introduction for a new word:** show `яблоко — apple`, an appropriate picture and prepared pronunciation when available. Explain “Look at the word and its meaning.” This is introduction, not an assessed recall.
3. **Later review:** “How do you say ‘apple’ in Russian? Say it or think it, then reveal the answer.” Provide **Show answer** and support without requiring typing or pretending speech is being assessed.
4. **Reveal:** show the Russian answer. Let the learner honestly choose **Practise again** or **I remembered**; save the review according to the native scheduler's assistance policy. The UI must not penalise admitting uncertainty through rewards.
5. **Finish:** name what was practised, acknowledge saved progress only after persistence succeeds, and offer **Finish** or an available related activity. Do not claim the words are mastered.

The same vocabulary can then appear in a reviewed story or the existing sentence game. That creates continuity through learning material and saved experience. It does not require every activity to be a chapter of a fictional campaign.

For reading, preserve the existing understandable sequence: choose a story → read/listen with support → answer questions about it → see useful corrections → revisit unfamiliar words. For composition: see supplied words → write a sentence → receive appropriate feedback → revise/save. Neither needs to become a letter.

## Migration consequences and next scope

1. **Correct the UX contract before extending the preview.** Replace story-led navigation/copy with the purpose and activity structure above; keep the artwork. Review one complete task, including its ending, before broad visual rollout. This is a prerequisite within the next native-review slice, not a new multi-stage world-building project.
2. **Reapply the design to existing functionality incrementally.** Shared tokens and page hierarchy can improve Flask templates immediately. Preserve working routes and data until replacement parity is demonstrated. An attractive launcher alone does not count as an integrated learning release.
3. **Deliver native review end to end on Stage 1.** Keep profiles, approved versions, attempts, local assets, recovery and rewards infrastructure. Finish the real queue, review, save/resume and undo through a clear interface. Do not spend this milestone persisting Moon Picnic.
4. **Adapt existing activities in the current priority order.** Reuse their mechanics and content services, add learner isolation/approval and suitable support, then share words/progress across them. Matching games are additional modes; they do not replace open sentence composition. Anki remains optional.

Flask, SQLite, Jinja/HTMX and bounded Preact interactions can deliver this presentation. The UI problem is not evidence for another stack migration. Preact is useful for card reveal and interactive answer state; ordinary pages and forms can remain server-rendered. Apply one design system across both and keep one owner of each interactive DOM region. Do not force a full Preact rewrite merely because an activity serves children. Local database/asset durability and later Fly.io preparation are unchanged.

Main migration risks remain lost feature parity, inappropriate reuse of legacy answers/private material, misleading progress, and two disconnected interfaces. Mitigate them with the route inventory, reviewed shared content plus independent attempts, evidence-specific progress, and a complete save/resume path for each migrated activity. Visual parity alone does not resolve those risks.

## Experience acceptance gate

Before a broad cutover, observe the intended learners using a small working slice with their normal level of adult support. Age and reading ability are still provisional. Record behaviour, not only whether someone likes the picture.

- Can the learner say what the app is for and start an activity without an explanation of invented terminology?
- Before answering, can they explain what to do and access the knowledge/support the task assumes?
- Do the instructions, response, correction and completion describe the same task?
- Can they choose another real activity, leave and return without losing work?
- Can the grown-up find existing games, add/review material and understand what the child actually practised?
- Does the interface describe copying, assisted answers and independent recall accurately?

Usability references: [Nielsen Norman Group's heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) support familiar language, visible choices, clear status and purposeful visual hierarchy. [W3C clear-content guidance](https://www.w3.org/WAI/WCAG2/supplemental/objectives/o3-clear-content/) supports understandable purpose, simple wording and clear steps. These principles inform this recommendation; they do not validate this exact navigation or a curriculum. Minimising recall needed to operate the interface is separate from deliberately practising vocabulary recall.

## Scope of this review checkpoint

This checkpoint corrects the programme documents. It does not change runtime screens, databases, card scheduling or artwork. Earlier engineering verification remains evidence about engineering behaviour, not proof that the preview is a coherent learning experience.
