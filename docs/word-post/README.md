# Word Post migration programme

Current guided course: [A1 journey milestones](course-milestones.md). The home-first route, received letters and cumulative assessment implement the [milestone build plan](journey-milestones-build-plan.md).

The [curriculum](../curriculum.md) is the current reference for the fifty A1–C2 topics, target vocabulary, grammar and activity briefs. Earlier migration proposals remain historical context.

Next programme: [Curriculum and assessment implementation plan](../curriculum-uplift-plan.md). It covers the source-backed A1–B2 teaching scope, activity evidence, five-domain assessment, release gates and preservation of existing progress. Coins buy optional games; they do not unlock proficiency levels or the current guided milestones. Earlier coin-based world proposals below are historical.

[Describe the scene](scene-builder.md) replaces Postcard Pairs in the catalogue with focused grammar practice. Learners select Russian words and endings to describe a simple illustration and situation. Existing Postcard Pairs sessions remain available.

Follow the directions uses the [procedural directions engine](procedural-directions-implementation.md). It assembles neighbourhood blocks, binds delivery events to real places and prepares short AI conversations around checked Russian directions. Each assignment includes similar buildings or entrances that require a spatial distinction. Towns stay stable between deliveries. [Earlier generators](procedural-deliveries.md) remain available for saved sessions and prepared demo content. The [wider redesign specification](directions-game-redesign.md) covers later assessment and spoken interactions.

[Journey games](journey-games.md) includes eight mechanics, with permanent access through the [game shop](game-access.md). First steps does not automatically unlock them. [Mixed vocabulary and radio practice](mixed-vocabulary-and-radio.md) combines familiar words from SQLite or tutor lessons with useful new vocabulary that learners can explicitly save. Picture games prepare four examples; text games do not require pictures. Post Office Radio has one roughly one-minute programme and four comprehension questions. Prepared content is cached, contextual-example games offer explicit native-card export, and shared profiles, rewards and provisional skill observations remain in place.

The [Lessons companion](lessons-companion.md) provides versioned annotated tutor material, reading bookmarks and individual practice with saved answers. [Lesson-driven practice](lesson-driven-practice.md) lets learners highlight words on the scanned page, save pending selections and create contextual native flashcards with pictures, audio and the existing review schedule. The [original lesson audit](lessons-audit-and-direction.md) records its rationale; writing, conversation, recap and completion rewards remain later stages.

The [vocabulary library](vocabulary-library.md) now connects words and grammatical forms to their native card inventory, with search, filters and a separate record of historical Anki exports.

Status: migration started on 8 September 2026. The Git/build baseline and [Stage 1 shared learning foundation](stage-1.md) are implemented. Household controls, content approval and persistent activity APIs now exist; the rebuilt `/post/` interface now uses the approved-choice activity APIs. The [native flashcards MVP](native-flashcards-mvp.md) now provides automatic card generation, individual editing and a durable FSRS reviewer. See [implementation progress and evidence](implementation-progress.md).

**9 September product correction:** the owner retains the visual design but rejects the preview's incoherent story, language and flow. Read the [experience review and migration correction](experience-review.md) first. It supersedes earlier claims that postal-world navigation and a mandatory adventure structure were approved requirements.

**Historical campaign direction, 9 September:** the [original campaign brief](barsik-journey.md) proposed coin-unlocked worlds and a final delivered-letter assessment. The current milestone contract supersedes that access model: assessment passes advance the guided course, and Barsik receives separate letters while keeping his original letter sealed. Coins now buy optional games. The passport remains removed.

The application helps individuals and households build, remember and use Russian vocabulary through flashcards, reading, sentence games and writing. Preserve those existing functional flows and apply the new visual system incrementally. Reliable persistence, independent study histories and optional content editing remain required. Barsik's delivery story will connect chapters while familiar activity choices remain directly accessible.

## Read in this order

Directions engine: [Implementation and operating details](procedural-directions-implementation.md) describe the current build, migration, preparation and limits. The [design document](procedural-directions-engine-design.md) explains the architecture and later extensions.

Current cleanup review: [activity audit and uplift recommendations](activity-audit.md) covers the running games, concrete save/load/display defects and a focused order before further story work. It is an audit, not a claim that its fixes are implemented.

Lesson integration proposal: [Lessons as a source of practice](lesson-driven-practice.md) maps the current annotated lesson to contextual flashcards, vocabulary capture, writing and conversation, with the existing implementation boundaries and a phased first build.

1. [Prioritised product backlog](product-backlog.md): current order, ease, existing game adaptations and new ideas.
2. [Native flashcards and Anki Link](native-flashcards.md): requirements for the first usable learning slice. [Anki-to-native migration](anki-to-native-migration.md) adds the 9 September code/data audit, interface flow and implementation gates.
3. [Levels and progression](levels-and-progression.md), [game shop](game-access.md) and [storage/hosting](storage-and-hosting.md): Lingocoins, skill estimates, permanent game purchases, local data and Fly.io preparation. [Shared progression](progression.md) retains the earlier design notes.
4. [Migration strategy](migration-strategy.md) and [technical architecture](technical-architecture.md): feature mapping, common data contracts and cutover.
5. [Design system](design-system.md), [delivery gates](delivery-plan.md) and [approved reference](reference/README.md): presentation, verification and preserved artwork.

For current setup, supported APIs and recovery, use the [Stage 1 operating guide](stage-1.md) and [native flashcards MVP guide](native-flashcards-mvp.md). The target documents include later capabilities and should not be read as an inventory of shipped features.

