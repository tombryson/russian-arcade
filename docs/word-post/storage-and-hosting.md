# Local storage now; Fly.io and Tigris later

Status: the owner reconfirmed local-first delivery on 8 September 2026. Fly.io is the preparation target, not a deployment authorised or performed by this requirements update. No bucket, account or cloud bill has been created.

Implementation update: [Stage 1](stage-1.md) adds local content-addressed assets, protected delivery and a database/Word Post asset backup command. Hosted adapters and deployment remain future work.

## Storage responsibilities

| Data | Local-first location | Future hosted location |
|---|---|---|
| Vocabulary, card definitions/versions, learners, attempts, FSRS state, rewards and export mappings | SQLite | Transactional database: initially SQLite on a persistent Fly Volume if a single-host household deployment is acceptable; evaluate managed Postgres when availability/concurrency requirements change |
| Audio, illustrations, approved attachments | Files behind an `AssetStore` interface | Private S3-compatible Tigris objects referenced by stable application asset IDs |
| Consistent database backups and asset manifests | Separate local backup directory | Protected off-host backup objects, with retention and restore verification |
| Curated UI art, fonts and hashed JS/CSS | Source assets and reproducible build | Versioned application release assets; retain old hashed files during rollout |
| Mobile word capture | Existing Google Drive text file | Same deliberate capture path until an explicit policy changes it |

Fly offers Tigris as S3-compatible object storage. This makes it suitable for media and backup files. A single mutable blob containing the application's live learning state would make our required transactional updates and concurrency checks much harder; keep those records in the database. [Fly/Tigris documentation](https://fly.io/docs/tigris/).

## Prepare now

Implement a narrow asset interface around put/open/metadata and stable storage keys. Local disk is the first backend; the card/session code never needs an absolute Anki directory or a provider-specific URL. Store hash, size, media type, owner/visibility, source and approval alongside each asset reference.

Upload media before publishing its database reference; validate it and only then make the card version eligible. Orphan cleanup uses a retention window and reference check. Never delete a referenced object immediately because one card is edited or withdrawn. Check type/size and avoid raw child names or writing in object keys.

Published text-only cards remain usable if optional media is missing. An audio-only task with unavailable required audio is unavailable or replaced by an explicitly different task; silently revealing its transcript would change the skill being tested.

Separate public design assets from private uploads and learner recordings. Tigris buckets can be private and support signed URLs. Begin with application-authorised delivery; if direct signed delivery is added, use short-lived access, approved content checks and an explicit CSP/CORS policy. Keep storage credentials on the server. [Tigris access options](https://fly.io/docs/tigris/).

## Hosted household gate

Fly Machine root filesystems are ephemeral. SQLite must live on a persistent volume if selected for hosting. Volumes are hardware-local and do not automatically replicate, so a single Machine/volume is a deliberate availability tradeoff. Fly snapshots are supplementary; restore-tested backups are still necessary. Volume-backed migrations must execute where the volume is actually mounted. [Fly Volume documentation](https://fly.io/docs/volumes/overview/).

Before hosting: decide acceptable data-loss/recovery windows, deploy an authenticated household boundary with HTTPS/CSRF and private-asset controls, provision persistent storage/secrets, and verify restart/deploy/restore with a copied dataset. Do not provision multiple independent SQLite writers and assume they share data. Choose an explicit replication design or a shared transactional database if multiple application Machines become necessary.

Use SQLite's backup API or a verified SQLite-aware backup mechanism to create a consistent backup; do not copy just a live main file while recent transactions remain in WAL. Pair the database snapshot with referenced asset hashes/keys and keep those asset versions for the backup's retention period. Test restoring onto a fresh instance and opening a saved review, media and reward history.

The first Fly release should not simultaneously introduce native scheduling, migrate legacy history and change every storage backend. Prove the local learning transaction first, then move a verified build and dataset through the hosting gate. Anki Link on a hosted server will require a file export or local bridge; the server cannot reach a laptop's AnkiConnect through its own `localhost`.
