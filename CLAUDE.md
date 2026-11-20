# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Extra Browser Columns is an Anki addon that adds sortable "Suspended", "Buried" and "Marked" columns to the Browser.
Target Anki version: 26.09.4.

## Git

- Do not create feature branches unless explicitly asked: commit directly to the current branch (`main`).
- Commit or push only when asked.
- The `/push` skill pushes `main`, checks GitHub Actions and SonarCloud results and fixes the issues found;
  invoking it is an explicit request to commit and push those fixes.
- The `/release` skill releases a version (needs `main` pushed with green CI and an "unreleased" CHANGELOG
  section with entries); invoking it is an explicit request to commit, tag and push the release.

## Commands

```bash
# Run unit tests (tox env "anki-current" pins Anki 26.9.4)
tox

# Run a single test file or test (within an active venv with the tox deps installed)
pytest tests/column_hooks_test.py
pytest tests/column_hooks_test.py::test_add_columns

# Build the .ankiaddon file into "dist/" (runs tests first; "--skip-tests" skips them)
./build_dist.sh

# Build interactively: suggests the version (last release tag or working tree): "/build-distribution" skill

# Deploy to the local Anki (also available as the "/deploy-locally" skill)
./deploy_locally.sh ~/.local/share/Anki2/addons21/extra_browser_columns

# Release (bump, tag, build, push, GitHub Release; AnkiWeb upload is manual): "/release" skill
# Versions: X.Y.Z.dev0 while developing; releasing X.Y.Z switches to X.Y.(Z+1).dev0
```

## Architecture

- `extra_browser_columns/__init__.py` — addon entry point: registers `ColumnHooks` on `profile_did_open` and removes
  them on `profile_will_close`.
- `extra_browser_columns/column_hooks.py` — `ColumnHooks`: adds the columns (`browser_did_fetch_columns`), fills cells
  with `✓` (`browser_did_fetch_row`) and implements sorting: `browser_will_search` replaces our column with the
  "Sort Field" column and stores our column key in `context.addon_metadata`; `browser_did_search` re-sorts
  `context.ids` so flagged items go first (descending).
- `extra_browser_columns/column_values.py` — `ColumnValues`: per-row flag checks via SQL on `cards`/`notes`, and sets
  of flagged ids for sorting via Anki searches (`is:suspended`, `is:buried`, `tag:marked`). In notes mode a note is
  suspended/buried if any of its cards is.
- `build_dist.py` — packages the addon and generates `manifest.json` (version from `extra_browser_columns/version.txt`).

## CI

GitHub Actions (`.github/workflows/`) run `tox` on Linux, macOS and Windows on push/PR to `main`; the Linux job also
runs the SonarCloud scan (`sonar-project.properties`, `coverage.xml` from tox, `SONAR_TOKEN` secret).
Dependabot is disabled on purpose: dependency versions are dictated by Anki.

## Tests

`tests/` uses pytest with a real temporary Anki `Collection` (`tests/conftest.py`); the Browser is a `MagicMock`.
Notes mode is detected via `browser._switch.isChecked()` because `Table.is_notes_mode()` lags while toggling.
