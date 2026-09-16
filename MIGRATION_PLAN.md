# Migration Plan — Flask + HTMX → Astro + Flask-as-API

> Port retired on 8 September 2026: both `russian_arcade_*` directories have been removed and archived outside the repository. The Astro/API-only migration below is no longer the active plan. See [current roadmap](docs/roadmap.md) and [archive recovery](docs/retired-port.md).

> The owner-approved replacement direction and current migration strategy are in the [Word Post programme](docs/word-post/README.md).

> Historical reference. Current setup and direction are in README.md and docs/. The active app now has an application factory, migrations, and isolated tests. Drive is a deliberate mobile capture channel alongside the SQLite learning library.

*Companion to `REPO_OVERVIEW.md`. Decisions baked in: keep Flask (JSON-only), finish comprehension first, stay single-user.*

---

## Difficulty rating

**Overall: 6/10 — moderate, with one large boring chunk.**

| Dimension | Rating | Why |
|---|---|---|
| Backend conversion | 4/10 | Mostly mechanical — strip templates, return JSON. 25 of 98 render points already use `jsonify`; 22 use `render_template_string` (small inline partials, easy); 53 use `render_template` (need new JSON shapes). The business logic in `services/` doesn't change. |
| Astro feature build | 7/10 | You have ~9 feature areas and only 1 has been started. Each needs pages + Preact components + state + fetch wiring. The patterns are repeatable but the volume is real. |
| State management | 6/10 | Sessions, AnkiConnect side-effects, session-stored "current story" all need rethinking when the frontend owns state. nanostores helps but doesn't solve persistence. |
| AnkiConnect / external services | 3/10 | Unchanged — the backend still calls them. |
| Risk of regression | 5/10 | The fork insulates the live app, so the worst-case is "the new one doesn't work yet." But the schema is shared via `vocab.db` — be careful about concurrent writes during cutover. |

**Realistic timeline (part-time):** 6–10 weeks. **Full-time focused:** ~3 weeks. The comprehension proof-of-concept is the first 1–2 weeks; the remaining 8 features are bulk repetition that compounds in speed once the first one is solid.

The biggest hidden cost is **defining the JSON contract** for each feature — once you have it written down, both ends are fast. Skipping that step is what made the first attempt expensive (the Astro page hard-codes assumptions about a backend shape that only exists in one stale fork).

---

## The fork strategy

**Don't fork the directory; fork the git branch.** Two backends in one repo (the current `flask_vocab_app/` + `russian_arcade_backend/` situation) is exactly the trap that made the first attempt costly — they drift, the DB lives in two places, and nobody knows which one is canonical.

Concretely:

1. **Create a long-lived branch** off `main` called `api-only` (or `v2`). The current Flask+HTMX app stays on `main` and remains the user-facing system until cutover.
2. **Delete `russian_arcade_backend/`** on the new branch. It's stale and will only confuse the diff.
3. **Work on `flask_vocab_app/` directly** on the `api-only` branch — same paths, just transformed in place. This means no duplicated services and no second copy of `vocab.db`.
4. **Keep `russian_arcade_frontend/`** as-is on the new branch and build it out alongside.
5. **Only merge `api-only` → `main` at cutover**, when the Astro frontend covers enough features that you're ready to retire HTMX.

This gives you the benefit of "fork to avoid breaking prod" without the cost of two diverging backends. If you need to keep the HTMX app working on `main` while developing, you switch branches rather than running two Flask processes.

**The one duplication you do want:** copy `vocab.db` to `vocab.dev.db` for the new branch. Same schema, separate file, so nothing the new code does can corrupt the live DB you're using daily.

---

## Phase 0 — Prep (1–2 days)

Things that pay back immediately and don't depend on any architectural decision:

1. **Rotate API keys.** OpenAI, Yandex, ElevenLabs, the Forvo key in `scripts/pronunciation_standalone.py`, and Flask's `SECRET_KEY` — all are in committed files. Rotate, then move to a `.env` file and use `python-dotenv`. Add `.env` and `*.bak` to `.gitignore`.
2. **Add `.gitignore` entries** for `vocab.db_*.bak`, `flask_session/`, `__pycache__/`, `venv/`, `.DS_Store`, `static/uploads/`, `static/media/sentence_*.mp3`, and `node_modules/`. The repo is currently committing all of these.
3. **Create `api-only` branch and `vocab.dev.db`.**
4. **Pick a port for the API.** Astro uses 3000. Flask defaults to 5000 — keep that. Document the assumption in a top-level README.

