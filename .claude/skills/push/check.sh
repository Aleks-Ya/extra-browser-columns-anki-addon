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

    # Only issues and hotspots on lines changed since the previous analyzed commit are counted: issue creation dates
    # can't be used, SonarCloud backdates them to the git blame date of the line
    base=$(sonar "project_analyses/search?project=$project&ps=100" |
        jq -r --arg sha "$sha" '[.analyses[].revision // empty | select(. != $sha)][0] // empty')
    if [[ -n $base ]] && git cat-file -e "$base^{commit}" 2> /dev/null; then
        echo "Counted: issues on lines changed since the previous analyzed commit $(git rev-parse --short "$base")"
        changed=$(git diff -U0 --no-color "$base" "$sha" | awk '
            /^diff --git / { header = 1; next }
            header && /^\+\+\+ / { file = ($2 == "/dev/null") ? "" : substr($0, 7); next }
            /^@@ / {
                header = 0
                n = split(substr($3, 2), range, ",")
                count = (n > 1) ? range[2] : 1
                if (file != "" && count > 0) print file "\t" range[1] "\t" range[1] + count - 1
            }' |
            jq -Rn '[inputs | split("\t") | {file: .[0], range: [(.[1], .[2]) | tonumber]}] |
                group_by(.file) | map({(.[0].file): map(.range)}) | add // {}')
    else
        echo "Counted: all issues (no previous analyzed commit in the local repo)"
        changed=null
    fi
    in_push='def in_push: if $changed == null then true else
        (.line // null) as $line | $changed[.component | sub("^[^:]*:"; "")] as $ranges |
        $ranges != null and ($line == null or any($ranges[]; .[0] <= $line and $line <= .[1])) end;'

    all_issues=$(sonar "issues/search?componentKeys=$project&resolved=false&ps=500")
    issues=$(jq --argjson changed "$changed" "$in_push"' .issues |= map(select(in_push))' <<< "$all_issues")
    issue_count=$(jq -r '.issues | length' <<< "$issues")
    rule_names='{}'
    for rule in $(jq -r '[.issues[].rule] | unique | .[]' <<< "$issues"); do
        name=$(sonar "rules/show?key=$rule&organization=$organization" | jq -r .rule.name)
        rule_names=$(jq --arg rule "$rule" --arg name "$name" '. + {($rule): $name}' <<< "$rule_names")
    done
    echo "Open issues: $issue_count (not counted: $(($(jq -r .total <<< "$all_issues") - issue_count)))"
    jq -r --argjson names "$rule_names" '.issues[] |
        "\(.component | sub("^[^:]*:"; "")):\(.line // "-") \(.rule) (\($names[.rule])) \(.type) \(.severity): \(.message)"' \
        <<< "$issues"

    all_hotspots=$(sonar "hotspots/search?projectKey=$project&status=TO_REVIEW&ps=500")
    hotspots=$(jq --argjson changed "$changed" "$in_push"' .hotspots |= map(select(in_push))' <<< "$all_hotspots")
    hotspot_count=$(jq -r '.hotspots | length' <<< "$hotspots")
    echo "Security hotspots to review: $hotspot_count (not counted: $(($(jq -r .paging.total <<< "$all_hotspots") - hotspot_count)))"
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
