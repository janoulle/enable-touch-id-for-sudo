# Frequently asked questions

## Is this workflow documented by Apple?

Yes. Apple's macOS Sonoma enterprise release notes say Touch ID can be allowed for `sudo` using `/etc/pam.d/sudo_local`, that the configuration persists across software updates, and that `/etc/pam.d/sudo_local.template` provides the details. See [the Apple workflow reference](references/APPLE-WORKFLOW.md).

## Why not edit `/etc/pam.d/sudo` directly?

Apple provides `sudo_local` specifically for local, update-persistent customization. Editing the system policy increases upgrade and recovery risk. This tool verifies the include but never changes that file.

## Does this replace my sudo password?

No. The template rule uses PAM's `sufficient` control behavior. Successful Touch ID can authorize the request, while the existing password stack remains available as fallback.

## Why does enablement still run through `sudo`?

Touch ID is an authentication method, not a replacement for macOS authorization or file ownership. `/etc/pam.d` is system-owned, so changing `sudo_local` requires administrator privileges. After configuration, Touch ID can satisfy eligible future `sudo` authentication requests.

## Why didn't Touch ID appear?

First run `sudo -k` to invalidate cached credentials, then use `sudo -v` in an interactive local Terminal session. Touch ID availability depends on macOS, hardware, enrollment, session context, and device state. Password fallback should remain available.

## Does this work over SSH?

Do not depend on a biometric prompt in remote or otherwise noninteractive sessions. The project preserves the normal password path for contexts where Touch ID cannot be presented.

## Why does the tool refuse my existing `sudo_local`?

It changes only an absent file derived from Apple's template or a template-shaped file with one commented `pam_tid.so` rule. Custom, duplicate, symlinked, incorrectly owned, or unexpectedly permissioned files require manual expert review; the tool will not overwrite them.

## What is backed up?

The backup contains an exact copy of the prior `sudo_local` when one existed and a JSON manifest recording prior state plus SHA-256 hashes. A previously absent file is recorded explicitly.

## How do I undo the change?

Follow [references/ROLLBACK.md](references/ROLLBACK.md). Rollback refuses to proceed if the installed file changed afterward or the manifest attempts to redirect restoration elsewhere.

## Is this an Apple product?

No. It is an independent open-source project and is not affiliated with or endorsed by Apple Inc.
