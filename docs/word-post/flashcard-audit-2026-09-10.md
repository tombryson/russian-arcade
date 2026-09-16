# Flashcard audit — 10 September 2026

Scope: the native generator, media jobs, library, reviewer and their connections to the home, tutorial and existing activities. This was a focused code, test and browser audit, including a 391 × 844 CSS-pixel viewport. No real cards were graded, regenerated or deleted for testing.

## Assessment

The storage and review foundations are sound for the local pilot. Automatic generation, independent native schedules, media persistence, retry, history and individual use are working. The experience is still incomplete: everyday review takes too many interactions, generation recovery is difficult to discover, and the application presents several different meanings of progress.

The existing suite passed before the audit, but new scenario tests exposed defects. Passing the existing tests alone was not sufficient evidence of completeness.

## Defects fixed in this audit

| Issue | Correction |
|---|---|
| Returning to the tab remounted the unfinished generator and silently reset the card type, quantity and filters. | Individual generation setup now retains its state on tab return. Optional household mode still refreshes access state. |
| Deleting a card while its media was pending made every subsequent batch advance fail, leaving other cards unfinished. | Deleted/replaced cards are skipped in batch progress and no longer block the remaining work. |
| An edited replacement left the old card eligible for attempted media generation, and old published versions inflated the generation cap. | Media requires a current card version; generation caps count current published cards. Historical versions remain intact. |
| Native flashcards depended on the unrelated activity catalogue and word-pocket requests just to open. | Native routes now load the profile and their own data without those two extra dependencies. |

The preview server was not listening when the audit began. It was restarted as a detached local process. This restores the preview, but is not a production service-management solution.

## Open findings, in priority order

| Priority | Finding and user impact | Recommended next change |
|---|---|---|
| P1 | **Mobile review is too tall.** On the existing revealed card, the rating controls start around 1,300 px down a page with an 844 px viewport. No horizontal overflow was found, but repeated scrolling makes a simple review cumbersome. | A compact mobile card face, concise replay controls and a persistent reveal/rating action area. Keep tags and playback settings secondary. |
| P1 | **Generation has no easily discoverable work history.** The page drives each request; leaving it stops subsequent stages. The batch URL can resume work, but the collection has no recent-batches view and pending text cards do not yet exist there. Text failures also lack an in-place retry. | Recent generation jobs with resume/retry, then a local worker independent of the open page. Keep successes and selected voices. |
| P1 | **The Anki-style reviewer is unfinished.** Two ratings, a compulsory feedback/Continue step, fixed five-new-card policy and no measured recall duration limit normal study. | Deliver four ratings and interval previews, immediate next-card/undo, then timing and personal scheduling settings. |
| P1 | **Progress and reward promises are inconsistent.** The tutorial teaches coin rewards, native flashcards award none, and existing games retain their own reward/progress paths. Barsik's journey does not yet reflect this study. | Define shared completion/progress events and honest reward copy before connecting coins, levels and the final letter. Self-reported recall must remain distinct from assessed answers. |
| P2 | **“Collections” exposes internal packaging.** Each generated card is currently a separate content pack, so the collection menu lists individual Russian words. | Introduce meaningful user collections/batches. Keep content-version containers out of the user-facing organisation model. |
| P2 | **Help restricts self-reporting.** Using a hint forces the current Again path rather than letting the individual choose a rating. | Record assistance separately and revise the rating policy explicitly alongside four-button review; preserve past scheduling evidence. |
| P2 | **Language and editing are inconsistent.** Native controls support English/Russian, while the card editor, much of the home/tutorial and topic labels still contain English-only copy. The editor exposes `[[blank]]` and manual form details, and has no direct edit-and-return-to-current-card flow. | Shared translated copy and navigation; a simple card preview/editor with advanced fields tucked away and a return-to-practice action. |
| P2 | **Error recovery still uses implementation language.** For example, a stopped server produced “Failed to fetch.” Missing media errors are generic and there is no clear provider/setup status for audio. | Human-readable loading/error states with a concrete recovery action; distinguish connection, configuration and generation failures. |
| P2 before scale | **Library queries still load and inspect the entire collection**, including per-card metadata/media/history lookups. Five cards do not test large-library performance. | Indexed facets, pagination, aggregated counts and performance fixtures before larger imports. |

## What works well

The shared vocabulary links and visual tokens provide a useful foundation for integration. Generation is automatic, individual use has no mandatory approval gate, and users can correct or set aside cards. The player distinguishes Russian prompts from English answers, provides separate recordings and example translations, and preserves historical reviews when support changes. The existing Anki tool remains accessible as an optional accessory.

The next release should concentrate on an efficient daily study loop and discoverable generation recovery. Additional story mechanics can then connect to a stable learning experience.

## Verification

Baseline: 199 backend tests and 59 UI tests passed. The audit added regression coverage for form retention, removed-card batch recovery, replacement media eligibility, current-card caps and removal of unrelated startup requests. Final validation: **201 backend tests and 60 UI tests passed**, TypeScript and the production UI build passed, and the home, Anki tools, vocabulary, reading, sentence-building, translation, writing and lessons pages all returned HTTP 200. The preview database integrity check passed; the five pilot cards, fifteen saved media jobs and existing review history were retained. Page-load checks do not establish full completion of every legacy activity or external-provider quality.

Related: [migration record](native-media-pass.md), [full parity plan](flashcard-parity-plan.md).
