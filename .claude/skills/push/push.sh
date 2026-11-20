#!/usr/bin/env bash
# Pushes "main" and checks GitHub Actions and SonarCloud results (via check.sh). Run from the repo root.
# Usage: push.sh [--continue]   ("--continue" keeps the fix-round counter, used by commit-fix.sh)
# Exit codes: 0 - all green, 1 - issues to fix, 2 - precondition/tool error or timeout.
set -euo pipefail

skill_dir=$(dirname "$0")
round_file="$(git rev-parse --git-dir)/push-skill-round"

fail() {
    echo "ERROR: $*" >&2
    exit 2
}

if [[ ${1:-} != --continue ]]; then
    echo 0 > "$round_file"
fi

changes=$(git status --porcelain)
if [[ -n $changes ]]; then
    fail "Uncommitted changes:"$'\n'"$changes"
fi

branch=$(git branch --show-current)
if [[ $branch != main ]]; then
    fail "Current branch is \"$branch\", not \"main\""
fi

git fetch --quiet origin main
behind=$(git rev-list --count HEAD..origin/main)
if [[ $behind -gt 0 ]]; then
    fail "Local \"main\" is $behind commit(s) behind \"origin/main\": pull or rebase first"
fi

echo "=== Push ==="
commits=$(git log --oneline origin/main..HEAD)
if [[ -z $commits ]]; then
    echo "Nothing to push: checking the results of HEAD"
else
    echo "Pushing commits:"
    echo "$commits"
    git push --quiet origin main
fi
echo "HEAD: $(git rev-parse HEAD)"
echo

exec "$skill_dir/check.sh" HEAD
