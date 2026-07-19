#!/usr/bin/env python3

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import configure_touch_id_sudo as tool

SUDO = b"auth       include        sudo_local\nauth required pam_opendirectory.so\n"
TEMPLATE = b"# local config\n#auth       sufficient     pam_tid.so\n"
ENABLED = b"# local config\nauth       sufficient     pam_tid.so\n"


class ConfigureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.sudo, self.template, self.local = self.root / "sudo", self.root / "sudo_local.template", self.root / "sudo_local"
        self.sudo.write_bytes(SUDO)
        self.template.write_bytes(TEMPLATE)

    def tearDown(self): self.tmp.cleanup()

    def test_absent_target_uses_template(self):
        state = tool.inspect(self.sudo, self.template, self.local)
        self.assertEqual(state["target"], "absent")
        self.assertEqual(tool.activate(state["source"]), ENABLED)

    def test_enabled_target_is_noop(self):
        self.local.write_bytes(ENABLED)
        with mock.patch.object(tool, "require_root"):
            result = tool.apply_change(tool.inspect(self.sudo, self.template, self.local), self.local, self.root / "unused", tool.ENABLE_CONFIRM)
        self.assertIn("already enabled", result)
        self.assertFalse((self.root / "unused").exists())

    def test_commented_target_is_accepted(self):
        self.local.write_bytes(TEMPLATE)
        self.assertEqual(tool.inspect(self.sudo, self.template, self.local)["target"], "disabled-template")

    def test_duplicate_rules_refused(self):
        self.local.write_bytes(ENABLED + ENABLED)
        with self.assertRaises(tool.Refusal): tool.inspect(self.sudo, self.template, self.local)

    def test_symlink_refused(self):
        other = self.root / "other"; other.write_bytes(TEMPLATE); self.local.symlink_to(other)
        with self.assertRaises(tool.Refusal): tool.inspect(self.sudo, self.template, self.local)

    def test_missing_include_refused(self):
        self.sudo.write_text("auth required pam_opendirectory.so\n")
        with self.assertRaises(tool.Refusal): tool.inspect(self.sudo, self.template, self.local)

    def test_insecure_metadata_refused_when_enforced(self):
        self.local.write_bytes(ENABLED)
        with self.assertRaises(tool.Refusal):
            tool.inspect(self.sudo, self.template, self.local, enforce_system_metadata=True)

    def test_confirmation_and_root_guards(self):
        state = tool.inspect(self.sudo, self.template, self.local)
        with self.assertRaises(tool.Refusal): tool.apply_change(state, self.local, self.root / "b", "wrong")
        with mock.patch("os.geteuid", return_value=501), self.assertRaises(tool.Refusal):
            tool.apply_change(state, self.local, self.root / "b", tool.ENABLE_CONFIRM)

    def test_apply_backs_up_then_writes(self):
        self.local.write_bytes(TEMPLATE); backup = self.root / "backup"
        with mock.patch.object(tool, "require_root"), mock.patch.object(tool, "atomic_write") as write:
            tool.apply_change(tool.inspect(self.sudo, self.template, self.local), self.local, backup, tool.ENABLE_CONFIRM)
            self.assertTrue((backup / "sudo_local.before").exists()); write.assert_called_once_with(self.local, ENABLED)
        self.assertEqual(json.loads((backup / "manifest.json").read_text())["previous_sha256"], tool.sha256(TEMPLATE))

    def make_manifest(self, previous_exists, previous=None):
        backup = self.root / "backup"; backup.mkdir(); self.local.write_bytes(ENABLED)
        manifest = {"schema": 1, "target": str(self.local), "previous_exists": previous_exists,
                    "previous_sha256": tool.sha256(previous) if previous else None, "installed_sha256": tool.sha256(ENABLED)}
        (backup / "manifest.json").write_text(json.dumps(manifest))
        if previous is not None: (backup / "sudo_local.before").write_bytes(previous)
        return backup

    def test_rollback_restores_existing(self):
        backup = self.make_manifest(True, TEMPLATE)
        with mock.patch.object(tool, "require_root"), mock.patch.object(tool, "atomic_write") as write: tool.rollback(backup, tool.ROLLBACK_CONFIRM, self.local)
        write.assert_called_once_with(self.local, TEMPLATE)

    def test_rollback_removes_previously_absent(self):
        backup = self.make_manifest(False)
        with mock.patch.object(tool, "require_root"): tool.rollback(backup, tool.ROLLBACK_CONFIRM, self.local)
        self.assertFalse(self.local.exists())

    def test_rollback_refuses_changed_current(self):
        backup = self.make_manifest(False); self.local.write_text("changed\n")
        with mock.patch.object(tool, "require_root"), self.assertRaises(tool.Refusal): tool.rollback(backup, tool.ROLLBACK_CONFIRM, self.local)

    def test_rollback_refuses_redirected_target(self):
        backup = self.make_manifest(False)
        with mock.patch.object(tool, "require_root"), self.assertRaises(tool.Refusal):
            tool.rollback(backup, tool.ROLLBACK_CONFIRM, self.root / "different")


if __name__ == "__main__": unittest.main()
