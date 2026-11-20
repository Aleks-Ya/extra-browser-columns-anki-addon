#!/usr/bin/env bash
# Builds the .ankiaddon into "dist/".
# "working-tree" builds the working tree (uncommitted changes included) after running the tests.
# A release tag ("vX.Y.Z" or "X.Y.Z") is built in a temporary git worktree without tests (/release required green CI
# for it), so the working tree is not touched.
# Run from the repo root.
# Usage: build.sh working-tree | vX.Y.Z | X.Y.Z
# Exit codes: 0 - built, 2 - error.
set -euo pipefail

target=${1:-}
if [[ -d .venv/bin ]]; then
    PATH="$PWD/.venv/bin:$PATH"
fi

fail() {
    echo "ERROR: $*" >&2
    exit 2
}

step() {
    echo "=== $* ==="
}

if [[ $target == working-tree ]]; then
    version=$(cat extra_browser_columns/version.txt)
    commit=$(git rev-parse --short HEAD)
    uncommitted=$(git status --short -- extra_browser_columns)
    step "Build working tree $version (with tests)"
    python build_dist.py || fail "Build failed"
else
    [[ -n $target ]] || fail "Usage: build.sh working-tree | vX.Y.Z | X.Y.Z"
    tag="v${target#v}"
    git rev-parse --quiet --verify "refs/tags/$tag" >/dev/null || fail "Tag not found: $tag"
    version=${tag#v}
    commit=$(git rev-parse --short "$tag^{commit}")
    worktree=$(mktemp -d)
    trap 'git worktree remove --force "$worktree" 2>/dev/null || rm -rf "$worktree"' EXIT
    step "Build $tag (without tests)"
    git worktree add --quiet --detach "$worktree" "$tag"
    (cd "$worktree" && python build_dist.py --skip_unit_tests) || fail "Build failed"
    rm -rf dist
    mkdir dist
    cp "$worktree"/dist/*.ankiaddon dist/
fi

addon_file="dist/extra-browser-columns-$version.ankiaddon"
[[ -f $addon_file ]] || fail "Addon file was not built: $addon_file"
manifest_version=$(unzip -p "$addon_file" manifest.json | jq -r .human_version) || fail "Can't read $addon_file"
if [[ $manifest_version != "v$version" ]]; then
    fail "$addon_file has version \"$manifest_version\" instead of \"v$version\""
fi

echo
echo "=== Build summary ==="
echo "Target: $target"
echo "Version: $version"
echo "Commit: $commit"
if [[ $target == working-tree ]]; then
    echo "Uncommitted changes: ${uncommitted:-none}"
fi
echo "Addon file: $PWD/$addon_file ($(du -h "$addon_file" | cut -f1))"
if [[ $version == *.dev* ]]; then
    echo "Dev version: not meant for AnkiWeb"
else
    echo "Upload to AnkiWeb: https://ankiweb.net/shared/upload"
fi
