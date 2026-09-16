# Russian Vocab — Repository Overview

> Port retired on 8 September 2026: both `russian_arcade_*` directories have been removed and archived outside the repository. The Astro/API-only migration below is no longer the active plan. See [current roadmap](docs/roadmap.md) and [archive recovery](docs/retired-port.md).

> Historical reference. Current setup and direction are in README.md and docs/. The active app now has an application factory, migrations, and isolated tests. Drive is a deliberate mobile capture channel alongside the SQLite learning library.

*An onboarding-oriented walkthrough of the codebase as of May 2026.*

---

## 1. What this project is

A personal-scale Russian-language learning toolkit built around a vocabulary database, an Anki spaced-repetition pipeline, and a web app that layers AI-generated practice activities on top of it (flashcards, reading comprehension, writing prompts, lessons, word jumbles, sentence practice). Everything is single-user (`user_id = 1` is hardcoded throughout).

The system has three siblings at the root, plus shared data and scripts:

| Folder | Role | Status |
|---|---|---|
| `flask_vocab_app/` | The actual running application — Flask + Jinja + HTMX, all features. | **Active backend** (last commit Oct 2025). Development paused. |
| `russian_arcade_backend/` | Older fork of `flask_vocab_app` (June 2025) trimmed back and given a JSON `/comprehension/data` endpoint. Intended as the API for Astro. | Stale; never finished. |
| `russian_arcade_frontend/` | Astro 5 + Preact rewrite target. | **Migration abandoned mid-flight** — only 1 of ~9 feature areas was started. |
| `scripts/` | Standalone Python utilities (mp4 → transcript → vocab → Anki cards, pronunciation, etc.) | Used to seed and maintain the DB. |
| `vocab.db`, `vocab-list.txt`, `anki_*` | Shared data and media assets. | Persistent. |

---

## 2. Technology stack

**Backend (`flask_vocab_app`)**
- Python 3 + **Flask** with `flask_session` (filesystem sessions).
- **SQLite** (`vocab.db`) accessed via `sqlite3` directly — no ORM. Each service opens its own connections; `models/database.py` provides a thin `get_db` helper but most services bypass it.
- **pymorphy2** for Russian morphological analysis (lemmatisation).
- **wordfreq** for difficulty scoring.
- **asgiref** (`async_to_sync`) to call async OpenAI helpers from sync routes.
- Other: `pdfplumber`, `Pillow`, `pydub`, `fuzzywuzzy`, `requests`.

**External services / APIs**
- **OpenAI** — story generation, exercise generation, scoring of user answers.
- **Yandex Translate** — fallback translation.
- **ElevenLabs** — TTS for stories and sentences (4 hard-coded voice IDs).
- **Google Drive** — syncs `vocab-list.txt` to a known file ID, cached locally for 1h.
- **AnkiConnect** (`localhost:8765`) — pushes generated flashcards into the user's Anki; pulls review stats back into `anki_cards`.

**Frontend layer (current — inside `flask_vocab_app`)**
- Server-rendered Jinja templates (`templates/*.html`, ~15 pages and partials).
- **HTMX 1.9.6** for partial swaps (the layer the user wants to move away from).
- **Bootstrap 5.3** for layout, ApexCharts for the metrics page.
- **Preact** loaded from `esm.sh` for "islands" — `VocabTable.js`, `StoryText.js`, `WordModal.js`, `SentenceTable.js`, plus thin wrappers `Lesson.js`, `WordJumble.js`, `Writing.js`. A mix of CDN-imported and `window.*`-attached components — no bundler.

**Migration target (`russian_arcade_frontend`)**
- **Astro 5** (`output: 'server'`, port 3000) + `@astrojs/preact` integration.
- **nanostores** for shared client state.
- TypeScript via `tsconfig.json`.
- Components are direct ports of the Flask Preact islands (`StoryText.tsx`, `WordModal.tsx`, plus a partly-migrated `VocabTable.js`).

---

## 3. Business logic — what the app actually does

The Flask app exposes 42 routes across 9 functional areas. The core data model is `words → forms` (one lemma, many inflected forms), with everything else attached around them.

