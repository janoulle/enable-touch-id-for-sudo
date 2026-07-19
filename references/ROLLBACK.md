# Rollback

Every change creates a dedicated backup directory containing `manifest.json` and, when a prior `sudo_local` existed, its exact bytes as `sudo_local.before`.

Before rollback, the script compares the current file with the installed SHA-256 recorded in the manifest. It refuses rollback if another process or administrator changed the file afterward.

Run:

    sudo python3 scripts/configure_touch_id_sudo.py \
      --rollback /absolute/path/to/backup \
      --confirm RESTORE-SUDO-LOCAL

If the file existed before enablement, rollback restores it atomically. If it did not exist, rollback removes only the exact unchanged file installed by this tool. Re-run the audit afterward; a missing `sudo_local` is a valid disabled state when Apple's template and include remain intact.