---

## Phase 1 — Backend: Flask becomes API-only (1–2 weeks)

The goal is for every route in `app.py` to return JSON, with no Jinja involvement. The business logic in `services/` is untouched.

**1.1 Add CORS and a versioned API prefix.**
Install `flask-cors`. Mount all routes under `/api/v1/`. Keep them stable from here on so the Astro side has a real contract.

**1.2 Group routes into Flask blueprints by feature.**
The 1,616-line `app.py` is the single biggest source of friction. Split into roughly:

- `routes/vocab.py` — `/`, `/add_word`, `/vocab`, `/edit_word`, `/delete_word`, `/word-details/<lemma>`
- `routes/flashcards.py` — `/generate`, `/generate_word_forms`, `/sync*`, `/sanitize_vocab`, `/apply_sanitization`, `/review_cards`
- `routes/comprehension.py` — `/comprehension*`
- `routes/writing.py`, `routes/lessons.py`, `routes/word_jumble.py`, `routes/sentences.py`
- `routes/metrics.py`, `routes/user.py`

Doing this *first*, before the JSON conversion, gives you a much smaller diff per feature and lets you migrate one blueprint at a time.

**1.3 Convert templates to JSON, blueprint by blueprint.**

For each route:
- If it returns `jsonify(...)` — leave it.
- If it returns `render_template_string(...)` — replace with `jsonify({...})` returning the data the template was rendering.
- If it returns `render_template('foo.html', ...)` — return the same context dict as JSON.
- If it branches on `HX-Request` or `accept_mimetypes` — keep only the JSON branch.

**1.4 Define the contract.**
For each feature, write a short markdown file (`api/contracts/comprehension.md`) listing endpoints, params, and response shapes. This is what the previous attempt skipped and what made the Astro side guess.

A lightweight `marshmallow` or `pydantic` layer on responses is optional but worth it — it stops the Astro side from breaking silently when a service returns a different shape.

**1.5 Move sessions to client-side or minimal server state.**
A bunch of routes use `session['current_story_text']`, `session['current_story_data']` etc. These don't survive a SPA-style frontend cleanly. Two options:
- Persist the in-flight story to a `current_story` row keyed by `user_id` (simplest, single-user).
- Return everything to the client and let it pass it back on subsequent calls (more REST-y, slightly more bandwidth).

Pick one and apply it everywhere; mixing is the source of the worst bugs.

**1.6 Delete the templates folder** at the end of Phase 1 to make sure nothing fell back to it. Templates and static JS islands can be removed once their corresponding API endpoints exist.

**Checkpoint:** `curl http://localhost:5000/api/v1/comprehension/data` returns the JSON the Astro page already expects. The HTMX app is broken on this branch — that's fine, `main` still works.

---

## Phase 2 — Astro: finish comprehension end-to-end (3–5 days)

Treat this as the **reference implementation**. Every other feature will copy its shape.

**2.1 Set up the foundation properly.**

- Replace `http://localhost:5000` hardcodes with `import.meta.env.PUBLIC_API_BASE` (defined in `.env`), so dev/prod can differ.
- Create `src/lib/api.ts` — one `fetchApi(path, opts)` wrapper that handles base URL, JSON parsing, and error shape. Every component calls this, never raw `fetch`.
- Create a real `src/layouts/Base.astro` with the sidebar (currently inlined in `comprehension.astro`). All future pages extend it.
- Create `src/stores/` for nanostores: `addedLemmas.ts`, `userStats.ts`, `currentStory.ts`. Single source of truth per concern.

**2.2 Finish `comprehension.astro`.**
The current page renders the story but is missing the form to *generate* a new one, the answer-submission flow, the save flow, and the saved-story loader. These are 4–5 more endpoints to wire up — all already exist in the Flask app, just need their JSON contracts settled in Phase 1.

**2.3 Audio + image handling.**
The Flask app serves these from `/static/media/...` and `/static/uploads/...`. The Astro page references the same URLs on `localhost:5000`. Decide now whether to (a) keep serving media from Flask permanently (simplest), or (b) move media into the Astro `public/` folder or a CDN. (a) is fine for single-user.

