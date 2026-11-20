#!/usr/bin/env bash
# Checks that "main" can be released, then waits for its GitHub Actions and SonarCloud results (via push/check.sh).
# Run from the repo root.
# Exit codes: 0 - ready to release, 1 - CI or SonarCloud issues, 2 - precondition/tool error or timeout.
set -euo pipefail

fail() {
    echo "ERROR: $*" >&2
    exit 2
}

changes=$(git status --porcelain)
if [[ -n $changes ]]; then
    fail "Uncommitted changes:"$'\n'"$changes"
fi

branch=$(git branch --show-current)
if [[ $branch != main ]]; then
    fail "Current branch is \"$branch\", not \"main\""
fi

git fetch --quiet origin main
if [[ $(git rev-parse HEAD) != $(git rev-parse origin/main) ]]; then
    fail "Local \"main\" differs from \"origin/main\": run /push first"$'\n'"$(git log --oneline --left-right HEAD...origin/main)"
fi

gh auth status > /dev/null 2>&1 || fail "gh is not logged in: run \"gh auth login\""

# The top section must be "## vX.Y.Z - unreleased" with at least one entry
section=$(awk '/^## /{n++} n==1' CHANGELOG.md)
if ! head -1 <<< "$section" | grep -Eq '^## v[0-9]+\.[0-9]+\.[0-9]+ - unreleased$'; then
    fail "CHANGELOG.md: the top section must be \"## vX.Y.Z - unreleased\", found: $(head -1 <<< "$section")"
fi
if [[ -z $(tail -n +2 <<< "$section" | grep -v '^[[:space:]]*$' || true) ]]; then
    fail "CHANGELOG.md: the \"unreleased\" section has no entries"
fi

echo "Preconditions: OK (HEAD $(git rev-parse --short HEAD) is pushed, CHANGELOG has unreleased entries)"
echo

exec "$(dirname "$0")/../push/check.sh" HEAD
