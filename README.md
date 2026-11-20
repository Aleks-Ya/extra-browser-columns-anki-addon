# Extra Browser Columns Anki addon

An addon for [Anki](https://apps.ankiweb.net) flashcard program
that adds 3 sortable columns to the Browser:

| Column    | Cards mode                 | Notes mode                                  |
|-----------|----------------------------|---------------------------------------------|
| Suspended | `✓` if the card is suspended | `✓` if any card of the note is suspended   |
| Buried    | `✓` if the card is buried (manually or by siblings) | `✓` if any card of the note is buried |
| Marked    | `✓` if the note has the `marked` tag | `✓` if the note has the `marked` tag |

Enable a column: right-click the Browser table header and choose the column.
Click a column header to sort: flagged items are listed first (click again to reverse);
within each group items are ordered by the Sort Field.

Supported Anki version: 26.09.4+

## Quality metrics

[![Unit-tests (Linux)](https://github.com/Aleks-Ya/extra-browser-columns-anki-addon/actions/workflows/unit-tests-linux.yml/badge.svg)](https://github.com/Aleks-Ya/extra-browser-columns-anki-addon/actions/workflows/unit-tests-linux.yml)
[![Unit-tests (Windows)](https://github.com/Aleks-Ya/extra-browser-columns-anki-addon/actions/workflows/unit-tests-windows.yml/badge.svg)](https://github.com/Aleks-Ya/extra-browser-columns-anki-addon/actions/workflows/unit-tests-windows.yml)
[![Unit-tests (MacOS)](https://github.com/Aleks-Ya/extra-browser-columns-anki-addon/actions/workflows/unit-tests-mac.yml/badge.svg)](https://github.com/Aleks-Ya/extra-browser-columns-anki-addon/actions/workflows/unit-tests-mac.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Aleks-Ya_extra-browser-columns-anki-addon&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Aleks-Ya_extra-browser-columns-anki-addon)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=Aleks-Ya_extra-browser-columns-anki-addon&metric=coverage)](https://sonarcloud.io/summary/new_code?id=Aleks-Ya_extra-browser-columns-anki-addon)

## Development

```bash
# Install dev tools
pip install -r requirements/dev.txt

# Run unit tests
tox

# Build the .ankiaddon file into "dist/" (runs tests first; add "--skip-tests" to skip them)
./build_dist.sh

# Deploy to a local Anki installation
./deploy_locally.sh ~/.local/share/Anki2/addons21/extra_browser_columns

# Release (bump, tag, build, push, GitHub Release; AnkiWeb upload is manual): "/release" skill
# Versions: X.Y.Z.dev0 while developing; releasing X.Y.Z switches to X.Y.(Z+1).dev0

# Scan with SonarQube locally (needs "sonar-scanner" with "sonar.token" in its "sonar-scanner.properties")
tox && sonar-scanner
```

SonarQube report: [SonarCloud](https://sonarcloud.io/project/overview?id=Aleks-Ya_extra-browser-columns-anki-addon)