**a. Vocabulary management** — `/`, `/add_word`, `/vocab`, `/edit_word`, `/delete_word`, `/word-details/<lemma>`
The home page is "add a word"; `/vocab` is the master list. Adding a word lemmatises it with pymorphy2, fetches its inflected forms, scores difficulty via `wordfreq`, optionally generates a mnemonic, and stores it.

**b. Flashcard generation & Anki sync** — `/generate`, `/generate_word_forms`, `/sync*`, `/sanitize_vocab`, `/apply_sanitization`, `/review_cards`
`FlashcardService` builds cloze-style Anki cards (sentence + audio + image) for selected forms and pushes them via AnkiConnect. `SyncService` reconciles `vocab.db` with the Drive `vocab-list.txt` and with Anki's review state, including a "preview before apply" sanitisation step. Difficulty bumps for plurals (+1) and participles (+2) — a recently added piece of logic.

**c. Reading comprehension** — `/comprehension*`
Pick a topic + difficulty → OpenAI generates a Russian story → DALL·E-style image → ElevenLabs audio → comprehension questions. Each token in the story is lemmatised and tagged "added/not added" against the user's vocab so it can be hover-clicked to add to vocabulary. Answers are AI-scored; stories can be saved and reloaded. Users can also paste a custom story.

**d. Writing exercises** — `/writing*`
OpenAI generates a writing prompt with required vocabulary; user response is timed and AI-scored.

**e. Lessons** — `/lessons*`
PDF/image upload → `pdfplumber` extraction → AI-generated practice prompts and grading, stored in `lessons` table.

**f. Word jumble** — `/word_jumble*`
Word-ordering mini-game generated and graded by OpenAI.

**g. Sentence practice** — `/sentences`, `/sentence/generate`, `/sentence/assess`, `/sentence/save`, `/sentence/add`
Generates target-form sentences, assesses user attempts (with `fuzzywuzzy` for close-match tolerance), saves favourites with audio.

**h. Metrics dashboard** — `/metrics`
ApexCharts visualisation of vocabulary growth, topic distribution, difficulty buckets — uses `models/metrics.py`.

**i. Gamification** — `/user/stats`
Lingocoins + ELO rating; rewarded actions update the `users` and `anki_cards.rewarded` columns.

---

## 4. Database schema (SQLite, 10 tables)

| Table | Rows | Purpose |
|---|---|---|
| `words` | 1,233 | Lemmas with `pos`, `count`, `lemma_difficulty`, `topic` (JSON), `mnemonic`, `date_added` |
| `forms` | 16,049 | All inflected forms per word with morphological `tags` (JSON) and `form_difficulty` |
| `anki_cards` | 192 | Mirror of Anki review state per form (`interval`, `lapses`, `reps`, `ease`, `due`, `mod`, `rewarded`) |
| `saved_stories` | 8 | Comprehension stories with image, audio, questions, answers, feedback, score |
| `user_stories` | 2 | Many-to-many between user and saved stories (with `rewarded` flag) |
| `sentences` | 21 | Generated/saved sentences with translation, topic, audio |
| `writing_exercises` | 2 | Writing tasks + responses + AI feedback |
| `lessons` | 4 | PDF-derived lessons with prompts and responses |
| `word_jumble_games` | 6 | Mini-game attempts |
| `users` | 1 | `lingocoins`, `elo_rating` (always `user_id = 1`) |

Twelve `vocab.db_*.bak` files sit alongside the live DB — manual snapshot-before-migration backups, not a real migration system.

---

## 5. Code layout inside `flask_vocab_app`

```
app.py                  ~1,600 LoC — every route is here, no blueprints
config.py               Hardcoded API keys + paths (see §7)
filters.py              Jinja filters
models/
  database.py           get_db / close_db helpers (lightly used)
  words.py, forms.py    Tiny CRUD helpers
  metrics.py            Aggregation queries for /metrics
services/               ~3,400 LoC — one class per external integration / feature
  openai_service.py, yandex_service.py, elevenlabs_service.py
  anki_connect.py, google_drive_service.py
  flashcard_service.py, sync_service.py
  comprehension_service.py, writing_service.py, lesson_service.py
  word_jumble_service.py, sentence_service.py, user_service.py
utils/
  pos_case.py           POS / case constants
  formatters.py         Cloze + Anki tag formatting
  logging.py            8-line shim
templates/              15 Jinja templates (HTMX-driven partials prefixed `_`)
static/
  css/style.css         346 LoC
  js/                   7 Preact islands (1,226 LoC)
  media/, uploads/      Generated audio/images, lesson uploads
*.py at root            One-off maintenance scripts (assign_topics, assign_mnemonics,
                        clean_database, sync_anki_cards, debug_pymorph, test_query)
```

