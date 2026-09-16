# Word Post delivery plan and migration risk register

Status: proposed backlog and release gates, 8 September 2026. Estimates are planning ranges for focused engineering effort, not promised calendar dates. Product choices, content review, child testing and hosting can change them substantially.

Implementation has started. See [current progress and evidence](implementation-progress.md) for the completed Git/restore checkpoint, WP-02 build and initial WP-03 catalogue. [Stage 1](stage-1.md) delivers the minimum WP-04/05/06 foundation, local assets and a tested shared reward ledger. It does not complete native review, connected child activities or G2–G4.

The owner expanded scope to native-first flashcards, shared child games, Lingocoins and Elo-style adaptation, and reconfirmed local-first/Fly.io preparation. **[Product backlog](product-backlog.md) is the authority for order and ease.** This document owns stable work-package IDs, dependencies and release gates; numerical IDs do not imply implementation order.

## 1. Work packages and dependencies

| ID | Deliverable | Depends on | Acceptance evidence |
|---|---|---|---|
| WP-00 | Record confirmed audience, Anki and publication decisions; refine reading support for the pilot | Core owner responses received; age refinement remains | Decision log updated; local-household scope, optional Anki and adult approval confirmed; age range checked before pilot content expansion |
| WP-01 | Recoverable baseline and migration inventory | Existing foundation | Source checkpoint reviewed; SQLite/media restore rehearsal; legacy ownership and route inventory |
| WP-02 | Vite/TypeScript build and Flask manifest integration | WP-01 | Reproducible lockfile install; production build served without Vite/CDNs; legacy tests pass |
| WP-03 | Tokens, local fonts/art and component catalogue | WP-02 | Home/letter/feedback/empty/error/resume states reviewed at target widths and both themes |
| WP-04 | Learner context and child/adult route policy | WP-00, WP-01 | Server-enforced access matrix including legacy URLs/assets; two-profile isolation tests; CSRF checks |
| WP-05 | Versioned starter cards/activities and publication validation | WP-00, WP-01 | Reviewed native starter deck first; existing game adaptations follow; Russian answers/variants, hints and assets validated; invalid packs rejected |
| WP-06 | Persistent learning-session/attempt service and API | WP-04, WP-05 | Reload/restart resume; idempotent submit; stale revision handling; atomic evidence and award |
| WP-07 | Approved practice in the shared interface | WP-03, WP-06 | Clear instruction → answer → correction → save → completion; keyboard/touch; provider-free completion |
| WP-08 | My words and saved practice | WP-06, WP-07 | Accurate empty states; hint-assisted evidence distinct; other learner unaffected; no passport or stamps |
| WP-09 | Durable job/execution and asset boundary | WP-01, relevant policy from WP-00 | Crash/reclaim/retry tests, stage progress, side-effect reconciliation and asset validation |
| WP-10 | Capture receipts, snapshot-aware preview and enrichment retry | WP-04, WP-09; Drive spike WP-S1 | Concurrent-edit behaviour demonstrated on disposable data; no lost capture in tested race; partial import recoverable |
| WP-11 | Adult content preparation/review/publish | WP-04, WP-05, WP-09 if AI is used | Draft cannot be reached from child API; publishing freezes version; withdrawal policy tested |
| WP-12 | Optional Anki Link and legacy-data adapters | WP-04, WP-09, WP-17 | Approved native versions export via reused adapters; remote note/card IDs preserved separately; ambiguous writes reconciled; existing history preserved |
| WP-13 | Shared child game adapters: a sentence modes, b story/listening, c creative jumble, d writing, e lesson play | WP-06, reviewed content through WP-05/11; WP-09 for provider work | Independent persisted attempts/feedback; preserve the existing mechanics and history; deterministic modes precede live-feedback dependencies |
| WP-14 | Small reviewed card/game collection and child pilot | WP-17, WP-07/08 and selected WP-13 modes | Observe review, help, resume, undo and game completion; address findings before expanding content |
| WP-15 | Default entry switch, operational docs and rollback window | Relevant parity gates + WP-14 | Old/new entry switches tested with expanded data; release assets retained; owner release acceptance |
| WP-16 | Remove unused legacy presentation and later schema cleanup | WP-15 + agreed observation/retention window | No consumers in route inventory/tests; old assets removed only after parity; separate recovery review for destructive schema work |
| WP-17 | Native flashcards and FSRS review | WP-03/04/05/06; local assets | Pass [FC-01–11 and native acceptance](native-flashcards.md); durable per-learner scheduling/history, safe undo and provider-free review. FC-12/export checks belong to the later WP-12. |
| WP-18 | Shared Lingocoin policy, ledger consumers and later cosmetics | Ledger foundation alongside WP-06; consumers after WP-17/13 | Concurrent retries/caps/spends consistent; Again/Good participation equal; no duplicate rewards across activities |
| WP-19 | Elo-style skill evidence and bounded adaptation | Comparable WP-17/13/20 evidence | Separate memory/reward/skill signals; shadow evaluation, sparse-data fallback and grown-up override |
| WP-20 | New games from shared content | WP-05/06 and relevant assets | Pairs/sort first; parcel/cloze/radio/detective later; each mode declares its evidence and grading policy |
| WP-21 | Asset storage interface and future Fly.io/Tigris release | Local adapter alongside WP-05/06; hosting after owner request and release gates | Stable IDs, private access, consistent media/DB restore, persistence through deployment; no live DB stored as a mutable object blob |

