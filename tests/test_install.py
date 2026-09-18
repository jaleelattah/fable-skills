"""Installer regression checks; every install uses an isolated temporary directory."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SHELL = os.environ.get("FABLE_TEST_SHELL", "sh")


def tree_snapshot(root):
    """Include directory types and file bytes to detect partial changes."""
    if not root.exists():
        return None
    return {
        path.relative_to(root).as_posix(): None if path.is_dir() else path.read_bytes()
        for path in root.rglob("*")
    }


@unittest.skipUnless(shutil.which(SHELL), "A POSIX shell is required")
class ShellInstallerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="fable-install-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = self.root / "source repository"
        self.fixture.mkdir()
        self.script = self.fixture / "install.sh"
        shutil.copyfile(REPO / "install.sh", self.script)
        self.source = self.fixture / "skills" / "fable-mode"
        shutil.copytree(REPO / "skills" / "fable-mode", self.source)
        self.working = self.root / "working directory"
        self.working.mkdir()
        self.skills_parent = self.working / "installed skills"
        self.destination = self.skills_parent / "fable-mode"

    def run_install(self, *arguments):
        return subprocess.run(
            [SHELL, str(self.script), *arguments],
            cwd=self.working,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def force_install(self):
        return self.run_install("--skills-dir", str(self.skills_parent), "--force")

    def test_option_tokens_are_rejected_as_missing_values(self):
        before = tree_snapshot(self.working)
        for option in ("--target", "--skills-dir"):
            for token in ("--target", "--skills-dir", "--force", "--help", "-h"):
                with self.subTest(option=option, token=token):
                    result = self.run_install(option, token)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn("needs a value", result.stderr)
                    self.assertEqual(tree_snapshot(self.working), before)

    def test_fresh_install_with_relative_spaces(self):
        result = self.run_install("--skills-dir", "installed skills")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tree_snapshot(self.destination), tree_snapshot(self.source))

    def test_explicit_flag_like_directory_is_valid(self):
        result = self.run_install("--skills-dir", "./--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            tree_snapshot(self.working / "--force" / "fable-mode"),
            tree_snapshot(self.source),
        )

    def test_existing_install_requires_force(self):
        self.destination.mkdir(parents=True)
        (self.destination / "SKILL.md").write_text("old skill")
        before = tree_snapshot(self.destination)
        result = self.run_install("--skills-dir", str(self.skills_parent))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Already exists", result.stderr)
        self.assertEqual(tree_snapshot(self.destination), before)

    def test_forced_update_preserves_extra_files(self):
        shutil.copytree(self.source, self.destination)
        (self.destination / "SKILL.md").write_text("old skill")
        (self.destination / "references" / "personal.md").write_text("keep this")
        (self.destination / ".personal").write_text("keep this too")
        expected = tree_snapshot(self.source)
        expected["references/personal.md"] = b"keep this"
        expected[".personal"] = b"keep this too"
        result = self.force_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tree_snapshot(self.destination), expected)

    def assert_conflict_is_unchanged(self):
        before = tree_snapshot(self.destination)
        result = self.force_install()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("Destination type conflict", result.stderr)
        self.assertEqual(tree_snapshot(self.destination), before)

    def test_directory_source_conflict_does_not_overwrite_skill(self):
        self.destination.mkdir(parents=True)
        (self.destination / "SKILL.md").write_text("old skill")
        (self.destination / "references").write_text("user file")
        self.assert_conflict_is_unchanged()

    def test_file_source_conflict_does_not_copy_other_files(self):
        (self.destination / "SKILL.md").mkdir(parents=True)
        (self.destination / "SKILL.md" / "personal.md").write_text("user file")
        self.assert_conflict_is_unchanged()

    def test_nested_hidden_conflict_is_checked_before_copying(self):
        (self.source / "references" / ".nested").mkdir()
        (self.source / "references" / ".nested" / "guide.md").write_text("new guide")
        (self.destination / "references").mkdir(parents=True)
        (self.destination / "SKILL.md").write_text("old skill")
        (self.destination / "references" / ".nested").write_text("user file")
        self.assert_conflict_is_unchanged()


if __name__ == "__main__":
    unittest.main()
