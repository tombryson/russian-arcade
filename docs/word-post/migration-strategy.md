# Word Post migration strategy

Date: 8 September 2026. Status: proposed implementation strategy for the approved design. The owner confirmed local-household deployment first, optional grown-up Anki and adult approval of content. Remaining assumptions are recorded in [the programme index](README.md).

**9 September correction:** the [experience review](experience-review.md) supersedes mandatory adventure flows and postal feature names in this original strategy. Preserve functional continuity with the existing app, apply the visual system incrementally, and validate a clear complete task. Stage 1 infrastructure remains useful; the preview's product model does not define the target.

Scope revised after the owner prioritised native flashcards and shared child games. The [product backlog](product-backlog.md) owns execution order and ease estimates; [native review requirements](native-flashcards.md) supersede the earlier scheduler-later recommendation. Fly.io preparation is included while delivery remains local first.

## 1. Recommendation

Evolve the current application into a **single Flask application with a shared design system and learning services**, separating material preparation from learner practice:

- **Learner practice:** retain useful existing flows; use Preact/TypeScript built with Vite for interactions that benefit from it, consuming the versioned Flask API. Serving children does not by itself require rewriting a whole page in Preact.
- **Grown-up workspace:** Jinja/HTMX forms and library tools, migrated into the same visual system at a calmer density.
- **Shared application services:** content publication, learner sessions, attempts, vocabulary capture, sync, assets and jobs.
- **SQLite initially:** one local household installation, explicit additive migrations, short transactions and a durable worker for provider work when needed.

Keep ordinary document navigation where appropriate. Within a Preact activity, one controller owns the interactive state. Do not allow HTMX and Preact to manipulate the same DOM subtree.

