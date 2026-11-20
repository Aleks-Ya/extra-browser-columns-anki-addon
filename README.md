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

# Bump version
bump-my-version bump patch   # or minor / major
```
