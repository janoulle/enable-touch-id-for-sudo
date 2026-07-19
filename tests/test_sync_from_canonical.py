import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_from_canonical.py"
SPEC = importlib.util.spec_from_file_location("sync_from_canonical", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source, self.mirror = self.root / "source", self.root / "mirror"
        for path in MODULE.FILES:
            target = self.source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"content for {path}\n")

    def tearDown(self):
        self.temp.cleanup()

    def test_apply_then_check_is_clean(self):
        differences = MODULE.sync(self.source, self.mirror, True)
        self.assertEqual(set(differences), set(MODULE.FILES.values()))
        self.assertEqual(MODULE.sync(self.source, self.mirror, False), [])

    def test_check_detects_changed_file_without_overwriting(self):
        MODULE.sync(self.source, self.mirror, True)
        target = self.mirror / "SKILL.md"
        target.write_text("public change\n")
        self.assertIn("SKILL.md", MODULE.sync(self.source, self.mirror, False))
        self.assertEqual(target.read_text(), "public change\n")

    def test_incomplete_source_is_refused(self):
        (self.source / "SKILL.md").unlink()
        with self.assertRaises(SystemExit):
            MODULE.validate_source(self.source)


if __name__ == "__main__":
    unittest.main()
