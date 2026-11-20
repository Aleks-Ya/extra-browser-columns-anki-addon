#!/usr/bin/env bash
# Runs the tests, commits all changes as a fix round and pushes them again (via push.sh). Run from the repo root.
# Usage: commit-fix.sh "<commit message>"
# Exit codes: 0 - all green, 1 - issues to fix, 2 - precondition/tool error or timeout, 3 - fix-round limit reached.
set -euo pipefail

skill_dir=$(dirname "$0")
round_file="$(git rev-parse --git-dir)/push-skill-round"
round=$(cat "$round_file" 2>/dev/null || echo 0)
max_rounds=3

fail() {
    echo "ERROR: $*" >&2
    exit 2
}

message=${1:-}
if [[ -z $message ]]; then
    fail "Commit message is required"
fi
if [[ -z $(git status --porcelain) ]]; then
    fail "No changes to commit"
fi
if [[ $round -ge $max_rounds ]]; then
    echo "ERROR: Fix-round limit ($max_rounds) reached: changes are left uncommitted" >&2
    exit 3
fi

echo "=== Tests ==="
if ! tox_output=$(tox 2>&1); then
    echo "$tox_output" | tail -50
    fail "Tests failed: nothing committed"
fi
echo "$tox_output" | tail -3
echo

git add -A
git commit --quiet -m "$message"
echo $((round + 1)) > "$round_file"
echo "Committed fix round $((round + 1)): $(git log --oneline -1)"
echo

exec "$skill_dir/push.sh" --continue
