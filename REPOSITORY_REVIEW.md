# Repository review — 8 September 2026

> Port retired on 8 September 2026: both `russian_arcade_*` directories have been removed and archived outside the repository. The Astro/API-only migration below is no longer the active plan. See [current roadmap](docs/roadmap.md) and [archive recovery](docs/retired-port.md).

> Historical pre-implementation review. Subsequent clarification: Drive and SQLite deliberately serve complementary capture and structured-storage roles. The initial claim of competing sources of truth should be read as a need for a clearer sync contract, not a recommendation to remove Drive capture. Current implementation and remaining work are documented in README.md and docs/.

This is a review of the current working tree at `c3d93ba4`, including the substantial uncommitted stabilization and UI work. Recommendations below are proposals, not implemented changes or newly agreed product requirements. Application source and learning data were left unchanged during this review.

The project is a substantial personal learning application in the middle of consolidation. It has useful domain logic, persisted learning material, and a working Flask page baseline. Its main constraints are fragmented data ownership, incomplete reproducibility, and competing application structures. The next milestone should establish a reliable application foundation and one complete learning workflow.

**Current structure**

| Location | Actual role | Recommended treatment |
|---|---|---|
| `flask_vocab_app/` | Canonical implementation: Flask, Jinja, HTMX, Preact components, SQLite, provider integrations | Continue here; consolidate before renaming directories |
| `russian_arcade_backend/` | Older Flask fork with different services, routes, and database | Compare unique behavior and data, then retire the duplicate implementation |
| `russian_arcade_frontend/` | Astro/Preact experiment, primarily comprehension | Treat as incomplete; reconnect to the canonical backend before extending |
| `scripts/` and root Python scripts | Import, transcript, pronunciation, Anki, and database maintenance utilities | Convert maintained workflows into documented commands using shared configuration and services |
| Root and app databases, backups, `anki_*`, runtime directories | Personal data, generated assets, installed dependencies, and runtime state | Separate from source control, with an explicit backup and restore policy |
| `README.md`, `REPO_OVERVIEW.md`, `MIGRATION_PLAN.md` | Minimal entry point plus historical analysis and migration proposal | Replace stale factual claims; link one maintained architecture and roadmap |

The active app has 44 routes excluding Flask's static route. Five blueprint factories cover vocabulary, flashcards, comprehension, sentences, and user statistics. Writing, lessons, and word jumble remain in the 414-line `app.py`. Five repositories provide some read operations, but business services and routes still access SQLite directly. There are 69 `sqlite3.connect` call sites across active Python source, including tests and maintenance scripts. Large files include `sync_service.py` (778 lines), `comprehension_service.py` (642), and `blueprints/vocab.py` (563).

Useful foundations already exist: environment-based keys, lazy service initialization, optional browser OAuth, a shared page shell, English/Russian UI support, repositories, and regression tests. Preserve these improvements. The current tree has 67 modified tracked files and four untracked files before this report; much of the noise is runtime state, but substantial source changes also need review and preservation.

**Validation performed**

Tests ran in a temporary copy of the active application and database, excluding credentials, local environment files, and existing sessions. External socket connections were blocked. Python dependencies came from the existing Python 3.9.23 virtual environment; this does not establish that a fresh Python installation is reproducible.

| Check | Result |
|---|---|
| Existing unittest suite | 16 tests passed |
| Existing route smoke script | All 11 checks returned HTTP 200 |
| Database snapshots | All three primary databases passed SQLite `quick_check` and had zero declared foreign-key violations |
| New empty database | `/`, `/metrics`, and `/writing` returned 500; `/vocab` returned 200 through its fallback/error handling |
| Astro dependency installation | `npm ci --ignore-scripts --no-audit --no-fund` succeeded in a temporary copy |
| Astro production build | Failed with `NoAdapterInstalled`; also warned that `src/pages/test.tsx` is unsupported as a page |
| Astro's expected Flask endpoint | `/comprehension/data` returned 404 in the active app |
| Invalid query values | `/vocab?page=abc` and `/sentence/generate?topic=food&difficulty=abc` returned 500 |
| Repeated assessment | Two identical sentence assessments returning the same saved sentence ID triggered two reward updates using fake services |
| UI language redirect | `next=//example.invalid` returned a redirect to that external host |

Provider generation, Drive/Anki writes, browser rendering and interaction, and real upload workflows were not exercised. Passing page tests establish server rendering, not complete end-to-end feature correctness. No dependency vulnerability audit or full historical secret scan was performed.

**Findings in priority order**

