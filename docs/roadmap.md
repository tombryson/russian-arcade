# Roadmap

> Latest integrated release: [Speaking practice levels, shared coins and Barsik’s journey](word-post/levels-and-progression.md) (15 September 2026).
## Implemented foundation

- Independent Flask application factory and injectable services.
- Explicit baseline/additive migrations, backups, schema checks, and synthetic demo data.
- Shared SQLite connection policy and removal of constructor-driven schema changes.
- Python 3.12 environment, maintained morphology dependency, complete hashed dependency lock, and CI workflow.
- Unit tests isolated from personal databases, credentials, and provider writes.
- Runtime/personal artifacts removed from Git's index with local files retained.
- Drive retained as a deliberate capture channel; fresh sync reads, preserved SQLite history, per-word rollback, visible partial results, and sync-run history.
- Sentence reward ledger preventing repeat awards, including concurrent retries.
- Query validation, local redirect validation, upload size limit, and sanitized upload filenames.
- Current setup, architecture, synchronization, and operations documentation.
- Dormant frontend/backend port removed, with its full source and historical data preserved outside the repository.

## Next: Word Post migration

The owner approved the Word Post design on 8 September 2026 and confirmed a local-household first release, optional grown-up Anki and adult approval of authored/AI-drafted content. The [migration programme](word-post/README.md) is the authoritative plan; the [delivery backlog and gates](word-post/delivery-plan.md) track the recommended sequence.

The build/design foundation and Git/restore checkpoint are now implemented; [remaining verification](word-post/implementation-progress.md) is explicit. The owner subsequently prioritised native flashcards, shared child games, Lingocoins and Elo-style adaptation. The [product backlog](word-post/product-backlog.md) owns the current order and effort assessment:

1. **Stage 1 implemented:** shared learner, content approval, persistent attempts, reward ledger and protected local assets. See [setup, APIs and verification](word-post/stage-1.md); the child preview remains separate.
2. Deliver native FSRS review with durable history, save/resume and undo; make it the first usable learning slice.
3. Add consistent Lingocoins, Sentence Post/Moon Picnic, matching/sorting games and reviewed reading/listening activities.
4. Add optional Anki Link through the existing preparation/export adapters with durable operations and reconciliation; adapt creative jumble, writing and lesson play to the same learner records.
5. Introduce conservative Elo-style difficulty selection after comparable evidence exists. Prepare local asset storage for a later Fly.io/Tigris move without making hosting a prerequisite.
6. Complete capture reliability, pilot, accessibility and rollback gates before switching the default; retire unused presentation separately.

Drive remains a deliberate capture channel. Removing a capture never deletes structured vocabulary/history. Existing reverse export remains unchanged until its future policy is decided explicitly. The old difficulty/ELO/coin measures do not become child proficiency or mastery measures by relabelling them.

The Word Post plan includes incremental route/SQL consolidation, maintained commands, production packaging and documentation. Native spaced repetition is now in scope. Full offline editing, public hosting, classroom management, arbitrary Anki template compatibility and two-way scheduling sync remain later work. Local-first delivery with Fly.io preparation was reconfirmed by the owner.

The dormant backend/frontend port has been removed and externally archived. The old Astro/API-only migration plan is retired. A future frontend replacement is a separate architectural decision based on current product needs, not a requirement to finish the abandoned port.
