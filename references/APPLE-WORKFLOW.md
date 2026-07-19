# Apple-supported workflow

Apple documents a persistent local PAM customization for Touch ID and `sudo` in the macOS Sonoma enterprise release notes. The documented mechanism is to create `/etc/pam.d/sudo_local` from `/etc/pam.d/sudo_local.template` and uncomment the `pam_tid.so` line. Apple says the local file is preserved across software updates.

Primary source: [What's new for enterprise in macOS Sonoma](https://support.apple.com/en-in/109030), under **Bug fixes and other improvements**.

The expected template rule is:

    auth       sufficient     pam_tid.so

`sufficient` allows successful Touch ID authentication to authorize the request while leaving the later password-based PAM rules intact as fallback. The script verifies that `/etc/pam.d/sudo` includes `sudo_local`, but it never edits Apple's system policy file.

Apple's documentation describes the configuration surface, not a guarantee that a Touch ID prompt is available in every execution context. Verify the user-visible behavior separately with a fresh interactive sudo credential request.
