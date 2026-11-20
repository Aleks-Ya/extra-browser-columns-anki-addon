#!/usr/bin/env bash
# Prints the current version, the last release and the targets /build-distribution offers, one per line:
# "<target> <kind> [recommended]" for the last release tag and "working-tree <version> uncommitted-changes:yes|no".
# The last release is recommended (it's the package for AnkiWeb); without release tags the working tree is.
# The working tree is omitted when it's clean and HEAD is the last release tag (it would build the same package).
# Run from the repo root: targets.sh
set -euo pipefail

current=$(cat extra_browser_columns/version.txt)
last=$(git tag --list 'v*' --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -n 1 || true)
if [[ -n $(git status --porcelain -- extra_browser_columns) ]]; then
    uncommitted=yes
else
    uncommitted=no
fi

echo "current: $current"
echo "last release: ${last:-none}"
if [[ -n $last ]]; then
    echo "$last release recommended"
    if [[ $uncommitted == no && $(git rev-parse HEAD) == $(git rev-parse "$last^{commit}") ]]; then
        exit 0
    fi
    echo "working-tree $current uncommitted-changes:$uncommitted"
else
    echo "working-tree $current uncommitted-changes:$uncommitted recommended"
fi
