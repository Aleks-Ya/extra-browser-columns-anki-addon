#!/usr/bin/env bash
# Deploys the addon from the working tree to the local Anki and gently restarts a running Anki. Run from the repo root.
# Usage: deploy.sh [addon_dir] [--restart[=true|false]]
# The restart sends SIGTERM: Anki closes as from its window (unsaved-input prompts, sync on close, backup).
set -e

quit_timeout=60
start_timeout=5

dest=""
restart=true
for arg in "$@"; do
    case "$arg" in
        --restart | --restart=true) restart=true ;;
        --restart=false) restart=false ;;
        --restart=*)
            echo "ERROR: Invalid value (expected true or false): $arg" >&2
            exit 1
            ;;
        -*)
            echo "ERROR: Unknown option: $arg" >&2
            exit 1
            ;;
        *)
            if [[ -n "$dest" ]]; then
                echo "ERROR: More than one addon folder given: $dest, $arg" >&2
                exit 1
            fi
            dest=$arg
            ;;
    esac
done
dest=${dest:-$HOME/.local/share/Anki2/addons21/extra_browser_columns}
addons_dir=$(dirname "$dest")

if [[ ! -d "$addons_dir" ]]; then
    echo "ERROR: Anki addons folder absents: $addons_dir" >&2
    exit 1
fi

anki_pids() {
    pgrep -x anki || true
}

stopped_anki=false
if [[ "$restart" == true ]]; then
    pids=$(anki_pids)
    if [[ -n "$pids" ]]; then
        echo "Asking Anki to quit (SIGTERM): $(echo "$pids" | tr '\n' ' ')"
        # shellcheck disable=SC2086 # word splitting of the PID list is intended
        kill -TERM $pids
        for ((i = 0; i < quit_timeout; i++)); do
            [[ -z "$(anki_pids)" ]] && break
            sleep 1
        done
        if [[ -n "$(anki_pids)" ]]; then
            echo "ERROR: Anki didn't quit within ${quit_timeout} s (a dialog may be waiting, e.g. 'discard unsaved input?'):" \
                "close it and rerun, or use --restart=false. Nothing was deployed." >&2
            exit 1
        fi
        stopped_anki=true
    fi
fi

mkdir -p "$dest"
./deploy_locally.sh "$dest"

for file in __init__.py column_hooks.py column_values.py version.txt; do
    if [[ ! -f "$dest/$file" ]]; then
        echo "ERROR: File was not deployed: $dest/$file" >&2
        exit 1
    fi
done
if [[ -n "$(find "$dest" -name __pycache__)" ]]; then
    echo "ERROR: __pycache__ was deployed: $dest" >&2
    exit 1
fi

if [[ "$stopped_anki" == true ]]; then
    setsid -f anki >/dev/null 2>&1 </dev/null
    for ((i = 0; i < start_timeout; i++)); do
        [[ -n "$(anki_pids)" ]] && break
        sleep 1
    done
    if [[ -z "$(anki_pids)" ]]; then
        echo "ERROR: Anki was deployed but didn't start again within ${start_timeout} s: start it manually" >&2
        exit 1
    fi
    anki_status="Anki restarted"
elif [[ -n "$(anki_pids)" ]]; then
    anki_status="Anki is running: restart it to load the new code"
elif [[ "$restart" == true ]]; then
    anki_status="Anki is not running (not started)"
else
    anki_status="Anki is not running"
fi

uncommitted=$(git status --short -- extra_browser_columns)

echo
echo "=== Deploy summary ==="
echo "Destination: $dest"
echo "Version: $(cat extra_browser_columns/version.txt)"
echo "Uncommitted changes: ${uncommitted:-none}"
echo "$anki_status"
