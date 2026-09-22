# Public release procedure

The public `russian-arcade` repository has an independent history. The older development repository stays private because its history contains credentials and personal files. Never merge its Git history into the public repository.

## Prepare and review a snapshot

Run the exporter from the development repository. Its default mode is read-only:

```sh
python scripts/release_snapshot.py \
  --compare /path/to/russian-arcade \
  --report /tmp/russian-arcade-release-report.json
```

The report lists added, changed and omitted paths, plus file sizes and SHA256 hashes. It includes tracked and untracked source files so new migrations, tests and assets are not missed. Ignored runtime data is not included. Files are checked against source locations and a separate exclusion policy even if they were accidentally tracked.

The export excludes Git history, environment files other than `.env.example`, credentials, databases, backups, tutor documents, uploads, learner recordings, generated learning media, dependency folders, build output and `.codex`. Bundled application artwork, authored delivery audio and the authored course recordings in `flask_vocab_app/static/audio/course/` remain part of the source release. Include the course audio manifest and verify that the exported source and deployment build contain every checkpoint clip. A path allowlist is not a substitute for reviewing the content of newly added files.

Review the report before copying anything into the public checkout. Check omitted paths as carefully as new files. Read the README and changed feature guides against the actual implementation. Future work must not be described as already enabled in the hosted demo.

## Scan and stage the release

Use a verified Gitleaks binary. The CI workflow pins version 8.30.1 and checks its download checksum. Install the corresponding verified binary for the local platform, then run:

```sh
python scripts/release_snapshot.py \
  --compare /path/to/russian-arcade \
  --scan --gitleaks /path/to/gitleaks \
  --output /tmp/russian-arcade-release-source \
  --report /tmp/russian-arcade-release-report.json
```

The output directory must be new and outside the source repository. The command refuses to overwrite an existing checkout. It scans a temporary source snapshot with redacted reporting before exporting. A failed scan prevents export. If source files change between the scan and copy, the command stops; discard that staging directory and rerun after the changes settle.

The report records scanner status and finding locations without matched secrets. No `.git` directory is copied, and the script does not commit, push, deploy or edit environment files. Keep the report outside both source trees.

## Validate and publish

Build and test the staged source using the locked dependencies and the commands in the development guide. The application checks include:

```sh
npm ci --prefix flask_vocab_app/ui
npm run build --prefix flask_vocab_app/ui
npm test --prefix flask_vocab_app/ui
PYTHONDONTWRITEBYTECODE=1 WORD_POST_REQUIRE_BUILD=1 \
  python -m unittest discover -s flask_vocab_app/tests -t flask_vocab_app -v
```

Compare the final snapshot with the public checkout. Copy only reviewed files into that checkout, retaining its own `.git` directory. Apply reviewed removals explicitly. Then inspect the diff, repeat the secret scan, commit in the public repository and let CI complete before deployment.

For Fly.io, follow the [hosting runbook](operations-fly.md). Back up persistent stores before migrations. Verify the deployed version, headers, sample routes, media and profile isolation after deployment. Source publication does not automatically enable funded AI; that requires its separate identity, admission, spending and provider controls.
