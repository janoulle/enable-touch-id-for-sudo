## What

Describe the user-visible behavior or maintenance outcome that changes.

## Why

Explain the evidence or risk that motivated the change and why it matters.

## How

Describe the PAM boundary, privilege model, backup and rollback behavior, and meaningful tradeoffs.

## How I validated it

Describe tested macOS versions and scenarios. State untested paths and remaining risks.

## Security checklist

- [ ] The change never edits `/etc/pam.d/sudo`.
- [ ] Password fallback and the exact `auth sufficient pam_tid.so` rule remain intact.
- [ ] Symlink, metadata, confirmation, privilege, backup, and rollback guards are preserved.
- [ ] Tests cover new authentication-policy or recovery behavior.
- [ ] No machine-specific PAM data, backups, usernames, credentials, or private paths are included.
- [ ] Canonical and public distributable files are reconciled.
