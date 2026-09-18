"""Behavioral checks for distribution drift and invalid source references."""

import importlib.util
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/package_skill.py"
SPEC = importlib.util.spec_from_file_location("package_skill", SCRIPT)
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fable-package-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.skill = self.root / "skills/fable-mode"
        (self.skill / "references").mkdir(parents=True)
        (self.root / "README.md").write_text("[Skill](skills/fable-mode/SKILL.md)\n")
        (self.skill / "SKILL.md").write_text("[Guide](references/guide.md)\n")
        (self.skill / "references/guide.md").write_text("# Guide\n")

    def build(self):
        files = package.source_files(self.root)
        package.check_links(self.root, files)
        package.build_archive(self.root, files)
        return files

    def test_nested_resources_and_reproducible_build(self):
        files = self.build()
        archive = self.root / package.ARCHIVE
        before = archive.read_bytes()
        (self.skill / "references/guide.md").touch()
        package.build_archive(self.root, files)
        self.assertEqual(archive.read_bytes(), before)
        package.check_archive(self.root, files)

    def test_changed_content_and_missing_members_are_detected(self):
        files = self.build()
        (self.skill / "references/guide.md").write_text("# Changed\n")
        with self.assertRaisesRegex(ValueError, "content differs"):
            package.check_archive(self.root, files)
        (self.skill / "references/new.md").write_text("# New\n")
        with self.assertRaisesRegex(ValueError, "members differ"):
            package.check_archive(self.root, package.source_files(self.root))

    def test_missing_reference_and_outside_link_are_detected(self):
        (self.skill / "references/guide.md").unlink()
        with self.assertRaisesRegex(ValueError, "Invalid local link"):
            package.check_links(self.root, package.source_files(self.root))
        (self.skill / "SKILL.md").write_text("[Outside](../../../outside.md)\n")
        with self.assertRaisesRegex(ValueError, "Invalid local link"):
            package.check_links(self.root, package.source_files(self.root))

    def test_duplicate_and_unsafe_archive_names_are_rejected(self):
        files = self.build()
        archive = self.root / package.ARCHIVE
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with ZipFile(archive, "a", compression=ZIP_DEFLATED) as zipped:
                zipped.writestr("fable-mode/SKILL.md", "duplicate")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            package.check_archive(self.root, files)
        package.build_archive(self.root, files)
        with ZipFile(archive, "a") as zipped:
            zipped.writestr("../outside.md", "unexpected")
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            package.check_archive(self.root, files)

    def test_source_symlink_is_rejected(self):
        (self.skill / "references/linked.md").symlink_to(self.skill / "SKILL.md")
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            package.source_files(self.root)

    def test_symlink_archive_member_is_rejected(self):
        files = self.build()
        with ZipFile(self.root / package.ARCHIVE, "w") as archive:
            for path in files:
                info = ZipInfo(path.relative_to(self.root / "skills").as_posix())
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, path.read_bytes())
        with self.assertRaisesRegex(ValueError, "not a regular file"):
            package.check_archive(self.root, files)

    def test_cli_check_is_read_only_and_invalid_build_preserves_archive(self):
        self.build()
        archive = self.root / package.ARCHIVE
        before = archive.read_bytes()
        modified = archive.stat().st_mtime_ns
        scripts = self.root / "scripts"
        scripts.mkdir()
        script = scripts / "package_skill.py"
        shutil.copyfile(SCRIPT, script)
        result = subprocess.run([sys.executable, str(script), "--check"], cwd=self.root.parent,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(archive.stat().st_mtime_ns, modified)
        self.assertEqual(archive.read_bytes(), before)
        (self.skill / "references/guide.md").unlink()
        result = subprocess.run([sys.executable, str(script), "--build"], cwd=self.root.parent,
                                capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(archive.read_bytes(), before)

    def test_cli_build_can_recreate_the_linked_archive(self):
        (self.root / "README.md").write_text("[Download](dist/fable-mode.zip)\n")
        scripts = self.root / "scripts"
        scripts.mkdir()
        script = scripts / "package_skill.py"
        shutil.copyfile(SCRIPT, script)
        result = subprocess.run([sys.executable, str(script), "--build"], cwd=self.root.parent,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        package.check_links(self.root, package.source_files(self.root))
        package.check_archive(self.root, package.source_files(self.root))

    def test_invalid_source_name_preserves_existing_archive(self):
        self.build()
        archive = self.root / package.ARCHIVE
        before = archive.read_bytes()
        (self.skill / "bad\\name.md").write_text("invalid portable name")
        scripts = self.root / "scripts"
        scripts.mkdir()
        script = scripts / "package_skill.py"
        shutil.copyfile(SCRIPT, script)
        result = subprocess.run([sys.executable, str(script), "--build"], cwd=self.root.parent,
                                capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsafe archive member", result.stderr)
        self.assertEqual(archive.read_bytes(), before)

    def test_invalid_staged_archive_preserves_existing_archive(self):
        files = self.build()
        archive = self.root / package.ARCHIVE
        before = archive.read_bytes()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                package.build_archive(self.root, files + [files[0]])
        self.assertEqual(archive.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