1. **Repository hygiene still exposes runtime and credential artifacts.** Of 18,965 tracked files, 17,030 are inside virtual environments. Tracked files also include sessions, databases, backups, `flask_vocab_app/token.json`, `credentials.json`, and two compiled `API_key` modules. `.gitignore` now covers many of these categories, but already tracked files remain tracked. The earlier overview records historical plaintext keys; rotation status cannot be established from the repository. Inventory and remove runtime/credential files from the index while preserving required local copies, verify credential revocation/rotation, and handle any history cleanup as a separately coordinated operation. Do not silently discard personal media or database snapshots.

2. **Vocabulary ownership is split across Drive and SQLite.** In `blueprints/vocab.py`, `/add_word`, `/edit_word`, `/delete_word`, and `/add-vocab/<lemma>` use Drive operations. Most learning selection and metrics read SQLite, with a separate sync process importing vocabulary. Sessions and browser caches add more representations of “added.” Consequently, an acknowledged addition need not yet be available for exercises. Make SQLite authoritative: save and normalize locally, make enrichment explicit, and expose pending/success/failed states for external synchronization. Treat Drive as import/export or backup, and Anki as the authority for its review scheduling data. Document deletion, conflict, and retry behavior before changing the sync implementation.

3. **There is no deterministic database bootstrap or migration history.** The active database has 1,233 words, 16,049 forms, and ten application tables. The root database has 930 words and two tables; the older backend has 979 words and four tables. They are not interchangeable. Some maintenance scripts explicitly target the root database while the app defaults to `flask_vocab_app/vocab.db`. Constructors create and alter individual tables opportunistically, but a new database cannot support the app. Establish a baseline schema, versioned migrations, small synthetic fixtures, and one configurable path for every command. Inspect unique data before retiring the older databases. Passing integrity checks is reassuring about the snapshots, not proof that future writes are protected: application connections do not consistently enable foreign-key enforcement.

4. **Assessment persistence and rewards need one shared transaction model.** `blueprints/sentences.py` rewards any successful save ID; `SentenceService.save_sentence` returns an existing ID for an already saved sentence. Retrying assessment can therefore reward the same result again. The new regression test prevents rewards on manual re-save, but does not cover assessment retries. Introduce an explicit attempt ID and a unique reward event for that attempt, with transactional persistence and retry-safe handling. Writing assessment currently returns feedback without persisting it; its save operation stores the exercise/response but omits score and feedback. Lessons and jumbles persist their own results without a common progress model. Define what constitutes an attempt, how deliberate retries work, how scores normalize, and which outcomes affect progress.

5. **The Astro frontend is not connected to the current application contract.** It hardcodes `localhost:5000`, expects an endpoint found in the old backend, and mixes JSON fetches with form submissions to HTML routes. Its configured server output lacks a build adapter. The build failure matches Astro's documented [adapter requirement](https://docs.astro.build/en/guides/on-demand-rendering/). It needs a deployment decision, shared layout, API client, coherent session/media handling, and feature-level acceptance checks before it can replace the current UI.

