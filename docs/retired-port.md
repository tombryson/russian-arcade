# Retired frontend/backend port

On 8 September 2026, the dormant `russian_arcade_backend/` and `russian_arcade_frontend/` directories were removed from the working repository. The active application and scripts had no references to either directory. The backend was an older Flask fork, and the frontend was an incomplete Astro/Preact experiment that did not build or target the current Flask API.

Both complete directories were moved outside the repository, retaining their source, historical database, media, dependencies, and local files. Every archived file was checked by SHA-256; symlink targets were also verified. The archive includes a manifest.

Archive location:

`~/.local/share/russian_vocab/archives/20260908-192650-retired-port`

The canonical application remains `flask_vocab_app/`. Its database and media were not changed by this removal. The archive's database is historical data, not a replacement for the current learning library.

For recovery, copy the needed source or data from the archive into a separate inspection directory. If the old port itself must be restored, copy its archived directories back to the repository under their original names. Do not run the old backend against the canonical database. This cleanup does not rewrite Git history.

The prior Astro migration plan is retired. Any future frontend replacement should be evaluated against current product needs and integrate with the canonical backend; it does not depend on restoring this port.
