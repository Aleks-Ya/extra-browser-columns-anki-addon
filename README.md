# Extra Browser Columns Anki addon

An addon for [Anki](https://apps.ankiweb.net) flashcard program
that adds 6 sortable columns to the Browser:

| Column    | Cards mode                 | Notes mode                                  |
|-----------|----------------------------|---------------------------------------------|
| Marked    | `✓` if the note has the `marked` tag | `✓` if the note has the `marked` tag |
| New       | `✓` if the card is new       | `✓` if any card of the note is new         |
| Learning  | `✓` if the card is in learning or relearning | `✓` if any card of the note is in learning or relearning |
| Review    | `✓` if the card is in review or relearning | `✓` if any card of the note is in review or relearning |
| Suspended | `✓` if the card is suspended | `✓` if any card of the note is suspended   |
| Buried    | `✓` if the card is buried (manually or by siblings) | `✓` if any card of the note is buried |

The New, Learning and Review columns match the "Card State" filters of the Browser sidebar
(`is:new`, `is:learn`, `is:review`), so a relearning card is both Learning and Review.

Enable a column: right-click the Browser table header and choose the column.
Click a column header to sort: flagged items are listed first (click again to reverse);
within each group items are ordered by the Sort Field.
Double-click the right border of a column header to shrink the column to its `✓`.
Hover a column header to see the column name and description (handy when the column is narrow).

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
