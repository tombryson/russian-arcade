# Security

## Deployment modes

Local profiles are intended for a trusted installation. They are not internet accounts. Do not expose the development server or the local profile selector directly to the internet.

The hosted entry point supports two modes:

- **Private installation:** HTTPS and site credentials protect all application routes and assets.
- **Public sample demo:** a disposable database contains authored sample content. Each browser receives a separate profile. An explicit route list permits sample practice. AI generation, uploads, editing and profile switching are blocked. Provider credentials are blanked during startup.

The anonymous demo limits requests and writes in SQLite. Limits are shared across threads and browser sessions. New profiles have a separate admission limit and an atomic total cap. No IP addresses are stored. These controls bound application work; they do not replace an edge firewall or protect against every denial-of-service attack.

Demo limits reset when its disposable database is recreated. They must not be used as a spending ledger. Paid AI remains disabled until verified identities, persistent cost reservations, provider limits and dedicated credentials are configured. See the [AI demo plan](docs/public-release-and-ai-demo.md).

## Credentials and publication

Keep credentials in ignored local environment files or the hosting provider's secret store. Never send them to the browser, put them in generated content or print them in logs. `.gitignore` prevents ordinary staging of local files; it does not remove secrets from old commits.

The original private development repository contains sensitive historical files. It must not be made public without a separate history cleanup. A new public repository should use a reviewed source snapshot and an independent history. Keep personal databases, tutor documents, recordings, OAuth files and environment files outside that snapshot.

For credentials that appeared in history, create replacements, update the installation, verify it, then revoke the old credentials. Preserve local environment files. An existing key's presence in history does not establish whether it has been misused.

## Automated checks

CI scans the committed source and incoming commit ranges with Gitleaks. It also audits the Python and JavaScript lockfiles. Reports redact detected credentials. Existing private history is not declared clean by these checks.

Before publishing a new repository, run a full-history scan in its clean checkout:

```sh
gitleaks git . --log-opts=--all --redact=100 --ignore-gitleaks-allow
```

Enable GitHub secret scanning and push protection where available. Review dependency alerts and rerun tests when updating the lockfiles. A passing scan cannot guarantee the absence of vulnerabilities or personal information.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting feature when it is enabled. Do not include credentials or personal learning data in a public issue. Until private reporting is available, contact the repository owner privately before sharing technical details.