## Decisions and assumptions

| Decision | Status | Working recommendation | What changes if the answer differs |
|---|---|---|---|
| Visual design versus product flow | **Clarified by owner, 9 September 2026** | Retain illustration/theme/design elements; replace incoherent story and flow with recognisable learning tasks | Previous approval of postal navigation was an incorrect interpretation; replacement labels remain recommendations in the experience review |
| Barsik's story and welcome | **Approved by owner, 9 September 2026** | A small letter. A big adventure. Barsik delivers one letter to the learner through a continuous world journey | World names/scenes remain editable; ordinary activities stay directly available |
| World unlocks | **Superseded by the milestone course and game shop** | Assessment passes advance the current guided route; coins buy optional games | Historical coin-based journey receipts remain saved and do not establish proficiency |
| Final letter assessment | **Approved by owner, 9 September 2026** | Decipher the final Russian letter using practised vocabulary, with comprehension marking and saved results | Letter content, reading load and independent-pass threshold remain pilot proposals; independent and supported understanding are distinct |
| Google Drive and SQLite coexist | **Approved** | Multiple capture methods; structured library and learning records remain in SQLite | Do not consolidate away the mobile capture workflow |
| Remove dormant frontend/backend port | **Completed previously** | Continue from the active Flask app | Do not revive the abandoned Astro port |
| Individual flashcard workflow | **Corrected by owner, 9 September 2026** | Automatic generation from selected parameters, followed by study and optional edit/delete; individual use by default | Household roles, PINs and draft approval are opt-in; no compulsory manual authoring |
| First audience/deployment | **Reconfirmed by owner, 8 September 2026** | One household, local first; prepare storage for Fly.io later | Hosting has its own authentication, availability and restore gate |
| Native flashcards / Anki's role | **Expanded by owner, 8 September 2026** | Native flashcards and spaced repetition are the first usable learning slice; Anki Link is optional and reuses the existing generation/export capability | Supersedes the earlier exclusion of a native review scheduler from the first release |
| Word meanings | **Clarified by owner, 9 September 2026** | No universal English translation on a vocabulary row; each reviewed card owns its context, answer and nuance | Wrong or confusing cards can be corrected, discarded or retired without treating a content defect as failed recall |
| Existing Anki progress | **Confirmed by owner, 9 September 2026** | Start a separate native schedule; keep Anki untouched | Native content imports do not copy intervals, invent reviews or award coins; historical schedule migration is outside the first release |
| Existing games | **Confirmed; individual access clarified, 9 September 2026** | Adapt suitable activities for children and individual users; preparation remains available to the individual | Household restrictions are optional; legacy interface placement is not an audience restriction |
| Lingocoins and ELO | **Rewards/world-unlock direction approved; detailed policy proposed** | Shared participation rewards unlock the journey; later skill adaptation remains separate | Coin values and the skill model need refinement; coins are not assessment scores |
| Content publication | **Household policy retained; individual use clarified, 9 September 2026** | Optional household mode uses grown-up content approval; individual generation/editing does not | Version and validate campaign/assessment material without imposing a PIN or another person's approval on individual use |
| Age and reading ability | **Provisional** | Approximately 7–11; beginner Russian; English support | Ages 4–6 need substantially more audio and picture-led interaction; older children need different copy, pacing and content |
| Preserve existing capabilities | **Working assumption** | Keep existing tools available to individual users during migration | Removing features requires an explicit inventory decision, not omission during reskinning |
| Existing Drive reverse export | **Existing contract; future policy unresolved** | Preserve it until the owner chooses otherwise; make the policy visible | Recommend exploring separate capture input and optional managed library export; never silently change the current file's semantics |

The three architecture-shaping questions were answered during preparation of this plan. Age/reading ability and future Drive export policy remain explicit assumptions or unresolved refinements; neither prevents the prepared-adventure foundation. Confirm the intended age/reading range before producing the pilot content collection, and obtain an explicit export-policy decision before changing the current Drive file's behaviour.

## Recommended first implementation

The entry and approved-choice flow have been rebuilt under the [experience review](experience-review.md). The [MVP](native-flashcards-mvp.md) implements **one real native review flow** on the shared learner/content/attempt foundation, with automatically generated basic/cloze cards, per-learner FSRS state, save/resume, review history and safe undo. Its automated checks cover reloads, service restarts and repeated submissions with AI/Drive/Anki unavailable. Generate a small set from your vocabulary and pilot the flow, then connect the existing games to the same learning records and reward policy. Moon Picnic is no longer the default journey or a required migration slice. See the [current ordered backlog](product-backlog.md).

This slice must prove both useful interaction and reliable persistence. Incremental visual improvement of existing templates is supported; a full rewrite is not a prerequisite.

## What was done to establish this plan

- Re-examined the active routes, schema, frontend lifecycle, activity services, sync and existing operational documentation.
- Re-ran the isolated suite: **38 tests passed** on 8 September 2026. The expected failure-path logging in that run is not a suite failure.
- Read the canonical SQLite database without writing: quick integrity check passed and no foreign-key violations were reported.
- Preserved the owner-approved concept and original/optimized artwork in this repository, with checksums.
- Recorded [the baseline route inventory, counts and source fingerprints](baseline.json) so subsequent changes can be reconciled against an explicit snapshot.
- Checked relevant upstream guidance for the proposed tooling, job execution, SQLite, Drive and accessibility. Citations appear beside the relevant recommendations.

The original planning checkpoint did not implement those changes. Subsequent work is recorded separately in [implementation progress](implementation-progress.md).
