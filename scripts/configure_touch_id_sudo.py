#!/usr/bin/env python3
"""Safely manage Apple's local Touch ID rule for sudo."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Optional

ACTIVE = re.compile(r"^\s*auth\s+sufficient\s+pam_tid\.so\s*$")
COMMENTED = re.compile(r"^\s*#\s*auth\s+sufficient\s+pam_tid\.so\s*$")
ENABLE_CONFIRM = "ENABLE-TOUCH-ID-FOR-SUDO"
ROLLBACK_CONFIRM = "RESTORE-SUDO-LOCAL"


class Refusal(RuntimeError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular_nonsymlink(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    except FileNotFoundError:
        return False


def read_safe(path: Path, label: str) -> bytes:
    if not regular_nonsymlink(path):
        raise Refusal(f"{label} must be a regular, non-symlink file: {path}")
    return path.read_bytes()


def require_system_metadata(path: Path, label: str) -> None:
    metadata = path.stat(follow_symlinks=False)
    mode = stat.S_IMODE(metadata.st_mode)
    if metadata.st_uid != 0 or metadata.st_gid != 0 or mode != 0o444:
        raise Refusal(f"{label} must be owned by root:wheel with mode 0444: {path}")


def line_counts(data: bytes) -> tuple[int, int]:
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise Refusal("PAM configuration is not valid UTF-8") from exc
    return (sum(bool(ACTIVE.match(x)) for x in lines), sum(bool(COMMENTED.match(x)) for x in lines))


def inspect(sudo: Path, template: Path, local: Path, enforce_system_metadata: bool = False) -> dict:
    sudo_data = read_safe(sudo, "sudo policy")
    if enforce_system_metadata:
        require_system_metadata(sudo, "sudo policy")
    if not re.search(rb"(?m)^\s*auth\s+include\s+sudo_local\s*$", sudo_data):
        raise Refusal("sudo policy does not include sudo_local")
    template_data = read_safe(template, "Apple sudo_local template")
    if enforce_system_metadata:
        require_system_metadata(template, "Apple sudo_local template")
    ta, tc = line_counts(template_data)
    if ta + tc != 1:
        raise Refusal("Apple template must contain exactly one pam_tid.so rule")
    result = {"template": "valid", "sudo_include": "valid", "target": "absent"}
    if not local.exists() and not local.is_symlink():
        result["source"] = template_data
        return result
    local_data = read_safe(local, "sudo_local")
    if enforce_system_metadata:
        require_system_metadata(local, "sudo_local")
    active, commented = line_counts(local_data)
    if active == 1 and commented == 0:
        result.update(target="enabled", source=local_data)
    elif active == 0 and commented == 1:
        result.update(target="disabled-template", source=local_data)
    else:
        raise Refusal("sudo_local is customized or has an ambiguous pam_tid.so rule")
    return result


def activate(data: bytes) -> bytes:
    text = data.decode("utf-8")
    lines = text.splitlines(keepends=True)
    matches = [i for i, line in enumerate(lines) if COMMENTED.match(line.rstrip("\r\n"))]
    active, _ = line_counts(data)
    if active == 1 and not matches:
        return data
    if active != 0 or len(matches) != 1:
        raise Refusal("source does not contain one safely activatable rule")
    ending = "\n" if lines[matches[0]].endswith("\n") else ""
    lines[matches[0]] = "auth       sufficient     pam_tid.so" + ending
    return "".join(lines).encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    fd, name = tempfile.mkstemp(prefix=".sudo_local.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chown(name, 0, 0)
        os.chmod(name, 0o444)
        os.replace(name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def require_root() -> None:
    if os.geteuid() != 0:
        raise Refusal("this operation requires administrator authorization (run with sudo)")


def create_backup(backup: Path, local: Path, installed: bytes) -> None:
    if not backup.is_absolute() or backup.exists() or backup.is_symlink():
        raise Refusal("backup directory must be a new absolute path")
    backup.mkdir(mode=0o700, parents=True)
    previous_exists = local.exists()
    previous_sha = None
    if previous_exists:
        previous = read_safe(local, "sudo_local")
        previous_sha = sha256(previous)
        (backup / "sudo_local.before").write_bytes(previous)
        os.chmod(backup / "sudo_local.before", 0o600)
    manifest = {"schema": 1, "target": str(local), "previous_exists": previous_exists,
                "previous_sha256": previous_sha, "installed_sha256": sha256(installed)}
    (backup / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    os.chmod(backup / "manifest.json", 0o600)


def apply_change(state: dict, local: Path, backup: Path, confirmation: str) -> str:
    if confirmation != ENABLE_CONFIRM:
        raise Refusal(f"apply requires --confirm {ENABLE_CONFIRM}")
    require_root()
    if state["target"] == "enabled":
        return "already enabled; no files changed"
    installed = activate(state["source"])
    create_backup(backup, local, installed)
    atomic_write(local, installed)
    return f"enabled; backup: {backup}"


def rollback(backup: Path, confirmation: str, expected_target: Path = Path("/etc/pam.d/sudo_local")) -> str:
    if confirmation != ROLLBACK_CONFIRM:
        raise Refusal(f"rollback requires --confirm {ROLLBACK_CONFIRM}")
    require_root()
    manifest = json.loads(read_safe(backup / "manifest.json", "backup manifest").decode("utf-8"))
    if manifest.get("schema") != 1:
        raise Refusal("unsupported backup manifest")
    target = Path(manifest["target"])
    if target != expected_target:
        raise Refusal(f"backup target is not the expected sudo_local path: {expected_target}")
    current = read_safe(target, "current sudo_local")
    if sha256(current) != manifest["installed_sha256"]:
        raise Refusal("current sudo_local changed after installation; refusing rollback")
    if manifest["previous_exists"]:
        previous = read_safe(backup / "sudo_local.before", "backup file")
        if sha256(previous) != manifest["previous_sha256"]:
            raise Refusal("backup integrity check failed")
        atomic_write(target, previous)
        return "restored previous sudo_local"
    target.unlink()
    return "removed the unchanged sudo_local installed by this tool"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--confirm", default="")
    p.add_argument("--backup-dir", type=Path)
    p.add_argument("--rollback", type=Path)
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.rollback:
            if sys.platform != "darwin":
                raise Refusal("this tool supports macOS only")
            print(f"APPLIED: {rollback(args.rollback, args.confirm)}")
            return 0
        sudo_file = Path("/etc/pam.d/sudo")
        template_file = Path("/etc/pam.d/sudo_local.template")
        local_file = Path("/etc/pam.d/sudo_local")
        if sys.platform != "darwin":
            raise Refusal("this tool supports macOS only")
        state = inspect(sudo_file, template_file, local_file, enforce_system_metadata=True)
        print(f"VERIFIED: sudo_local include={state['sudo_include']}; template={state['template']}; target={state['target']}")
        if args.apply:
            if args.backup_dir is None:
                raise Refusal("--apply requires --backup-dir")
            print(f"APPLIED: {apply_change(state, local_file, args.backup_dir, args.confirm)}")
        return 0
    except (Refusal, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
