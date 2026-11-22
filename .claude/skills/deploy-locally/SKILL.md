---
name: deploy-locally
description: "Deploy the addon from the working tree to the local Anki and restart a running Anki: `/deploy-locally` - default addons folder, `/deploy-locally <dir>` - a given addon folder, `--restart=false` - don't restart Anki."
allowed-tools: Bash(.claude/skills/deploy-locally/deploy.sh *)
disable-model-invocation: true
---

# Deploy locally

Deploy the addon from the working tree (uncommitted changes included) to the local Anki.
The default destination is `~/.local/share/Anki2/addons21/extra_browser_columns`; an optional folder argument
overrides it.

By default a running Anki is restarted gently: the script sends it SIGTERM (Anki closes as from its window: prompts
about unsaved input, sync on close, backup), waits up to 60 s for it to quit, deploys, then starts Anki again.
A not running Anki is not started. `--restart=false` deploys without touching Anki.

Run from the repo root, with a Bash `timeout` of at least 120000 ms (the script may wait for Anki to quit):

```bash
.claude/skills/deploy-locally/deploy.sh $ARGUMENTS
```

If the script exits with an error, stop and show its output — don't retry or fix things.
Otherwise relay the "Deploy summary": destination, version, uncommitted changes and the Anki status.
The script handles the Anki restart: never kill or start Anki outside it, and never use `kill -9`.

Note: the destination folder is wiped before copying, including Anki's `meta.json` (enabled/disabled state).
That's fine: the addon has no config.