**2.4 Sidebar links.**
Currently the sidebar in `comprehension.astro` links back to `localhost:5000` for Flashcards and Vocab. Once Phase 1 is done, those *aren't there anymore* — the sidebar needs to point to Astro routes that don't exist yet. Use placeholder "Coming soon" pages so the user can navigate without 404s during the rollout.

**Checkpoint:** Open `localhost:3000/comprehension`, generate a story, listen to audio, answer a question, save it, reload it. Everything works without touching `localhost:5000` directly.

---

## Phase 3 — Port remaining features (3–7 weeks part-time)

Repeat the comprehension pattern for the other eight features. Suggested order, biased toward low-risk → high-value:

1. **Vocab list + word details** — read-mostly, the existing `VocabTable.js` is half-ported, easy win.
2. **Sentences + saved sentences** — similar shape to comprehension (generate, save, load).
3. **Writing exercises** — small surface, mostly forms.
4. **Word jumble** — small surface, drag/drop is the only new wrinkle.
5. **Lessons** — file uploads add friction (FormData + multipart), do this once you've ported simpler stuff.
6. **Metrics dashboard** — ApexCharts → swap for Chart.js or Recharts on the Astro side. Mostly visual.
7. **Add word / generate flashcards** — the main daily flow. Save for last because it touches AnkiConnect side-effects and is the one most users would notice if broken.
8. **Sync (Drive + Anki)** — the riskiest because it writes to external systems. Port last, behind a feature flag, with the existing Flask CLI scripts (`sync_anki_cards.py`) as a fallback.

For each feature, the loop is:
1. Define the JSON contract.
2. Convert the Flask routes to that contract.
3. Build the Astro page + Preact components.
4. Smoke-test against `vocab.dev.db`.
5. Tick the feature off `_sidebar.html`'s old list.

---

## Phase 4 — Cutover (1–2 days)

1. Point the `api-only` branch's Flask config at the real `vocab.db`.
2. Run both branches side by side for a week — `main` on its old port, `api-only` on a different one — and use `api-only` as your daily driver.
3. When you're confident, merge `api-only` → `main`. The merge will look enormous but it's mostly deletions (templates, static JS, HTMX wiring).
4. Delete `russian_arcade_backend/` from history if you want a clean repo (`git filter-repo`).
5. Tag `v2.0`.

---

## What this plan deliberately does *not* do

- **Doesn't add auth.** Single-user assumption stays — adding it later is ~1 week of focused work and is independent of this migration.
- **Doesn't change the database.** Same SQLite, same schema. The schema is fine; the problem was always the frontend.
- **Doesn't replace AnkiConnect, Drive, or any external service.** They keep working unchanged.
- **Doesn't introduce TypeScript on the backend or Pydantic schemas.** Optional polish for later.
- **Doesn't try to host this anywhere.** Everything stays on localhost. If hosting becomes a goal, it's a separate project (involves Anki running on the server, which is its own headache).

---

## The biggest risks, ranked

1. **JSON contract drift** — the same problem that killed attempt #1. Mitigation: write the contract files in Phase 1 *before* writing any Astro code for that feature. Treat them as the source of truth.
2. **Session-state assumptions** in the Flask routes (the "current story" pattern). Audit these in Phase 1.4 — they're easy to miss until a flow breaks halfway through.
3. **AnkiConnect timing.** Some flows assume Anki is already open. The Astro app should surface a clear error state when the AnkiConnect call fails, not a generic 500.
4. **`vocab.db` accidentally written by both branches.** The `vocab.dev.db` copy in Phase 0 is the mitigation — don't skip it.
5. **Scope creep.** Every time a new "while we're here" idea comes up (auth, hosting, Postgres, multi-language), write it down for v3 and don't do it now. The sunk cost of attempt #1 was largely from rewriting things that didn't need rewriting.

---

## TL;DR

A 6/10 migration. Branch (don't fork directories), strip Flask down to JSON in place, ship comprehension end-to-end as the reference, then grind through the other 8 features in the order above. The hard part isn't the code — it's writing down the API contract before you write the frontend, which is the thing that didn't happen the first time.
