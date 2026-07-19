---
name: enable-touch-id-for-sudo
description: Audit, enable, verify, or safely roll back Touch ID authentication for sudo on supported macOS versions using Apple's persistent /etc/pam.d/sudo_local template workflow. Use when a user wants biometric sudo authorization without removing password fallback or directly editing Apple's sudo PAM policy.
---

# Enable Touch ID for sudo

Use `scripts/configure_touch_id_sudo.py` to inspect and manage the single local PAM override Apple provides for this purpose.

## Workflow

1. Read [references/APPLE-WORKFLOW.md](references/APPLE-WORKFLOW.md) and confirm the Mac exposes both `/etc/pam.d/sudo_local.template` and a `sudo_local` include in `/etc/pam.d/sudo`.
2. Run the script without a mutation flag. Report the detected state and stop if any check is `REFUSED`.
3. Before enabling, tell the user that the operation writes `/etc/pam.d/sudo_local`, retains password authentication as fallback, creates an integrity-checked backup, and requires administrator authorization. Obtain explicit approval.
4. Enable with `sudo python3 scripts/configure_touch_id_sudo.py --apply --confirm ENABLE-TOUCH-ID-FOR-SUDO --backup-dir <absolute-directory>`.
5. Re-run the audit and perform a fresh `sudo -k; sudo -v` interactively. Do not claim biometric verification from file inspection alone.
6. For rollback, read [references/ROLLBACK.md](references/ROLLBACK.md), inspect the backup manifest, then use the guarded rollback command.

## Boundaries

- Never edit `/etc/pam.d/sudo` or bypass Apple's `sudo_local.template` mechanism.
- Never replace a customized, ambiguous, duplicated, symlinked, or unrecognized `sudo_local` file.
- Activate only the exact `auth sufficient pam_tid.so` rule supplied by Apple's template.
- Preserve password fallback. Do not add `pam_tid.so` as `required` and do not alter the remaining sudo PAM stack.
- Do not promise Touch ID in environments where macOS cannot present it, including some remote or closed-lid sessions; password fallback remains available.
- Treat PAM configuration as security-sensitive. Back up before mutation, write atomically, and fail closed on changed-state rollback.

## Validate

    python3 -m py_compile scripts/configure_touch_id_sudo.py scripts/test_configure_touch_id_sudo.py
    python3 scripts/test_configure_touch_id_sudo.py -v
    python3 /path/to/skill-creator/scripts/quick_validate.py .
