#!/usr/bin/env python3
"""Build or check the repository's portable Fable Mode skill archive."""

import argparse
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from urllib.parse import unquote, urlsplit
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
SKILL = Path("skills/fable-mode")
ARCHIVE = Path("dist/fable-mode.zip")


def check_member_name(name):
    if "\\" in name or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts:
        raise ValueError(f"Unsafe archive member name: {name}")


def source_files(root):
    skill = root / SKILL
    if skill.is_symlink():
        raise ValueError("Skill source directory is a symbolic link")
    if not (skill / "SKILL.md").is_file():
        raise ValueError("Missing skills/fable-mode/SKILL.md")
    files = []
    for path in sorted(skill.rglob("*")):
        if "__pycache__" in path.parts or path.name == ".DS_Store":
            continue
        if path.is_symlink():
            raise ValueError(f"Skill source contains a symbolic link: {path.relative_to(root)}")
        if path.is_file():
            check_member_name(path.relative_to(root / "skills").as_posix())
            files.append(path)
    return files


def check_links(root, files, allow_generated_archive=False):
    """Check this repo's inline local link targets; skip URLs and fragments."""
    documents = [root / "README.md", *sorted((root / "docs").rglob("*.md"))]
    documents.extend(path for path in files if path.suffix == ".md")
    for document in documents:
        content = document.read_text(encoding="utf-8")
        content = re.sub(r"^```[^\n]*\n.*?^```[^\n]*$", "", content, flags=re.M | re.S)
        for raw in re.findall(r"\[[^\]]*\]\(([^)\n]+)\)", content):
            target = raw.strip()
            if not target:
                continue
            target = target[1:target.index(">")] if target.startswith("<") else target.split()[0]
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            resolved = (document.parent / unquote(parts.path)).resolve()
            generated = allow_generated_archive and resolved == (root / ARCHIVE).resolve()
            if not resolved.is_relative_to(root) or (not resolved.exists() and not generated):
                raise ValueError(f"Invalid local link in {document.relative_to(root)}: {target}")


def check_archive(root, files, archive_path=None):
    expected = {path.relative_to(root / "skills").as_posix(): path for path in files}
    with ZipFile(archive_path if archive_path is not None else root / ARCHIVE) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Archive contains duplicate member names")
        for name in names:
            check_member_name(name)
        missing = sorted(set(expected) - set(names))
        extra = sorted(set(names) - set(expected))
        if missing or extra:
            raise ValueError(f"Archive members differ from source: missing={missing}, extra={extra}")
        for name, path in expected.items():
            info = archive.getinfo(name)
            if stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG):
                raise ValueError(f"Archive member is not a regular file: {name}")
            data = path.read_bytes()
            if info.file_size != len(data) or archive.read(name) != data:
                raise ValueError(f"Archive content differs from source: {name}")


def build_archive(root, files):
    destination = root / ARCHIVE
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".zip", delete=False) as handle:
        staging = Path(handle.name)
    try:
        with ZipFile(staging, "w", compression=ZIP_DEFLATED) as archive:
            for path in files:
                info = ZipInfo(path.relative_to(root / "skills").as_posix(), (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
                info.external_attr = (0o100000 | mode) << 16
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
        check_archive(root, files, archive_path=staging)
        staging.replace(destination)
    finally:
        staging.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--build", action="store_true", help="validate sources, then rebuild the ZIP")
    mode.add_argument("--check", action="store_true", help="check the existing ZIP (default; no writes)")
    args = parser.parse_args()
    try:
        files = source_files(ROOT)
        check_links(ROOT, files, allow_generated_archive=args.build)
        if args.build:
            build_archive(ROOT, files)
            check_links(ROOT, files)
        check_archive(ROOT, files)
    except (OSError, ValueError, BadZipFile) as error:
        parser.exit(1, f"Package validation failed: {error}\n")
    print(f"Package {'built and checked' if args.build else 'checked'}: {len(files)} skill files; local links resolve.")


if __name__ == "__main__":
    main()
