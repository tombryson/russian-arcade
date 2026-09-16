# Foundation delivery — 8 September 2026

This implementation preserves the existing uncommitted stabilization/UI work and the deliberate Drive capture → SQLite learning-library workflow. It completes the foundation and initial sync reliability milestone, not the full frontend migration.

## Validation

- Fresh Python 3.12 environment installed from the complete dependency lock; dependency consistency check passed.
- 38 unit/integration tests passed with isolated fixture databases and no provider writes.
- All 11 route smoke checks passed against both a newly initialized demo database and the canonical database.
- Browser check with synthetic data and an in-memory Drive double: previewed captures, normalized/imported a word, exported existing library words, displayed pending enrichment, and refreshed the vocabulary table successfully.
- JavaScript syntax and Git whitespace checks passed.
- Migrations were first applied to a copy of the personal database. The canonical database was then upgraded to schema version 3 with all rows in its ten existing tables unchanged; integrity and foreign-key checks passed.
- The CI workflow is added but has not run on GitHub in this session. No live Drive, Anki, or AI provider write was performed.

## Preservation and Git state

The source/data/media backup made before implementation is:

`~/.local/share/russian_vocab/backups/20260908-185819-foundation`

The automatic pre-migration backup of the canonical database is:

`~/Projects/russian_vocab/flask_vocab_app/vocab.db.pre-migration-20260908-191908-993387.bak`

18,813 tracked runtime/personal artifacts were removed from Git's index. Every local file-presence check remained unchanged. The index removals are staged; source/documentation edits remain working-tree changes. No commit, push, or Git history rewrite was performed. Historical data in Git still requires separately coordinated credential/history cleanup.

## Remaining decisions and work

The current reverse export of SQLite-only words into Drive is preserved. SQLite history is never deleted because a Drive capture is removed. The frontend remains the working Flask interface. The subsequently requested removal of the dormant frontend/backend port is recorded in [retired port](retired-port.md), including archive recovery. See `roadmap.md` for revision-aware Drive writes, enrichment retries, activity persistence, and remaining interface/service/module cleanup.
