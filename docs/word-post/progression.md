# Shared progression: Lingocoins, memory and Elo-style difficulty

> **Current implementation (17 September 2026):** [Practice levels, shared coins and Barsik’s journey](levels-and-progression.md) records the current progression policy. [Game access](game-access.md) records shop purchases: 25 Lingocoins for the first paid game, then 50 each. Review rewards, compensating undo and permanent purchases are implemented. The design notes below preserve earlier proposals and are not the current release contract.
Status: owner requested progression across activities, 8 September 2026. Mechanisms below are proposed product policies. They are not a claim of measured proficiency or implemented rewards in the Word Post preview.

Implementation update: [Stage 1](stage-1.md) now implements the activity participation policy in the shared backend ledger, using the provisional 3-per-activity / 12-per-day values. The [native MVP](native-flashcards-mvp.md) now stores FSRS reviews and self-reported/supported word evidence. It does not write coin rewards or Elo. Native review rewards, configurable economy, spending and Elo adaptation remain later work.

**Approved 9 September refinement:** eligible Lingocoins earned across practice unlock worlds on Barsik's route; spending does not reduce that earned-progress total or relock worlds. The journey ends with an exam-style letter comprehension challenge based on practised language. [The canonical campaign brief](barsik-journey.md) defines these requirements. Reward values, thresholds and grading calibration remain proposals. Unlocks and the final assessment are not implemented by the welcome hero.

The first-delivery tutorial now explains the current learner participation rules and demonstrates answer/hint controls. It awards no coins and displays no invented balance. Its copy must stay consistent with the versioned backend policy if those amounts or eligibility rules change. A replayable interface tutorial is not a qualifying learning session.

**17 September 2026 update:** optional games are chosen in Barsik’s shop and bought from the visible Lingocoin balance. Introductory lessons and automatic coin milestones do not grant games. Existing ownership is preserved. Spending does not reduce journey earnings or provisional skill ratings. See [game access](game-access.md) for the current policy.

## Current evidence and what changes

The current [user service](../../flask_vocab_app/services/user_service.py) awards `marks * 10` coins and updates one `elo_rating` with an expected score fixed at `0.5`, multiplied by difficulty. It does not estimate the probability of success from learner ability versus item difficulty. Score scales differ across activities, so extending that formula would create inconsistent rewards.

The sentence path has a uniquely keyed [reward ledger](../../flask_vocab_app/migrations/003_reward_events.sql). Other paths do not all use that same atomic mechanism: story reward marking is separate, and several writing/lesson/jumble paths do not apply common rewards. The initial word-jumble score/display mismatch was corrected in the [9 September activity uplift](activity-audit.md); this does not unify the legacy reward paths. Preserve old totals as legacy history; new learner profiles start with explicit new state.

## Separate kinds of progress

| Mechanism | Question answered | Scope |
|---|---|---|
| FSRS | When should this learner recall this particular item again? | Per learner/card; defined recall events |
| Elo-style adaptation | Which challenge is an appropriate next step? | Per skill/task family; comparable outcomes and item difficulty |
| Lingocoins | What has practice earned, and which world is available next? | Auditable participation rewards; earned total for world unlocks, spendable balance kept separately |
| Journey position | Where is Barsik on this learner's route? | Saved available worlds and completed scenes; individual control by default |
| Final-letter assessment | How much of this practised language can the learner understand in a new message? | Per-attempt comprehension results, with independent answers and support recorded separately |

Seeing an image, reading a story, matching a word, typing a word and recalling it without help create different evidence. A shared event format connects them without treating all successes as interchangeable.

A chapter completion advances the story; total eligible earned coins unlock available destinations. Coin spending, clearing due reviews and Elo estimates do not determine these unlocks. Coins alone do not prove vocabulary coverage or comprehension. The final letter uses covered language and its own assessment rubric. Ordinary practice remains available outside the journey. Persist an unlock once earned; cosmetic spending or subsequent reward corrections do not silently relock it.

## Lingocoins: first policy

Reward completed, server-issued practice, including honest mistakes and help use. In native flashcards, Again and Good earn the **same participation reward** when the event is eligible. Otherwise the interface rewards saying “I remembered” regardless of recall. Imported/generated words, clicking reveal repeatedly and passive page views do not earn coins.

Proposed pilot amounts, held in a versioned policy and adjustable after observation:

| Eligible event | Proposed award | Bound |
|---|---|---|
| Completed review of a distinct issued card | 1 coin | Once per learner/card/study day; up to 10 review coins that day. Relearning still works after the allowance is used. |
| Completed small game/reading/writing activity | 3 coins | Once per learner/published activity/study day; up to 12 game coins that day. Content re-publication does not reset the stable activity key. |

These values are a starting proposal, not an approved economy or an effectiveness claim. Expose any eventual configurable limits to the individual; optional household mode can manage its own policy. Keep practice and its rewards understandable. Limits suppress repeated rewards, not access to learning.

First UI: an actual earned total, “earned from this practice” feedback, readable history and progress towards the next available world. World unlocks are now the first campaign use of coins; envelope colours or postbag decoration can follow. Ordinary practice, hints and pronunciation remain accessible outside campaign progression. Exact thresholds must be calibrated against the real earning policy before display.