6. **Service boundaries and operational behavior remain inconsistent.** `app.py` constructs global configuration, application state, and lazy services at import time; route tests import that global app. A factory accepting configuration and test doubles would enable isolated app instances, as described in [Flask's factory guidance](https://flask.palletsprojects.com/en/stable/patterns/appfactories/). Repositories coexist with older model helpers and service SQL. Provider clients are independently constructed inside multiple feature services despite injected service objects. Several direct HTTP calls omit timeouts, and generation/media work runs within web requests. Consolidate transaction handling and provider policies, then introduce durable job status and safe retry for long operations. SQLite's connection context manager handles commit/rollback but does not close the connection; use explicit lifecycle management rather than relying on garbage collection ([Python documentation](https://docs.python.org/3/library/sqlite3.html#how-to-use-the-connection-context-manager)).

7. **Input, response, and configuration contracts need cleanup.** Integer parsing before validation produces the reproduced 500s. The language redirect accepts protocol-relative external URLs. Several routes interpolate user/provider text into raw HTML. Upload handling relies on filename extensions and retains client filename text; there is no application upload-size limit configured. Response shapes vary among full pages, HTML fragments, and JSON, and some failures return 200. Define boundary validation, escaped rendering, consistent errors, bounded uploads, and local-only redirects. Before any remote deployment, explicitly address authentication, request-forgery protection, and production secret configuration; current hardcoded user 1 behavior is a local single-user design. `.env.example` also omits model settings and Drive auto-auth, while the configured default deck is bypassed by a hardcoded deck in app wiring.

8. **Documentation currently misrepresents both progress and remaining work.** `REPO_OVERVIEW.md` says there are no tests or blueprints and describes a roughly 1,600-line `app.py`; all are outdated. `MIGRATION_PLAN.md` treats schema/integrations as unchanged and proposes removing HTML before frontend parity on a long-lived branch. Data ownership, retry semantics, and bootstrap findings make that too optimistic. Its delivery estimates and suggestion that multi-user support is independent should not be treated as validated commitments. The one-line root README provides no reliable starting procedure.

**Recommended direction**

Keep one Flask backend and SQLite for the current single-user product. Make domain services the shared implementation used by pages, API routes, background work, and CLI commands. Retain the working Flask interface while introducing explicit JSON contracts one feature at a time. The documented Astro/Preact target can remain the frontend direction, but its value should be demonstrated by completing comprehension against the canonical backend. Avoid another backend fork or a wholesale API-only conversion before frontend parity.

The intended learning loop should be: capture a word from reading or an import; normalize and save it; use it in practice; retain the attempt and feedback; update progress once; export appropriate cards to Anki; import review outcomes. A shared vocabulary identity and attempt history will connect the product more meaningfully than giving independent pages a common sidebar.

Recommended boundary: routes validate input and format output; services implement learning workflows; repositories manage persistence through a shared connection/transaction layer; integrations adapt Drive, Anki, AI, translation, and audio providers. Browser state holds transient interaction state; durable vocabulary, activities, attempts, rewards, and sync state belong in the database. Use one browser origin for application/API/media routing if Astro proceeds, with an explicit cookie/session arrangement.

After behavior and ownership are settled, a possible destination layout is:

```text
backend/
  russian_vocab/
    __init__.py          # create_app
    config.py
    routes/              # pages and versioned API adapters
    services/            # learning workflows
    repositories/
    integrations/
    jobs/
    cli/
  migrations/
  tests/
frontend/                # Astro/Preact, if retained after the pilot
docs/
  architecture.md
  development.md
  data-model.md
  integrations.md
  operations.md
  roadmap.md
  api/
  decisions/
instance/                # ignored local database, media, sessions, uploads
README.md
.env.example
```

This is a destination, not a proposal to move all files before stabilizing behavior. Keep existing paths until individual changes are tested.

**Delivery sequence and completion criteria**

| Milestone | Work | Complete when |
|---|---|---|
| 1. Preserve and establish a baseline | Review existing uncommitted source work; back up data/media; remove tracked runtime artifacts; document canonical app/data paths and runnable commands | Git changes reflect intentional source changes; data restore is checked; existing tests pass without personal credentials |
| 2. Make setup reproducible | Application factory, unified configuration, explicit Python runtime, dependency installation verification, migrations, synthetic fixtures, CI | A clean checkout can create an empty database, migrate, load demo data, start, and run tests without a personal database or providers |
| 3. Integrate vocabulary and progress | Local vocabulary service, consistent identities, persisted attempts/feedback, retry-safe rewards, explicit Drive/Anki sync records | A word added from reading appears immediately in vocabulary/practice; retrying a submission does not duplicate rewards or external writes |
| 4. Complete the comprehension pilot | Versioned API contract, Astro build/adapter, shared API client and layout, saved activity IDs, media handling, browser tests | Generate or paste, read, add vocabulary, answer, save, reload, and resume all work through the canonical backend, including failure states |
| 5. Expand by complete workflow | Migrate vocabulary/sentences, then other practice modes; expose integration status and recoverable generation jobs | Each feature has documented behavior, persistence, failure handling, and automated workflow coverage before its old UI is retired |
| 6. Release and simplify | Remove duplicate backend after data/behavior comparison, retire replaced templates, package startup and backup/restore, update user guide | One documented application entry point supports ordinary use, upgrades, recovery, and troubleshooting |

Prefer small branches merged after passing checks over a long-running branch that intentionally breaks the app. Defer a new database server, multiple services, or multi-user deployment until a concrete product requirement justifies them. If Astro is no longer a firm preference, a bundled Preact frontend within Flask is also possible; both choices still require the same data and service consolidation.

**Documentation to maintain alongside implementation**

The README should identify the canonical app, explain its learning workflow, give exact install/start/test commands, and distinguish required local capabilities from optional providers. Development documentation should cover supported runtimes, fixtures, migrations, and test isolation. Architecture and data-model documents should identify source-of-truth rules, vocabulary/form identities, attempt/reward semantics, and transaction boundaries. Integration documentation should explain configuration, health, sync direction, conflict behavior, retry/idempotency, and the local Anki dependency. Operations documentation should cover where files live, backups, restore, upgrades, and failure recovery. API contracts and short decision records should change in the same pull request as the behavior they describe.

The first implementation batch should focus on baseline preservation, repository hygiene, an accurate README, and factory/configuration/test isolation. Follow with migration/bootstrap support and the concrete consistency defects above. This creates a reviewable foundation for the frontend work without discarding the useful application already present.
