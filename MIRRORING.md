# Public mirror policy

This repository is the curated public distribution of one reusable skill. Its canonical source is maintained in a private, version-controlled agent-configuration repository so multiple LLM harnesses can share one local implementation.

## Publication boundary

The mirror includes the distributable skill, generic references, deterministic script, tests, CI, issue templates, community policies, and licensing.

It must never include machine-specific PAM files, audit results, backups, usernames, absolute home paths, credentials, tokens, browser sessions, private repository metadata, unrelated skills, or private history.

## Refresh workflow

1. Update and validate the canonical skill first.
2. Run `scripts/sync_from_canonical.py --source /path/to/canonical-skill --check`.
3. Apply expected changes with `--apply`, then review every changed file.
4. Run unit tests, the skill validator, compile checks, whitespace checks, privacy scanning, and link validation.
5. Commit and publish only the curated mirror diff.

Public contributions are reconciled into the canonical source before release so the two copies do not silently diverge.