The critical path from the implemented build is **WP-04/05 → WP-06 → WP-17**, with minimal ledger/local-asset support included. WP-07/08 and the easier games then share that foundation. WP-10 is not a prerequisite for proving a prepared deck, but capture correctness is required before expanding/replacing adult sync. WP-11 can begin with a validated authored pack and an adult publication command; a full editor is not a prerequisite for native review.

### Time-boxed investigations

| ID | Investigation | Bound / decision produced |
|---|---|---|
| WP-S1 | Drive v3 text-media conditional update and concurrent phone-style edits, on a disposable file | 1–2 focused days; demonstrate expected conflict response or choose explicit import-only/separate-export fallback for owner decision |
| WP-S2 | Existing-story ownership, feedback ambiguity and legacy mapping | About 1 day on a copied database; publish a mapping report with unassignable records explicitly marked |
| WP-S3 | Queue implementation and crash recovery | 1–2 days; select a maintained local queue or minimal persistent executor against the same lease/idempotency tests |
| WP-S4 | Cyrillic typography, audio assets and target-device usability | First catalogue pass plus a real phone/child session; decide necessary text/audio support before multiplying content |

These investigations are planned; this documentation change did not perform live provider writes or a child usability study.

### Effort envelope

Use the S/M/L estimates and dependency assumptions in the [ordered backlog](product-backlog.md#ordered-backlog). The shared learning core and native reviewer are each initially L; small game adapters can become S once that foundation exists. Do not add the core cost to every game or assume a thin export UI includes all job/history migration work.

The earlier whole-programme estimate predates native scheduling, broader game progression and the storage preparation decision and is retired. Re-estimate the remaining programme after WP-17, with pilot/content review and any hosting work shown separately. These ranges are planning assumptions, not delivery promises.

## 2. Release gates

### G0 — Safe baseline

- The relevant regression suites pass; record the exact source state and test counts. The original baseline had 38 Python tests; the build foundation reached 45 Python and 4 UI tests, recorded in [implementation evidence](implementation-progress.md).
- Restore a copied canonical database and related assets; verify quick/integrity checks, foreign keys, counts and hashes of legacy rows selected for preservation.
- Record existing staged removals and their external archive independently from Word Post commits. No blanket add/reset/cleanup of the current working tree.
- Record data/profile attribution; new children must not inherit the existing user's rewards.

### G1 — Design and asset build

- CI builds the UI, resolves the manifest and serves a production page with external CDN traffic blocked.
- Component catalogue covers home, letter, hint, wrong/correct answer, audio states, save retry, empty pocket, completion and adult capture.
- Keyboard, 200% text zoom, 320px width, long Russian strings and reduced motion remain usable. Check the agreed performance budgets on a reference phone, not just desktop localhost.
- Approved artwork and necessary font licences are packaged; no host-only prototype helper or base64 asset bundle is required.

### G2 — Learning integrity

Apply these checks to both native review and adventure sessions. The [native acceptance suite](native-flashcards.md#acceptance-tests) additionally covers scheduler state, reveal/help, undo, related cards, queue limits, timezone boundaries and dependency upgrades. The [progression contract](progression.md) covers shared reward allowances and later spending. A working scheduler library alone does not satisfy G2.

- A saved step and its feedback survive a browser reload and server restart.
- Two concurrent copies of one submission produce one attempt and at most one award; same idempotency key with different content is rejected.
- A stale new submission from a second tab/device does not overwrite newer state. A retried already-committed submission returns its original result.
- Replaying an adventure records new practice without duplicating the first-completion stamp.
- Switching profiles does not reveal another learner's draft/answers/history, including through direct API/asset URLs.
- Word pocket reports recorded evidence; imported library entries alone do not appear as learned words.
- Manipulated task/score/reward payloads cannot define server outcomes; accepted Russian variants are tested.

### G3 — Integration reliability

- Add via app and import via Drive both create durable capture receipts with raw text and linkage.
- Failed enrichment/export retains successful library import; a retry works without re-importing or duplicating forms.
- A mobile edit after preview invalidates stale destructive approval. The actual upload-race test proves conditional conflict handling or the selected fallback avoids rewriting the capture file.
- Worker restart reclaims abandoned jobs; duplicate execution preserves local uniqueness; ambiguous external side effects are reconciled.
- Read/attempt/complete a prepared child adventure with Drive/AI/Anki unavailable. No technical provider error leaks into child copy.

### G4 — Pilot and cutover

- Children in the agreed range can identify how to start, use a hint, recover from a wrong answer and finish. Record observations and fix blocking findings; do not infer learning efficacy from enthusiasm alone.
- Adult feature parity is recorded per route group: migrated, retained in legacy, deliberately deferred or retired by owner decision.
- No open blocker involving lost data, wrong-learner data, lost captures, duplicate achievements or unreviewed content exposure remains.
- Rehearse the new-entry disable switch while preserving new session records; rehearse asset/manifest rollback.
- Parent/learner guidance, setup, provider failure recovery, backup/restore and deployment documents match the release.

## 3. Largest migration risks

Likelihood below is qualitative engineering judgement based on the current code and proposed scope, not a measured probability. Severity and detection evidence determine priority.

| Risk | Likelihood / impact | Mitigation | Evidence / rollback response |
|---|---|---|---|
| Lost vocabulary, forms or historical data during schema changes | Medium / critical | Additive migrations, explicit legacy ID mapping, copied-data rehearsal, full backup and row reconciliation | Any unexplained row/ID difference blocks upgrade; stop writes and follow pre/post-write recovery distinction |
| One child's answers/progress leak into another profile | High without redesign / critical | Separate content from attempts; server-authorised profile context; adult-only legacy routes | Cross-profile route/asset tests; disable affected child route and investigate before resuming |
| Repeated taps/retries create duplicate stamps or provider work | High / high | Unique operation IDs, payload hashes, atomic completion, at-least-once job reconciliation | Concurrent submit/crash tests; retain records, repair duplicates with audit rather than erasing all progress |
| Two frontends fight over DOM/state or Bootstrap leaks into Word Post | High if blended / high | Separate entry points/base templates; one owner per subtree; full navigation across boundaries | Mixed-navigation and remount tests; feature-switch back while keeping data |
| Polished appearance masks incomplete learning/persistence | High / high | Gate on one real save/resume/finish slice before broad reskin | Restart midway and reconcile actual attempts; do not switch default when only visual checks pass |
| Drive edits overwritten by preview/apply/export races | Known residual issue / critical | Snapshot receipts, conditional-write spike, shared writer adapter, explicit safe fallback | Disposable concurrent writer tests; stop rewriting original capture file on conflict; retain library imports |
| Provider delay/outage/cost blocks children | High during live generation / high | Prepared published assets, adult drafting jobs, deadlines, fallback pack and budget controls | Simulate 429/timeouts/malformed output; child prepared flow must still finish |
| Incorrect or unsuitable generated content reaches children | Material / high | Versioned validation and adult publication; reviewed answer variants/pronunciation | Invalid/unapproved pack cannot be fetched by child API; withdraw version without deleting attempt history |
| Legacy HTML interpolation becomes exposed under new routes | Material / high | Structured payloads, escaping, markup allowlist, CSRF and route policy | Security regression tests and provider-output fixtures; block publication/route on unresolved injection paths |
| Original visual identity disappears in implementation | High / medium-high | Preserve approved art/reference/tokens; review complete states, not only components in isolation | Visual comparison at G1/G4; revise component composition before expanding it |
| Child reading/touch needs differ from assumed age band | Medium / high | Confirm audience, audio/support preferences, short instructions, real-device observation | WP-S4/pilot findings; adjust content and interaction before catalogue expansion |
| File/media paths or expired remote URLs break after release | Medium / high | Asset registry, stable IDs, stored media, release manifest, private/public policy | Broken-asset audit and restore rehearsal; recover from source asset bundle/backup |
| Hosted requirements are discovered late | Medium / high | Audience decision before identity implementation; local pilot explicitly scoped | If hosted/schools selected, revise WP-04/deployment and estimate before release |
| Migration remains indefinitely split across old/new systems | Medium / high | Named owners, route parity ledger, flag removal criteria and retirement milestone | G4 inventory; no new features added to retired presentation paths without a reason |
| Rollback restores an old backup over new learning | Medium / critical | Separate application rollback from data restore; retain expanded schema and post-cutover delta | Post-write rollback drill preserves attempts/captures; any destructive restore requires a reconciliation plan |

Implementation owners should be assigned when work is scheduled: application/data engineer for data and access, UI engineer for presentation/state, content reviewer for language/audience, and product owner for scope and release acceptance. One person may hold several roles; each gate still needs explicit evidence.

## 4. Verification strategy

Keep the existing isolated Python tests. Add tests at the boundary where a failure would matter:

- **Migrations:** populated compatible fixture, incompatible schema, preservation of IDs and history, repeat migration, interrupted backfill and restore. Do not use the user's live database as a writable fixture.
- **Domain:** published-version immutability, legal session transitions, hint evidence, supported answer variants, exactly one first-completion award.
- **API:** ownership/permissions, CSRF, malformed/oversized payloads, concurrency, stale revisions and idempotency reuse.
- **Jobs/integrations:** lease expiry, partial completion, ambiguous provider result, retry exhaustion, revoked connection and fresh/stale Drive snapshots.
- **UI components:** meaningful interactions such as sentence rearrangement, focus after step change, saved/error feedback and audio-unavailable behaviour.
- **Browser:** complete an approved activity; reload/resume; fail a save then retry; learner switch; offline provider; adult capture preview/conflict/retry. Run Chromium and WebKit where supported, plus real mobile Safari checks for audio/touch.
- **Visual/accessibility:** representative states at the agreed widths/themes; keyboard/VoiceOver and reduced motion; automated audits supplement manual checks.

Use a frontend lockfile and scripts for typecheck, component tests, production build and browser checks. CI should boot an isolated Flask instance with fake integrations and synthetic reviewed content. The frontend build must be tested in its production form, not only under Vite's development server.

Do not write snapshot tests for every markup detail or mirror implementation functions without a behavioural assertion. Version important visual snapshots, and require explanation for reference changes.

## 5. Operational measurements

Begin with small, first-party, privacy-conscious operational counters: session start/finish/resume success, save failure, duplicate request replay, API latency, job queue age/retries, provider cost/error class, Drive conflict and asset missing. Associate support diagnostics with opaque IDs; exclude raw child writing, full prompts and tokens from normal logs.

Use measurements to identify broken flows, not rank children. No third-party behavioural tracking is necessary for the initial release. A pilot can use adult observation and consented notes without collecting detailed permanent click streams.

Release thresholds: zero known data-loss/wrong-learner/duplicate-award defects; all mandatory workflow checks green; no unexplained migration reconciliation differences. Latency and weight numbers in the design system are proposed budgets to validate, not measured current performance.

## 6. Documentation and retirement obligations

Each completed work package updates architecture, commands, configuration, migration/recovery notes and user-facing help together. Keep a short change log for publication policy, scoring, normalisation and sync rules because they affect existing data interpretation.

Before final presentation retirement, search remaining template/script/route consumers; remove the obsolete global shell, CDN imports and Bootstrap only when no supported page uses them. Keep historical code in Git history or the existing archive, not active duplicate application folders.

Database contraction, credential rotation/history remediation, public hosting and broad mobile distribution have their own operational consequences. Schedule them explicitly; do not hide them inside a visual-refresh pull request.
