#!/usr/bin/env bash
# Waits for GitHub Actions and SonarCloud results of a pushed commit and prints them. Run from the repo root.
# Usage: check.sh [commit]   (default: HEAD)
# Exit codes: 0 - all green, 1 - issues to fix, 2 - tool error or timeout.
set -euo pipefail

sha=$(git rev-parse "${1:-HEAD}")
project=$(sed -n 's/^sonar.projectKey=//p' sonar-project.properties)
organization=$(sed -n 's/^sonar.organization=//p' sonar-project.properties)
round_file="$(git rev-parse --git-dir)/push-skill-round"
round=$(cat "$round_file" 2>/dev/null || echo 0)

fail() {
    echo "ERROR: $*" >&2
    exit 2
}

sonar() {
    local path=$1
    curl -sSf "https://sonarcloud.io/api/$path" || fail "SonarCloud API request failed: $path"
}

echo "=== GitHub Actions: $sha ==="
workflows=(.github/workflows/*.yml)
expected=${#workflows[@]}
count=0
for ((i = 0; i < 24; i++)); do
    count=$(gh run list --commit "$sha" --json databaseId --jq length)
    if [[ $count -ge $expected ]]; then
        break
    fi
    sleep 5
done
if [[ $count -lt $expected ]]; then
    fail "Only $count of $expected workflow runs started for $sha"
fi

github_ok=true
sonar_scanned=false
for id in $(gh run list --commit "$sha" --json databaseId --jq '.[].databaseId'); do
    gh run watch "$id" --exit-status > /dev/null 2>&1 || true
    run=$(gh run view "$id" --json workflowName,conclusion,url,jobs)
    jq -r '"\(.workflowName): \(.conclusion) \(.url)"' <<< "$run"
    if [[ $(jq -r '[.jobs[].steps[] | select(.name == "SonarCloud Scan" and .conclusion == "success")] | length' <<< "$run") -gt 0 ]]; then
        sonar_scanned=true
    fi
    if [[ $(jq -r .conclusion <<< "$run") != success ]]; then
        github_ok=false
        echo "--- Failed log (last 100 lines) ---"
        gh run view "$id" --log-failed | tail -100
        echo "---"
    fi
done
echo

echo "=== SonarCloud: $project ==="
gate=skipped
issue_count=0
hotspot_count=0
if [[ $sonar_scanned != true ]]; then
    echo "SonarCloud Scan step didn't succeed: fix GitHub Actions first"
else
    revision=
    for ((i = 0; i < 30; i++)); do
        revision=$(sonar "project_analyses/search?project=$project&ps=1" | jq -r '.analyses[0].revision // empty')
        if [[ $revision == "$sha" ]]; then
            break
        fi
        sleep 10
    done
    if [[ $revision != "$sha" ]]; then
        fail "SonarCloud analysis of $sha didn't appear in 5 minutes (latest: ${revision:-none})"
    fi

    gate=$(sonar "qualitygates/project_status?projectKey=$project" | jq -r .projectStatus.status)
    echo "Quality gate: $gate"

    issues=$(sonar "issues/search?componentKeys=$project&resolved=false&ps=500")
    issue_count=$(jq -r .total <<< "$issues")
    rule_names='{}'
    for rule in $(jq -r '[.issues[].rule] | unique | .[]' <<< "$issues"); do
        name=$(sonar "rules/show?key=$rule&organization=$organization" | jq -r .rule.name)
        rule_names=$(jq --arg rule "$rule" --arg name "$name" '. + {($rule): $name}' <<< "$rule_names")
    done
    echo "Open issues: $issue_count"
    jq -r --argjson names "$rule_names" '.issues[] |
        "\(.component | sub("^[^:]*:"; "")):\(.line // "-") \(.rule) (\($names[.rule])) \(.type) \(.severity): \(.message)"' \
        <<< "$issues"

    hotspots=$(sonar "hotspots/search?projectKey=$project&status=TO_REVIEW&ps=500")
    hotspot_count=$(jq -r .paging.total <<< "$hotspots")
    echo "Security hotspots to review: $hotspot_count"
    jq -r '.hotspots[] |
        "\(.component | sub("^[^:]*:"; "")):\(.line // "-") \(.ruleKey) \(.vulnerabilityProbability): \(.message)"' \
        <<< "$hotspots"
fi
echo

echo "=== Check summary ==="
echo "Commit: $sha"
echo "GitHub: $([[ $github_ok == true ]] && echo OK || echo FAILED)"
echo "Sonar quality gate: $gate"
echo "Sonar issues: $issue_count"
echo "Sonar hotspots: $hotspot_count"
echo "Fix round: $round/3"

if [[ $github_ok == true && $gate != ERROR && $issue_count -eq 0 && $hotspot_count -eq 0 ]]; then
    exit 0
fi
exit 1
