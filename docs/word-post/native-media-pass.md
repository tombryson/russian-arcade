# Native flashcards: first media and metadata migration pass

**Follow-up correction, 10 September:** the [Russian flashcard source audit](russian-flashcard-source-audit-2026-09-10.md) identifies unmet form-selection, grammar, contextual-meaning and required-media readiness requirements. This document records the delivered first pass; successful pilot media enrichment is not evidence that the full Russian learning workflow has been migrated.

10 September 2026 · branch `codex/native-flashcards-mvp`.

This pass brings the generated native cards closer to the existing Anki output. Generation remains automatic: choose the type and filters, then Generate. The five existing pilot cards are enriched in place, with their text, stable card identities and review schedules retained.

## Delivered

- Picture and Russian audio checkboxes are on by default in the generator. Word and example recordings are separate, with replay and 0.75×/1×/1.25× playback controls.
- Images use the existing OpenAI adapter; Russian recordings use the existing ElevenLabs adapter and the original random voice pool. Each recording chooses its voice independently, and retries retain that choice.
- Text, image, word audio and example audio are saved in separate stages. Generation can pause/resume; a media failure retains the card and other files. Retry operates on missing work, including a file saved before publication was interrupted.
- A dedicated illustration area, Russian example, answer and full example translation appear in the player. Recognition cards offer media on the front; Russian recall and cloze put the generated answer-bearing media on the back.
- Vocabulary/form links supply grammatical tags, all source topics, lemma/form difficulty and any existing mnemonic. Tags have readable English/Russian labels. Unknown source metadata remains unknown.
- The library filters by POS, case and difficulty alongside its existing search, topic, direction, state and collection filters. It sorts by due date, Russian alphabetic order or lexical difficulty. These sorts do not change the review queue or reschedule cards.
- Existing schema-2 native cards have **Add audio & picture**, **Resume media** or **Retry media** actions in the collection. Generated batch edit links point at the latest enriched version.

## Data and recovery

Migration **011** adds `native_card_media_jobs`; it does not rebuild the review tables. Each job records the card ID, media kind, input text, provider model, selected voice where applicable, creation time, status, lease, asset reference and a retryable error. Provider credentials are not copied into jobs.

Media bytes live in the existing content-addressed asset store. SQLite retains their IDs, checksums, byte sizes, MIME types and references. MP3 input is decoded and bounded to three minutes/10 MB; existing PNG/JPEG/WebP/WAV support remains. FFmpeg is required, as it already is for speech normalization. Neither native playback nor storage depends on an Anki media directory.

Adding support creates a new immutable content version with the same card ID and memory objective. Ungraded occurrences in active sessions can move to that richer version; session revisions change so stale commands are rejected. Graded occurrences, attempts, reviews and scheduling state remain pinned to their recorded versions. If the tested text is edited, the existing objective-replacement behavior still applies; recordings for the old wording are not carried into that replacement.

Saved media results survive a failure to attach/publish and are reused on retry. A running stage has a five-minute lease; a second request cannot start another media stage for the same card while the lease is active. A provider timeout before its result reaches local storage can still incur a second provider charge on retry; there is no cross-provider exactly-once guarantee.

## API and operations

| Entry | Behavior |
|---|---|
| Batch options `image` / `audio` | Optional booleans; the new UI enables both. Omitted flags retain the old text-only behavior for existing callers and batches. |
| `POST /api/v1/card-generation/batches/{id}/next` | Advance one text/media stage; return persisted progress. |
| `POST /api/v1/card-generation/batches/{id}/retry-media` | Requeue failed media stages only. |
| `POST /api/v1/flashcards/{id}/media` | Queue missing media for a native card and advance one stage. Send `{"retry":true}` once to retry failed stages; continue with `{}` until terminal. |
| `GET /api/v1/flashcards` | Adds metadata, assets, media status, `pos`, `case`, `difficulty` and `sort=due|alphabetical|difficulty`. |

Run the explicit database upgrade before restarting the application, then build the UI. Preserve the current `.env` files and their keys. No new keys were needed for the preview migration. The active text default is still **GPT-5.6 Luna, low reasoning**; enriching old cards does not regenerate their text.

## Preview verification

The preview on port **5052** now contains five generated pictures and ten Russian MP3 recordings for **что-то, вместе, юмор, зарплата, особенно**. All fifteen jobs completed successfully. The already saved user review and the scheduling/attempt/introduction tables were compared before and after enrichment; their contents were unchanged. The canonical database and Anki data were not modified.

The ignored runtime directory contains a full database-and-assets backup at `before-native-media-20260910-201522/`, the additive migration's database backup, and a dated `native-media-*.json` result receipt. These are operational artifacts, not fixtures to commit.

Deterministic tests cover stage failure/retry, preserved random voice selection, interrupted publication, restart between text and media, concurrent requests, MP3 validation, metadata filters, front/back media visibility, retained scheduling/history and current edit links. Browser checks cover the actual generated image and completed audio playback. The full UI suite passed; the updated backend migration expectation and media regressions passed. No synthetic ratings were submitted to the real collection.

## Still to migrate

The next pass should implement **Again / Hard / Good / Easy**, interval previews and the faster next-card/undo interaction. Then add active recall/answer timing, deck settings and useful statistics.

This pass does not complete the larger parity plan: reusable notes with several card variants, dictionary links, autoplay/image-side preferences, explicit media replacement, expanded generation provenance and stored duration, indexing/pagination, user tags, saved filters, collections/bulk operations, conversion of older schema-1 decks, import of existing Anki media and Anki Link export remain open. Older decks remain available to study, with no unsupported media-generation action. Library facets still use the existing in-memory projection and need indexed queries before a large collection. Hosted storage and sync remain later work.

See the [full parity plan](flashcard-parity-plan.md) for acceptance gates and ordering.

## Follow-up audit

The [focused audit](flashcard-audit-2026-09-10.md) records mobile usability and integration gaps, plus fixes for form resets, deleted/replaced cards blocking generation, historical versions inflating generation limits and unrelated startup dependencies.
