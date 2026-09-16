# Russian Arcade on Fly.io

## Public demo

URL: https://russian-arcade.fly.dev/post/

The user selected a public demonstration with synthetic content, rather than
uploading their private learning installation. `fly.toml` sets `PUBLIC_DEMO=true`.
The public entry point creates a new disposable SQLite database on every process
start, seeds 13 vocabulary lemmas and 15 authored contextual cloze cards from
First steps, and gives each browser a separate temporary profile. No personal
vocabulary, lessons, recordings, OAuth files or provider keys are deployed.

Visitors can try the First steps lessons, browse sample vocabulary, review sample
cloze cards with the native scheduler, and explore activity/scenario catalogues.
The sample cards demonstrate text review; they do not include generated images
or speech. Generation, uploads, editing, live speaking and switching profiles are
blocked with a preview explanation. Real provider-backed functionality remains
available in a configured local installation.

Only explicitly allowed routes operate in demo mode, including legacy GET
routes that otherwise could trigger provider calls. Profile APIs return only the
current browser's identity. CSRF and activity ownership checks remain enabled.
Provider keys are cleared in demo app configuration even if accidentally supplied.
The deployment receives only a generated `FLASK_SECRET_KEY` via Fly secrets.

The demo runs as one Sydney Machine with one threaded Gunicorn process (eight
threads), one shared CPU and 2 GB RAM. It has no persistent volume: progress resets
on restart/deployment. SQLite enforces these shared limits:

- 1,200 application requests per minute, excluding static assets.
- 600 writes per minute and 10,000 per UTC day across all visitors.
- 60 writes per minute and 300 per UTC day for one browser credential.
- 30 new profiles per minute, 120 per hour and 2,000 in total.

Counters and profile admission are transactional. Refreshing cookies does not
reset the shared limits. HTTP 429 responses include `Retry-After`. Static files
remain available at the limit. These controls do not replace edge-level abuse
protection, and the temporary counters must not be used for paid AI allowances.
Reset a full demo with `fly apps restart -a russian-arcade`. Do not treat it as a
production account service or promise permanent learning records.

Deploy from the repository root:

```sh
fly deploy --remote-only --ha=false
fly status -a russian-arcade
fly checks list -a russian-arcade
```

The Docker build compiles Node 24 assets and uses the Python dependency lock.
The `.dockerignore` allowlist excludes runtime data and secrets. Do not pass
provider keys or `.env` as build arguments. HTTPS is enforced by Fly and secure
responses include a one-year HSTS policy; `/healthz`
checks database readiness. Keep a single Machine: in-memory/background ownership
and SQLite are not configured for replicas.

Validation covers visitor isolation, blocked generation/upload/Drive endpoints,
CSRF, private deployment authentication, sample page rendering and native cloze
reveal. Also verify the live homepage, stylesheet/script assets and HTTPS checks
after each deployment.

## Optional private household installation (not this public demo)

The following is a separate future deployment procedure for real personal data.
Use another app, omit `PUBLIC_DEMO`, mount a persistent volume and configure the
mandatory HTTP Basic credentials. Do not change the public demo into a personal
installation by merely copying its data.

## Build and storage

The Docker build compiles the UI with Node 24 and installs the hash-locked Python
3.12 dependencies plus Gunicorn. FFmpeg, Poppler and Russian Tesseract are
included. The build context excludes credentials, databases, uploads, generated
media and local sessions. Secrets enter through Fly runtime secrets, never
Docker build arguments or a copied `.env`.

`/data` is a persistent Fly volume:

| Location | Contents |
| --- | --- |
| `/data/vocab.db` | Vocabulary, profiles, schedules, lessons and progress |
| `/data/assets` | Content-addressed flashcard/game/speaking media |
| `/data/lesson-assets` | Original lesson documents and page renders |
| `/data/media`, `/data/uploads` | Legacy story/audio/image/upload files |
| `/data/sessions` | New hosted sessions; do not import local browser sessions |
| `/data/anki-media` | Generated Anki media where applicable |
| `/data/private` | Optional separately transferred Drive OAuth files |

Source the import from `instance/native-flashcards-mvp/settings.json` and its
configured paths. **Do not use the old `flask_vocab_app/vocab.db`.** Snapshot the
live database with SQLite's backup API, never copy a database in WAL mode by
itself. Copy its sibling `lesson-assets`, configured Word Post assets, uploads,
media and any required Anki media. Resolve legacy absolute media references on
the imported copy and verify representative lessons, stories, flashcards and
recordings. Keep originals unchanged.

Pause generation while taking the final database/media snapshot. Inspect pending
jobs and apply their existing recovery procedures on the hosted copy; in-process
threads do not migrate. Do not run simultaneous local/cloud edits expecting sync.
Choose the hosted copy as the active data store after cutover; keep the local
snapshot for recovery.

## Launch sequence

1. Confirm the release access model. This configuration is for private access.
2. Verify name availability and create the app in the intended Fly organisation.
3. Build the image and inspect the build context. Create one Sydney Machine and
   its volume without exposing an unprotected app. Use a maintenance command
   initially while importing data; the normal entry point refuses a missing DB.
4. Transfer the verified database/media snapshot privately with Fly SSH/SFTP.
   Verify integrity and file checksums before switching to the normal command.
5. Set `FLASK_SECRET_KEY`, `HOSTED_ACCESS_USERNAME`, `HOSTED_ACCESS_PASSWORD` as
   Fly secrets. Use independently generated credentials: session secret at least
   32 characters, access password at least 24. Set provider keys and preserve
   the current model/voice environment overrides. Do not print secret values or
   place them on command lines. Do not upload the local settings JSON wholesale.
6. Deploy with `fly deploy --ha=false` so Fly does not create a second Machine.
   Startup applies transactional migrations on the mounted volume, taking a
   pre-migration backup when needed. Do not add a `release_command`: release
   Machines do not mount this volume.
7. Verify unauthenticated HTML/API/media requests are denied; then verify sign-in,
   profiles, secure session cookies, CSRF-protected writes, existing media and
   microphone access over HTTPS. Smoke-test one provider-backed activity.
8. Establish an off-Machine backup and test restore before relying on the hosted
   installation. Volume snapshots alone are not the complete backup procedure.

This sequence is a runbook, not an automated deployment already performed.

## Limitations and follow-up

AnkiConnect on the server cannot reach Anki on your Mac through `localhost`.
Keep native study available and use the local Anki accessory until a supported
export or local bridge is implemented. Drive's interactive OAuth login must
remain disabled on the server; transfer/re-authorise its credentials explicitly
if hosted Drive sync is needed.

Deploy while no lessons, media batches or speaking assessments are running.
Graceful shutdown is bounded and cannot guarantee completion of long background
jobs. Durable workers/recovery supervision are needed before multiple instances.

Schedule off-volume SQLite snapshots plus media backups, with encryption and a
retention policy. Tigris is a reasonable later home for media/backups; the live
SQLite database must remain on a filesystem, not an object-store blob. A single
Machine/volume is not a high-availability deployment. Roll back code only when
schema-compatible; otherwise restore the verified snapshot and matching media
together during maintenance.

References: [Fly volumes](https://fly.io/docs/volumes/overview/),
[configuration](https://fly.io/docs/reference/configuration/),
[runtime secrets](https://fly.io/docs/apps/secrets/).