There are **no automated tests** — `test_query.py` is an ad-hoc DB query script.

---

## 6. The Astro migration — where it actually got to

`russian_arcade_frontend` is essentially a green-field Astro project with one half-migrated page:

- **`src/pages/index.astro`** — default `<h1>Astro</h1>` boilerplate. Untouched.
- **`src/pages/comprehension.astro`** (220 LoC) — the only real port. Server-side fetches `http://localhost:5000/comprehension/data` (a JSON endpoint that exists *only* in `russian_arcade_backend`, not in the live `flask_vocab_app`). Renders `<StoryText>`, `<WordModal>`, the audio/image, questions form, and a hardcoded sidebar that links *back* to the Flask app for Flashcards and Vocab List.
- **`src/components/StoryText.tsx`** + **`WordModal.tsx`** — direct TypeScript ports of the Preact islands, using `nanostores` for the added-lemmas set. Fetches still hit `http://localhost:5000` directly (no env var, no proxy).
- **`src/components/VocabTable.js`** — JS port begun, not wired into any page.

So the migration covered roughly **one of nine feature areas**, with a parallel Flask backend (`russian_arcade_backend`) modified to return JSON for that one route. The other eight features have neither an Astro page nor a JSON endpoint.

The `russian_arcade_backend/` is a **June 2025 snapshot** of `flask_vocab_app/` minus the `lesson`, `sentence`, `user`, `word_jumble`, and `writing` services (which were added later). It was likely intended to evolve into a clean API, but `flask_vocab_app/` continued growing in the HTMX direction instead, and the two have since drifted.

---

## 7. Things to know before touching it

- **Hardcoded secrets in source.** `flask_vocab_app/config.py` and `scripts/API_key.py` contain plaintext OpenAI, Yandex, and ElevenLabs keys, plus a hardcoded Flask `SECRET_KEY`. These have been in git history — assume compromised and rotate before any further work or any public hosting.
- **Hardcoded macOS paths.** `~/...` appears in `config.py`, `app.py`, and several scripts. Anything moving off this machine needs a config layer.
- **Single-user assumption.** No auth, no signup, `user_id=1` everywhere. A real multi-user rewrite is a non-trivial schema change (every table that doesn't reference `user_id` would need to).
- **AnkiConnect dependency.** Several flows require Anki to be running locally with the AnkiConnect add-on on port 8765.
- **`vocab.db` lives in two places.** Both `flask_vocab_app/vocab.db` and `russian_arcade_backend/vocab.db` exist and are independently writable — confusing if both backends are ever run.
- **Large media in tree.** `anki_images/` is 443 MB, `anki_audio/` 29 MB, `anki_audio_english/` 12 MB. They appear to be checked in (only `API_key.py` is in `.gitignore`).
- **No migrations / tests / CI.** Schema changes are done by ad-hoc scripts (`vocab-list_to_schema.py`, `clean_database.py`); the only "test" is `test_query.py`.

---

## 8. Recommended starting points if resuming

1. **Decide the front-door story first** — finish Astro, retreat to Flask+HTMX, or pick a third option (e.g., FastAPI + Astro static, or just Astro + Flask-as-API but with a real API contract). The current half-and-half state is the most expensive place to be.
2. **Promote `flask_vocab_app` to API-only** by extracting the JSON shapes already implicit in HTMX responses — most routes already check `request.accept_mimetypes` or `HX-Request`, so the JSON branch exists in places.
3. **Rotate the API keys, then move them to env vars** before any further commits.
4. **Split `app.py`** — at 1,616 lines with 42 routes, Flask blueprints by feature would make the next migration round much cheaper.
5. **Drop `russian_arcade_backend/`** once a clean API plan exists — it's a fork of a fork and will only diverge further.
