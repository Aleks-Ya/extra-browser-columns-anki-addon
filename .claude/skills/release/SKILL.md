---
name: release
description: "Release a version: suggest versions, ask which one, bump, tag, build the .ankiaddon, push and create the GitHub Release."
allowed-tools: Bash(.claude/skills/release/*)
disable-model-invocation: true
---

# Release

Run from the repo root. Invoking `/release` is the permission to commit, tag and push the release.

## 1. Preconditions

```bash
.claude/skills/release/precheck.sh
```

It takes minutes: it waits for GitHub Actions and SonarCloud of `HEAD`.

- `0`: continue.
- `1` (CI or SonarCloud issues): show the "Check summary" and stop; suggest `/push` to fix them. Don't fix here.
- `2` (precondition/tool error): show the error and stop. If the CHANGELOG has no "unreleased" entries, ask the
  user to add them; don't write them yourself.

## 2. Choose the version

```bash
.claude/skills/release/versions.py
```

Ask with AskUserQuestion: "Current version is `<current>` (last release `<last release>`). Which version to
release?". Options: the printed candidates, the exact versions as labels; the `recommended` one first with
"(Recommended)". Descriptions: major - breaking changes, minor - new features, patch - fixes only,
in progress - the version being developed. If the user types another version, check it with
`.claude/skills/release/versions.py <version>` and ask again unless it prints `ok`.

## 3. Release

```bash
.claude/skills/release/release.sh <version>
```

On a non-zero exit show the output and stop: don't retry, reset commits, delete tags or force-push.

## Report

Relay the "Release summary" (versions, commits, tag, GitHub Release URL, addon file, release notes) and remind the
user of the manual AnkiWeb upload.
