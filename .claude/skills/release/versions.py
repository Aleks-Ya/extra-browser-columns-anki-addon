#!/usr/bin/env python3
"""Print the current version and the versions /release offers, or check a version the user typed.

Candidates are the major, minor and patch versions after the last release tag (after 0.0.0 when there is no tag),
plus the in-progress version (the current version without ".devN") when it is higher than the last release.
The candidate equal to the in-progress version is marked "recommended".
With a version argument it checks that the version is a plain X.Y.Z higher than the last release:
it prints "ok" and exits 0, or prints why not and exits 1.
Run from the repository root: versions.py [<version>]
"""
import re
import subprocess
import sys
import tomllib

Version = tuple[int, int, int]


def parse(version: str) -> Version | None:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def current_version() -> str:
    with open(".bumpversion.toml", "rb") as f:
        return str(tomllib.load(f)["tool"]["bumpversion"]["current_version"])


def last_release() -> Version | None:
    tags = subprocess.run(["git", "tag", "--list", "v*"], check=True, capture_output=True, text=True).stdout.split()
    versions = [version for tag in tags if (version := parse(tag.removeprefix("v")))]
    return max(versions, default=None)


def candidates(current: str, last: Version | None) -> list[tuple[str, str, bool]]:
    major, minor, patch = last or (0, 0, 0)
    in_progress = current.split(".dev")[0]
    result = [(f"{major + 1}.0.0", "major"), (f"{major}.{minor + 1}.0", "minor"),
              (f"{major}.{minor}.{patch + 1}", "patch")]
    in_progress_version = parse(in_progress)
    if in_progress_version and in_progress_version > (last or (0, 0, 0)) \
            and in_progress not in [version for version, _ in result]:
        result.append((in_progress, "in progress"))
    return [(version, kind, version == in_progress) for version, kind in result]


def invalid(version: str, last: Version | None) -> str | None:
    """Why `version` can't be released after `last`, or None when it can."""
    parsed = parse(version)
    if not parsed:
        return f"{version!r} is not a plain X.Y.Z version"
    if parsed <= (last or (0, 0, 0)):
        return f"{version} is not higher than the last release {'.'.join(map(str, last or (0, 0, 0)))}"
    return None


if __name__ == "__main__":
    last_version = last_release()
    if len(sys.argv) > 1:
        problem = invalid(sys.argv[1], last_version)
        print(problem or "ok")
        sys.exit(1 if problem else 0)
    print(f"current: {current_version()}")
    print(f"last release: {'v' + '.'.join(map(str, last_version)) if last_version else 'none'}")
    for candidate, candidate_kind, recommended in candidates(current_version(), last_version):
        print(f"{candidate} {candidate_kind}{' recommended' if recommended else ''}")
