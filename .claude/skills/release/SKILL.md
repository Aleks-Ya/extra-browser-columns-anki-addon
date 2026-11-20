---
name: release
description: "Release a version: draft the CHANGELOG entries if missing, suggest versions, ask which one, bump, tag, build the .ankiaddon, push and create the GitHub Release."
allowed-tools: Bash(.claude/skills/release/*)
disable-model-invocation: true
---

# Release

Run from the repo root. Invoking `/release` is the permission to commit, tag and push the release.

## 1. CHANGELOG

```bash
.claude/skills/release/changelog.py
```

- `0`: the "unreleased" section has entries: continue.
- `2`: show the error and stop.
- `1`: no entries. It printed the commits since the last release, each marked `addon` (changes the package) or
  `dev`.
  - `addon changes: yes`: draft the entries from the `addon` commits only (read their diffs if the subjects are
    unclear): one entry per change visible to addon users, worded for them, not as commit subjects, in the style
    of the existing entries: `__[FEATURE]__` new behavior, `__[FIX]__` bug fix. Ask with AskUserQuestion:
    "The CHANGELOG section `vX.Y.Z` has no entries. Use these?". Options: "Use the draft (Recommended)" with the
    entries in `preview`, and "Stop"; the user can type their own entries via "Other".
  - `addon changes: no`: ask with AskUserQuestion: "No addon changes since `<last release>`: the package would be
    the same. Release anyway?". Options: "Stop (Recommended)" and "Release with `__[CHANGE]__ No functional
    changes`"; the user can type their own entry via "Other".

  On "Stop", stop. Otherwise write the entries (the text after the number, one argument each); it commits
  CHANGELOG.md and pushes `main`:

  ```bash
  .claude/skills/release/changelog.py write "<entry>" ...
  ```

  On a non-zero exit show the output and stop.

## 2. Preconditions

```bash
.claude/skills/release/precheck.sh
```

It takes minutes: it waits for GitHub Actions and SonarCloud of `HEAD`.

- `0`: continue.
- `1` (CI or SonarCloud issues): show the "Check summary" and stop; suggest `/push` to fix them. Don't fix here.
- `2` (precondition/tool error): show the error and stop.

## 3. Choose the version

```bash
.claude/skills/release/versions.py
```

Ask with AskUserQuestion: "Current version is `<current>` (last release `<last release>`). Which version to
release?". Options: the printed candidates, the exact versions as labels; the `recommended` one first with
"(Recommended)". Descriptions: major - breaking changes, minor - new features, patch - fixes only,
in progress - the version being developed. If the user types another version, check it with
`.claude/skills/release/versions.py <version>` and ask again unless it prints `ok`.

## 4. Release

```bash
.claude/skills/release/release.sh <version>
```

On a non-zero exit show the output and stop: don't retry, reset commits, delete tags or force-push.

## Report

Relay the "Release summary" (versions, commits, tag, GitHub Release URL, addon file, release notes) and remind the
user of the manual AnkiWeb upload.