This is a stronger boundary than the current mixture of DOM listeners, HTMX fragments and small Preact wrappers. It retains the useful Python integration code while giving the child experience a coherent interaction model. Vite explicitly supports backend-rendered applications through build manifests; it does not require a separate production frontend server. [Vite backend integration](https://vite.dev/guide/backend-integration). Preact also supports Vite and incremental integration. [Preact getting started](https://preactjs.com/guide/v10/getting-started/).

### Alternatives considered

| Approach | Benefit | Cost/risk | Decision |
|---|---|---|---|
| Incrementally restyle existing templates and integrate shared services | Fast visible value while preserving useful tasks and routes | Styling alone cannot resolve persistence, learner isolation or assessment inconsistencies | **Supported migration path**; combine visual improvements with the relevant service adapters |
| Flask + bounded Preact child app + HTMX grown-up tools | Reuses backend, supports rich interactions and gradual replacement | Requires explicit frontend ownership and a small asset build | **Recommended** |
| Rewrite everything as a React/Next or similar separate application | One frontend model and broad ecosystem | New deployment/auth/data contracts while also changing learning semantics; substantial parity risk | Reconsider only when a demonstrated requirement warrants it |
| Revive the archived Astro port | Some old exploratory code exists | It was incomplete and has already been retired; it does not implement Word Post | Do not revive |
| Introduce a game engine/canvas for the whole interface | Advanced animation and spatial scenes | Text accessibility, responsive layout, testing and ordinary forms become harder | Use HTML/CSS and illustrations; a later isolated game can justify a specialised engine |

## 2. What we are migrating

The earlier foundation work is valuable: the app factory, lazy/injectable services, Python 3.12 lock, explicit migrations, temporary-database tests, connection policy, safer sync and sentence reward ledger should remain.

The following is a **local snapshot**, not a claim about a deployed product:

| Evidence, 8 September 2026 | Migration consequence |
|---|---|
| 47 explicitly declared routes across `app.py` and five blueprints, including two configured asset routes | Inventory route behaviour before retiring URLs; account for both HTML and JSON consumers |
| `app.py`: 399 lines; `app_shell.js`: 796; shared CSS: 671 | Extract responsibility as features migrate; avoid an unrelated all-at-once file reorganisation |
| CDN Bootstrap 5.3.0, HTMX 1.9.6, Preact 10.19.3; no current frontend build manifest | Introduce a reproducible asset build before scaling the new interface |
| 1,233 words, 16,049 forms, 192 Anki mapping rows | Preserve IDs, inflections and external card mappings; the UI's 117-card statistic is a different measure and must not be treated as this row count |
| 8 stories, 2 writing exercises, 5 uploaded lessons, 6 jumble games, 21 sentences | Keep historical content accessible; do not mark it child-ready or newly completed without review/evidence |
| One legacy user; 21 legacy reward events; three applied migrations | Preserve legacy totals; create clean learner state for actual new children |
| 38 isolated tests pass; SQLite quick check and foreign-key check pass | This is the baseline to maintain, not coverage of all new child workflows |

Source: [app factory/routes](../../flask_vocab_app/app.py), [baseline schema](../../flask_vocab_app/migrations/001_baseline.sql), [shell](../../flask_vocab_app/static/js/app_shell.js), [base template](../../flask_vocab_app/templates/base.html), [test support](../../flask_vocab_app/tests/support.py).

### Structural gaps that the new experience exposes

1. **Content and response data are mixed.** A saved story carries answers, feedback and score; lesson responses live inside JSON. A single content item cannot safely stand in for several children's independent attempts.
2. **User identity is frequently hard-coded to `1`.** Hiding the old navigation does not provide child/adult permissions or learner isolation.
3. **The browser and session carry important activity context.** Several requests submit base64-encoded prompts/questions. A production client should reference a server-owned activity version and submit an answer, not define its own assessed task.
4. **Generation and assessment occur during requests.** Text, image and audio operations can make a child wait; partial success has no general durable retry mechanism.
5. **The current learning model is adult-oriented.** Writing starts at 50 words and uses a 30-minute countdown. Topic filters and difficulty bands are not an age-appropriate curriculum or proficiency assessment.
6. **Sync still rewrites one mutable text file.** Fresh reads have reduced stale-cache overwrites; simultaneous edits and stale sanitisation previews remain unresolved.
7. **Rendering is not uniformly safe or self-contained.** Some responses interpolate provider feedback into HTML; runtime assets come from CDNs; modal/state cleanup is distributed across listeners.

Source: [writing service](../../flask_vocab_app/services/writing_service.py), historical writing timer (removed; [current writing interface](../../flask_vocab_app/static/js/writing_tools.js)), [comprehension routes](../../flask_vocab_app/blueprints/comprehension.py), [lesson marking](../../flask_vocab_app/app.py), [sync contract](../synchronization.md). These findings are based on code inspection; this planning work did not exploit production inputs.

## 3. Product boundary and feature destination

Use recognisable task names and clear instructions to make the next action understandable. A learner should not need fictional lore, database knowledge or provider terminology to practise. The destination labels below are historical feature mappings; use the experience review's literal activity names when implementing them.

| Current capability/routes | Destination | Migration treatment |
|---|---|---|
| `/` flashcard generator; `/generate`; `/generate_word_forms` | Grown-ups → Prepare native cards; optional Anki Link | Save/approve card versions before export; retain provider/formatting capability and IDs; native review runs in Word Post |
| `/review_cards`; `/user/stats`; `/metrics` | Grown-ups → Review activity / legacy progress | Label the existing action accurately; do not turn legacy ELO/coins/card coverage into child mastery |
| `/comprehension`, answer/save/load/more-questions | Letters and reading activities | Adapt reviewed story content into versioned adventures; create independent learner attempts |
| `/writing`, generate/assess/save/load | Short replies within adventures; longer writing in grown-up practice | Add age-appropriate templates, persist feedback, remove mandatory countdown from the child path |
| `/word_jumble`, create/load/mark | Mailbag Mix creative sentence activity | Preserve composing a sentence from supplied words; add scaffolding and a reviewed feedback policy. Tile rearrangement is a separate, simpler Sentence Post mode. |
| `/sentences`, generate/assess/add/save/saved | Phrase activities; adult sentence library | Preserve legacy records/rewards; new completion belongs to a learner session |
| `/lessons`, create/load/generate/mark | Grown-up material preparation; child Lesson Expeditions | Keep imports and publish reviewed activities for children; separate private source files from the play experience |
| `/vocab`, `/word-details/<lemma>` | Adult library and child Word pocket | Shared lexical records; separate per-learner evidence and approved visibility |
| Add/edit/delete word; add-vocab; sync/preview/history; sanitisation | Grown-ups → Capture and connections | Multiple entry paths retained; snapshot-aware sync and explicit destructive maintenance |
| `/ui-language` | Grown-up preferences and learner support settings | Separate interface language, learning language, hint language and reading support |
| Configured media/upload routes | Managed assets, with protected private uploads | Public app illustration assets and private lesson/learner material get different access policies |

“Preserve” means keep behaviour/data accessible until a replacement passes its checks. The games' current placement in the legacy workspace does not make them adult-only; preparation, provider controls and maintenance remain grown-up responsibilities.

## 4. Migration sequence

### Phase 0 — Baseline and decisions

Record the approved design and the now-confirmed first-release audience, Anki role and publication policy; verify a recoverable source/data/media baseline. Review the large existing staged cleanup separately from new Word Post work. Record which legacy content belongs to the existing user and which content may be reviewed for children.

**Exit:** agreed release scope, feature inventory, backup/restore evidence and a small approved learning-content sample. Source checkpoint and restore rehearsal have now been performed; see [implementation evidence](implementation-progress.md). New learner attribution and starter content approval remain part of the learning foundation.

### Phase 1 — Build and design foundation

Introduce Vite, TypeScript and a lockfile under the active application's UI directory. Produce manifest-based assets served by Flask. Add a Word Post component catalogue with the approved illustration, navigation, letter, word tile, hint, completion, audio and error states. Introduce the `/post/` entry without changing `/`.

**Exit:** production build runs without CDN access or the Vite development server; layouts work at small phone, tablet and desktop widths; the legacy route suite remains green; component states are visually reviewed against the approved reference.

### Phase 2 — Shared learning core and native review

Add the learner context, approved card/content versions, sessions, attempts, local asset IDs and atomic ledger needed for a small native deck. Implement basic/cloze cards, reveal, Again/Good, FSRS state, due/new queue policy, resume, review history and safe undo. Keep activity evidence extensible so Moon Picnic and other games use the same records.

**Exit:** a reviewed starter deck survives reload/restart and supports safe undo; concurrent retries do not duplicate reviews or rewards; profiles remain isolated; AI/Drive/Anki can be unavailable. Pass the [native acceptance tests](native-flashcards.md#acceptance-tests).

### Phase 3 — Shared games and progression

Connect Lingocoins, Sentence Post/Moon Picnic, simple matching/sorting and reviewed story activities to the same learner/attempt services. Reuse the prepared vocabulary and media instead of building isolated content stores. Separate skill evidence from participation rewards and recall scheduling. Preserve the approved visual world while keeping literal game instructions clear.

**Exit:** a learner can review words and play several activities without losing history, duplicating coins or conflating helped and independent outcomes. Story/question content is approved and previous users' answers remain private. Short, deterministic modes work without provider calls.

### Phase 4 — Integration, deeper activities and pilot

Add optional Anki Link, durable drafting/export/feedback operations and reliable capture receipts/retry. Migrate Drive writers through the same snapshot-aware boundary and investigate concurrent edits before expanding writes. Adapt the existing creative word jumble, short writing and lesson play; adults prepare/review material and feedback. Collect comparable evidence before enabling Elo-style difficulty selection. Pilot with the intended age/reading range and an adult present. These tracks follow dependencies in the product backlog; known capture correctness work remains a separate high-priority obligation.

**Exit:** completed/resumed activities and source data reconcile; children can start, get help and finish; adult tools retain required functions; accessibility, latency and error-state checks pass. Adjust the design where observation shows a problem without losing its visual identity.

### Phase 5 — Default switch and retirement

Use a feature switch to make Word Post the default only after the pilot gate. Keep an adult-accessible legacy route for one agreed rollback window. Move obsolete URLs to safe GET redirects or explicit compatibility handlers; never redirect a state-changing POST blindly. Remove unused JS, templates and Bootstrap only after their final consumers have moved.

**Exit:** no necessary legacy consumer remains, rollback drill is complete, operating/learner/parent documentation is current, and the owner accepts the release. Destructive schema cleanup belongs in a later release after retention and recovery requirements are satisfied.

## 5. Coexistence rules

- Initially `/` remains the current app; `/post/` is the new child entry; `/grownups/` is the adult entry. Names are proposed, not routes added by this plan.
- Keep separate HTML base templates and separate asset entry points. Bootstrap and `app_shell.js` are never loaded into the Word Post page.
- Navigation between old/new experiences is a full page load while they coexist. This removes shared global-listener and CSS-cascade surprises.
- Both surfaces use the same authoritative domain services for migrated operations. Avoid writing the same new attempt into two competing stores.
- Before introducing multiple active learners, route legacy access through an adult/legacy context. Legacy handlers that hard-code user `1` must never run as if they represented the selected child.
- Make flags server-controlled and test enabled/disabled states. Flags route experiences; they do not grant access. A hidden link is not an authorisation rule.
- Legacy data may be read through adapters. Write new progress only to the new attempt model; backfill legacy history with provenance and an explicit mapping report.

## 6. Rollback without losing new learning

Use additive tables and nullable/sidecar associations first. Do not rename/drop old tables or regenerate word IDs during the initial migration.

There are two different rollback cases:

1. **Before new production writes:** stop writers, restore the validated pre-migration database/media baseline and run its compatible application release if necessary.
2. **After children have used Word Post:** first stop the affected new writes, switch entry points back to the compatible experience, and retain the expanded database and new attempt records. Fix forward or use a tested compatible application version. Restoring an old backup at this point would lose later learning and captures; preserve and reconcile that delta before any such restoration.

Rehearse asset rollback too: keep the old release's hashed assets and manifest, not just its Python code. Backups must include private media, published content versions and asset metadata. Drive state and external Anki state cannot be rolled back merely by restoring SQLite.

## 7. What constitutes a successful migration

- The approved design survives implementation: original art, typographic hierarchy, postal objects, intentional motion and short child-oriented copy.
- A child can start, resume and finish a learning activity without managing integrations or waiting for a provider to invent the next screen.
- Each attempt/award belongs to the correct learner, content version and activity; repeated network delivery does not create repeated achievements.
- Existing lexical IDs, inflections, history and Anki mappings remain explainable and recoverable.
- Drive capture is preserved, with conflicts and pending work visible to the adult.
- The project has a repeatable build, documented release/rollback process, reference components and meaningful workflow tests.

The first production goal is a coherent, reliable learning loop, including native review through a maintained spaced-repetition library. A full native mobile application, public family hosting, a bespoke scheduling algorithm, classroom management and offline multi-device editing are separate scope decisions.
