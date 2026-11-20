---
name: build-distribution
description: "Build the .ankiaddon package (e.g. for the AnkiWeb upload): suggest the version, ask which one and build it. `/build-distribution` - ask, `/build-distribution <target>` - build `working-tree` or a release tag (`vX.Y.Z`)."
allowed-tools: Bash(.claude/skills/build-distribution/*)
---

# Build distribution

Run from the repo root.

## 1. Choose the target

If `$ARGUMENTS` names a target, skip to step 2. Otherwise:

```bash
.claude/skills/build-distribution/targets.sh
```

If it prints one target, build it without asking. Otherwise ask with AskUserQuestion: "Current version is
`<current>` (last release `<last release>`). Which version to build?". Options: the printed targets, labels
`vX.Y.Z` for the release and `Working tree X.Y.Z.devN` for the working tree; the `recommended` one first with
"(Recommended)". Descriptions: release - the package for AnkiWeb, built from the tag; working tree - dev build with
the uncommitted changes (say whether there are any), runs the tests. If the user types another version, pass it to
`build.sh`: it checks the tag.

## 2. Build

```bash
.claude/skills/build-distribution/build.sh <working-tree|vX.Y.Z>
```

On a non-zero exit show the output and stop: don't retry or fix things.

## Report

Relay the "Build summary": version, commit, addon file, and the AnkiWeb upload link or the dev-version warning.
