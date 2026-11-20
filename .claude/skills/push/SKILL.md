---
name: push
description: "Push `main`, check GitHub Actions and SonarCloud results, and fix the issues found (commit, push, re-check)."
allowed-tools: Bash(.claude/skills/push/*)
disable-model-invocation: true
---

# Push

Run from the repo root:

```bash
.claude/skills/push/push.sh
```

Act on the exit code of `push.sh` or `commit-fix.sh` (both take minutes: they wait for CI):

- `0`: all green. Relay the "Check summary" and stop.
- `2` (precondition/tool error, timeout) or `3` (fix-round limit reached): show the error and stop. Don't stash,
  switch branches, pull, or retry.
- `1`: fix the issues (below), then run the next line and act on its exit code the same way:

  ```bash
  .claude/skills/push/commit-fix.sh "<commit message describing the fixes>"
  ```

  It runs `tox`, commits all changes, pushes and re-checks (invoking `/push` is the permission to commit and push).

## Fixing

- GitHub failure: find the root cause in the printed failed log and fix the code, tests or workflow.
- Sonar issue or hotspot: fix it if it makes sense; never silence it with `# NOSONAR`. If it isn't worth fixing
  (e.g. locking the `tox` version installed in CI), leave the code as is and list it in the final report with a
  reason, for the user to mark "Won't Fix" in SonarCloud. If only such issues remain, stop: don't run
  `commit-fix.sh` without changes.

## Final report

Pushed commits, GitHub results, Sonar quality gate and issue counts, fixes made, and issues left for the user.
