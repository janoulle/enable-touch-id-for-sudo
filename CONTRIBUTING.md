# Contributing

Contributions are welcome when they preserve the project's fail-closed authentication model.

## Before opening a pull request

1. Open an issue before changing PAM semantics, supported paths, privilege behavior, file metadata, backup format, or rollback behavior.
2. Keep machine-specific PAM contents, usernames, audit output, backups, and absolute home paths out of the repository.
3. Add regression tests for every security boundary or behavior change.
4. Reconcile distributable changes with the canonical source and run the mirror check in [MIRRORING.md](MIRRORING.md).
5. Run the validation commands in [README.md](README.md).
6. Explain the threat model, recovery behavior, macOS versions tested, and untested scenarios.

## Safety invariants

Changes must not:

- edit `/etc/pam.d/sudo`;
- follow symlinks or accept ambiguous PAM rules;
- remove password fallback or change `pam_tid.so` to `required`;
- mutate without root, explicit confirmation, and a prior backup;
- restore to a target other than `/etc/pam.d/sudo_local`;
- bypass ownership, permission, hash, or changed-state checks;
- claim biometric success based only on file inspection.

## Pull request descriptions

Use **What**, **Why**, **How**, and **How I validated it** sections. State compatibility gaps and remaining risks directly.

By contributing, you agree that your contribution is licensed under Apache License 2.0.
