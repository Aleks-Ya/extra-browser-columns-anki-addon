#!/usr/bin/env bash
# Deploys the addon from the working tree to the local Anki. Run from the repo root.
# Usage: deploy.sh [addon_dir]
set -e

dest=${1:-$HOME/.local/share/Anki2/addons21/extra_browser_columns}
addons_dir=$(dirname "$dest")

if [ ! -d "$addons_dir" ]; then
    echo "ERROR: Anki addons folder absents: $addons_dir"
    exit 1
fi

mkdir -p "$dest"
./deploy_locally.sh "$dest"

for file in __init__.py column_hooks.py column_values.py version.txt; do
    if [ ! -f "$dest/$file" ]; then
        echo "ERROR: File was not deployed: $dest/$file"
        exit 1
    fi
done
if [ -n "$(find "$dest" -name __pycache__)" ]; then
    echo "ERROR: __pycache__ was deployed: $dest"
    exit 1
fi

uncommitted=$(git status --short -- extra_browser_columns)
if pgrep -f /usr/local/share/anki >/dev/null || pgrep -x anki >/dev/null; then
    anki_status="Anki is running: restart it to load the new code"
else
    anki_status="Anki is not running"
fi

echo
echo "=== Deploy summary ==="
echo "Destination: $dest"
echo "Version: $(cat extra_browser_columns/version.txt)"
echo "Uncommitted changes: ${uncommitted:-none}"
echo "$anki_status"
