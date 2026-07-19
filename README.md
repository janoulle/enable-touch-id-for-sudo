# Enable Touch ID for sudo

A safety-focused Codex skill and standalone Python tool for enabling Touch ID authentication for `sudo` through Apple's update-persistent `/etc/pam.d/sudo_local` workflow.

This repository is a curated public mirror of one version-controlled skill. It contains the distributable skill, deterministic tooling, tests, and community documentation—not personal configuration or machine audit data. See [MIRRORING.md](MIRRORING.md).

> [!CAUTION]
> PAM controls authentication. An invalid configuration can disrupt administrator access. This project never edits `/etc/pam.d/sudo`, preserves password fallback, audits before changing anything, and refuses ambiguous or insecure files. Keep the generated backup until rollback is no longer needed.

## What it does

Apple documents `/etc/pam.d/sudo_local` as the persistent configuration surface for allowing Touch ID with `sudo`. This project verifies Apple's include and template, then activates only the template's exact `auth sufficient pam_tid.so` rule.

The tool supports three explicit operations:

- audit the Apple policy, template, local rule, ownership, permissions, and activation state;
- enable Touch ID after a literal confirmation phrase and integrity-checked backup;
- roll back only when the current file still matches what the tool installed.

Password authentication remains available when Touch ID is unavailable or unsuccessful.

## Requirements

- macOS Sonoma 14 or later
- a Mac and account with Touch ID configured
- Python 3.10 or later
- administrator authorization for enablement or rollback
- Codex for skill-driven use; the Python tool can also run directly

No third-party Python packages are required.

## Install as a Codex skill

```bash
git clone https://github.com/janoulle/enable-touch-id-for-sudo.git \
  ~/.codex/skills/enable-touch-id-for-sudo
```

Then invoke `$enable-touch-id-for-sudo` in Codex.

## Audit first

```bash
python3 scripts/configure_touch_id_sudo.py
```

Audit mode is read-only and does not require `sudo`. Continue only when it reports `VERIFIED`.

## Enable

Choose a new absolute backup path. The directory must not already exist.

```bash
sudo python3 scripts/configure_touch_id_sudo.py \
  --apply \
  --confirm ENABLE-TOUCH-ID-FOR-SUDO \
  --backup-dir /absolute/path/to/touch-id-sudo-backup
```

Re-run the audit, then test a fresh interactive authorization request:

```bash
sudo -k
sudo -v
```

File inspection verifies configuration, not whether macOS presented and accepted the biometric prompt.

## Safety model

- macOS-only execution;
- exact verification of Apple's `sudo_local` include and template rule;
- root ownership, wheel group, and mode `0444` required for PAM policy files;
- rejection of symlinks, duplicate rules, custom rules, and malformed UTF-8;
- no edits to `/etc/pam.d/sudo`;
- `sufficient`, never `required`, so password fallback remains intact;
- literal apply and rollback confirmation phrases;
- root enforcement for every mutation;
- atomic installation as `root:wheel`, mode `0444`;
- SHA-256 backup metadata and changed-state rollback refusal;
- rollback target pinned to `/etc/pam.d/sudo_local`.

Read [the Apple workflow](references/APPLE-WORKFLOW.md), [rollback procedure](references/ROLLBACK.md), and [FAQ](FAQ.md) before changing authentication policy.

## Validation

```bash
python3 scripts/test_configure_touch_id_sudo.py -v
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/configure_touch_id_sudo.py \
  scripts/test_configure_touch_id_sudo.py scripts/sync_from_canonical.py
```

GitHub Actions runs the suite on macOS with supported Python versions.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes. Report authentication, privilege, path, backup, or rollback vulnerabilities privately according to [SECURITY.md](SECURITY.md).

## License

Licensed under the [Apache License 2.0](LICENSE).

This is an independent open-source project and is not affiliated with or endorsed by Apple Inc.