## Reward integrity requirements

- All activity types call one policy service. Every ledger entry references the learner, accepted attempt/milestone, policy version and a stable eligibility key.
- Eligibility, daily cap consumption, ledger insertion and balance projection update in one database transaction. Concurrent sessions cannot each claim the last allowance.
- New review attempts may occur repeatedly; reward uniqueness is deliberately broader than submission uniqueness. Replaying a previously committed submission returns its earlier result.
- A server-issued activity defines required steps. Merely sending “completed” from the browser is insufficient. Provider timeouts or unassessed free text must not become fake “correct” results.
- A short writing submission can earn participation when saved and structurally complete, while its skill assessment remains pending. Cosmetic rewards must not depend on an unpredictable live AI grade.
- Spending later uses the same ledger with an atomic balance check and purchase key; no negative balance or duplicate purchase under retries. Earn/spend reversal retains an audit trail and reconciles dependent items.
- Rewards derived from a review/game event are routed once; embedding a reviewed card inside an adventure cannot mint a second reward for the same qualifying event.
- Legacy totals are labelled and mapped explicitly. Do not copy the existing adult balance/ELO to every new child.

The [native migration plan](anki-to-native-migration.md#6-rewards-assets-and-anki-boundaries) adds a concrete prerequisite for review rewards: an entitlement/claim record separate from ledger operation keys. The existing unique eligibility key cannot hold both an award and its compensation. Prove undo, net daily caps and re-review behaviour before activating review coins. The core reviewer may ship first with no promised review reward. Imported Anki content creates neither native history nor coins; the owner chose a separate native schedule.

## Final-letter evidence

Use the [final-letter contract](barsik-journey.md#5-the-final-letter-an-assessment-with-a-story-payoff): covered vocabulary/forms/patterns, a pinned letter and rubric, accepted meanings, saved first answers and per-question support. Reading comprehension does not automatically update every mentioned card's FSRS state or become a global Elo score. Completing the physical delivery, understanding the letter with help and passing independently are separate outcomes. Retrying preserves earlier results and cannot repeatedly issue a first-completion reward.

## Elo-style adaptation: preserve the idea, rebuild the calculation

Use adaptation to select helpful challenges. Child-facing language can be “Ready for a new challenge”; grown-ups can inspect practice patterns and evidence coverage. A single number should not imply a CEFR level or rank children.

Start with separate areas such as word recognition, word recall, listening, sentence meaning and sentence construction. Keep creative writing distinct while its rubric is being developed. Activity difficulty is a reviewed starting estimate; a five-level topic label is not calibrated item difficulty.

A candidate later model compares learner skill with an item's difficulty, e.g. a logistic expected-success function and a bounded update proportional to observed minus expected success. Record model version, evidence count and uncertainty/provisional status. Elo-inspired educational models exist, including work on multiple concepts; that supports an investigation, not a claim that our household data is sufficient to calibrate one. [Multivariate Elo learner-model research](https://arxiv.org/abs/1910.12581).

Implementation sequence:

1. **Collect clean evidence now.** Save skill tags, task/version, supported versus independent attempt, rubric, item exposure and trustworthy outcome. Self-reported flashcard recall remains memory evidence; it is not an objective cross-game skill score.
2. **Use authored levels initially.** Grown-ups can choose easier/harder material. With little evidence, show “still learning about your practice” instead of a precise rating.
3. **Run a shadow model.** Calculate suggested difficulty without changing what the learner sees. Inspect predictions against later independent attempts and compare with a simple baseline.
4. **Enable bounded adaptation after review.** Limit level jumps, permit overrides and continue offering familiar successes. Keep uncertain or incomparable outcomes out of the update.

For a single household, learning ability and item difficulty are difficult to estimate jointly from sparse data. Begin with reviewer-set item difficulty and conservative learner updates; do not fit both freely from a handful of answers. Model choice, learning rates and readiness thresholds belong to the investigation and should not be invented from the legacy `1000` starting rating.

Assisted completion, repeated exposure after revealing an answer, skips and provider failures must have explicit policies. Do not turn an AI writing score out of 100 into the same Elo signal as a deterministic matching answer. New tasks should be compared within a stable objective/rubric. An uncertain model or absent data must leave the activity usable.

## Game integration contract

Each adapter supplies a published definition, required completion steps, a grading policy and evidence tags. The shared learning service persists the attempt, then eligible consumers produce word evidence, coins, milestones and (later) skill updates. FSRS updates only for a linked, qualified recall review.

Examples: Postcard Pairs produces recognition evidence and participation coins; Story Mail produces comprehension evidence and a saved completion record; Mailbag Mix can save a creative response and award bounded participation while feedback awaits review. A postcard that genuinely asks for independent recall can update FSRS through the common review contract.

Acceptance checks include concurrent cap/purchase attempts, retry replay, undo/reversal, new-profile isolation, no duplicate reward when activities are combined, stable caps over timezone changes, consistent scales, and a disabled/uncertain adaptation model that leaves learning functional.
