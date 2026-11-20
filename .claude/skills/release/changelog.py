#!/usr/bin/env python3
"""Show the "unreleased" CHANGELOG section with the commits to draft its entries from, or write the entries.

Without arguments it prints the top section of CHANGELOG.md. When the section has entries it prints "entries: yes"
and exits 0. Otherwise it prints "entries: none", the commits since the last release tag (except "Bump version"
commits) as "<hash> <subject> [addon|dev]" with their changed files, and "addon changes: yes|no", and exits 1.
A commit is "addon" when it changes a file that ships in the .ankiaddon package.

"write <entry>..." numbers the entries under the "unreleased" heading, commits CHANGELOG.md and pushes "main".
It prints the new section and exits 0, or prints the error and exits 2.
Run from the repository root: changelog.py [write <entry>...]
"""
import re
import subprocess
import sys
from pathlib import Path

from versions import last_release

CHANGELOG = Path("CHANGELOG.md")
UNRELEASED_HEADING = re.compile(r"## v(\d+\.\d+\.\d+) - unreleased")
PACKAGED_FILES = re.compile(r"extra_browser_columns/.*|README\.md|LICENSE|build_dist\.py")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(2)


def top_section(lines: list[str]) -> tuple[int, int]:
    """Line indexes of the top section: its heading and the next section's heading (or the end)."""
    headings = [i for i, line in enumerate(lines) if line.startswith("## ")]
    if not headings:
        fail("CHANGELOG.md has no sections")
    return headings[0], headings[1] if len(headings) > 1 else len(lines)


def unreleased_section(lines: list[str]) -> tuple[str, int, int]:
    """The version of the "unreleased" top section and its line indexes (see `top_section`)."""
    start, end = top_section(lines)
    match = UNRELEASED_HEADING.fullmatch(lines[start])
    if not match:
        fail(f'CHANGELOG.md: the top section must be "## vX.Y.Z - unreleased", found: {lines[start]}')
    return match[1], start, end


def show() -> int:
    lines = CHANGELOG.read_text().splitlines()
    _, start, end = unreleased_section(lines)
    entries = [line for line in lines[start + 1:end] if line.strip()]
    print("\n".join([lines[start], *entries]))
    if entries:
        print("entries: yes")
        return 0
    print("entries: none")
    last = last_release()
    since = f"v{'.'.join(map(str, last))}" if last else None
    print(f"commits since {since or 'the first commit'}:")
    addon_changes = False
    for line in git("log", "--format=%h %s", *([f"{since}..HEAD"] if since else [])).splitlines():
        commit, subject = line.split(" ", 1)
        if subject.startswith("Bump version"):
            continue
        files = git("diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit).splitlines()
        addon = any(PACKAGED_FILES.fullmatch(file) for file in files)
        addon_changes |= addon
        print(f"{commit} {subject} [{'addon' if addon else 'dev'}]")
        for file in files:
            print(f"    {file}")
    print(f"addon changes: {'yes' if addon_changes else 'no'}")
    return 1


def write(entries: list[str]) -> int:
    if not entries:
        fail("Usage: changelog.py write <entry>...")
    if git("branch", "--show-current") != "main":
        fail('Current branch is not "main"')
    if git("status", "--porcelain"):
        fail("Uncommitted changes")
    git("fetch", "--quiet", "origin", "main")
    if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
        fail('Local "main" differs from "origin/main": run /push first')
    lines = CHANGELOG.read_text().splitlines()
    version, start, end = unreleased_section(lines)
    if any(line.strip() for line in lines[start + 1:end]):
        fail(f"CHANGELOG.md: v{version} already has entries")
    section = [lines[start], *(f"{number}. {entry}" for number, entry in enumerate(entries, 1))]
    lines[start:end] = section + ([""] if end < len(lines) else [])
    CHANGELOG.write_text("\n".join(lines) + "\n")
    git("commit", "--quiet", "-m", f"CHANGELOG: entries for v{version}", "--", str(CHANGELOG))
    try:
        git("push", "--quiet", "origin", "main")
    except subprocess.CalledProcessError as e:
        fail(f"Push failed (the CHANGELOG commit is local only): {e.stderr.strip()}")
    print(f"Committed {git('rev-parse', '--short', 'HEAD')} and pushed:")
    print("\n".join(section))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(write(sys.argv[2:]) if sys.argv[1:2] == ["write"] else show())
    except subprocess.CalledProcessError as error:
        fail(f"{' '.join(error.cmd)}: {error.stderr.strip()}")
