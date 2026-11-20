---
name: deploy-locally
description: "Deploy the addon from the working tree to the local Anki: `/deploy-locally` - default addons folder, `/deploy-locally <dir>` - a given addon folder."
allowed-tools: Bash(.claude/skills/deploy-locally/deploy.sh *)
disable-model-invocation: true
---

# Deploy locally

Deploy the addon from the working tree (uncommitted changes included) to the local Anki.
The default destination is `~/.local/share/Anki2/addons21/extra_browser_columns`; an optional argument overrides it.

Run from the repo root:

```bash
.claude/skills/deploy-locally/deploy.sh $ARGUMENTS
```

If the script exits with an error, stop and show its output — don't retry or fix things.
Otherwise relay the "Deploy summary": destination, version, uncommitted changes, and the reminder to restart Anki
if it's running (never kill or start Anki yourself).

Note: the destination folder is wiped before copying, including Anki's `meta.json` (enabled/disabled state).
That's fine: the addon has no config.
