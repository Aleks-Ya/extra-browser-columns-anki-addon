#!/usr/bin/env bash
# Releases a version: dates the CHANGELOG section, bumps, commits and tags the release, builds the .ankiaddon,
# switches to the next patch dev version, pushes "main" with the tag and creates the GitHub Release.
# Run from the repo root after precheck.sh passed.
# Usage: release.sh <X.Y.Z>
# Exit codes: 0 - released, 2 - error (the failed step is printed; nothing is undone).
set -euo pipefail

skill_dir=$(dirname "$0")
version=${1:-}
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

check=$(python3 "$skill_dir/versions.py" "$version") || fail "Invalid version: $check"
if [[ -n $(git status --porcelain) ]]; then
    fail "Uncommitted changes"
fi
git fetch --quiet origin main
if [[ $(git rev-parse HEAD) != $(git rev-parse origin/main) ]]; then
    fail "Local \"main\" differs from \"origin/main\": run /push first"
fi

current=$(cat extra_browser_columns/version.txt)
IFS=. read -r major minor patch <<< "$version"
next="$major.$minor.$((patch + 1)).dev0"
tag="v$version"
repo=$(git config --get remote.origin.url | sed -E 's#^(git@github\.com:|https://github\.com/)##; s#\.git$##')
addon_file="dist/extra-browser-columns-$version.ankiaddon"

step "Release commit: $current → $version"
date=$(date +%Y-%m-%d)
sed -i -E "0,/^## v[0-9]+\.[0-9]+\.[0-9]+ - unreleased$/s##\#\# [$tag](https://github.com/$repo/releases/tag/$tag) - $date#" \
    CHANGELOG.md
grep -q "^## \[$tag\]" CHANGELOG.md || fail "CHANGELOG.md: the \"unreleased\" heading was not found"
bump-my-version bump --new-version "$version" --no-commit --no-tag --allow-dirty
changed=$(git status --porcelain | awk '{print $2}' | LC_ALL=C sort | tr '\n' ' ')
if [[ $changed != ".bumpversion.toml CHANGELOG.md extra_browser_columns/version.txt " ]]; then
    fail "Unexpected changed files: $changed"
fi
message="Bump version: $current → $version"
git commit --quiet -am "$message"
git tag -a "$tag" -m "$message"
release_commit=$(git rev-parse --short HEAD)
echo "Committed $release_commit and tagged $tag"
echo

step "Build"
python build_dist.py --skip_unit_tests
manifest_version=$(unzip -p "$addon_file" manifest.json | jq -r .human_version) || fail "Can't read $addon_file"
if [[ $manifest_version != "$tag" ]]; then
    fail "$addon_file has version \"$manifest_version\" instead of \"$tag\""
fi
echo

step "Development commit: $version → $next"
bump-my-version bump --new-version "$next" --no-commit --no-tag
sed -i "0,/^## \[$tag\]/s##\#\# v${next%.dev0} - unreleased\n\n&#" CHANGELOG.md
git commit --quiet -am "Bump version: $version → $next"
dev_commit=$(git rev-parse --short HEAD)
echo "Committed $dev_commit"
echo

step "Push"
git push --atomic origin main "$tag" || fail "Push was rejected: the release commit and tag are local only"
echo

step "GitHub Release"
notes=$(awk -v heading="## [$tag]" 'index($0, heading) == 1 {found=1; next} found && /^## /{exit} found' CHANGELOG.md)
release_url=$(gh release create "$tag" --verify-tag --title "$tag" --notes "$notes" "$addon_file") \
    || fail "GitHub Release was not created: the commits and the tag are pushed"
echo

echo "=== Release summary ==="
echo "Versions: $current → $version → $next"
echo "Release commit: $release_commit ($tag)"
echo "Development commit: $dev_commit"
echo "GitHub Release: $release_url"
echo "Addon file: $PWD/$addon_file"
echo "Release notes:"
echo "$notes"
echo "Manual step: upload the addon file to AnkiWeb (https://ankiweb.net/shared/upload)"
