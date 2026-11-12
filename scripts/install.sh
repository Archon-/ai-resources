#!/bin/sh
# Link skills into Claude Code and Codex. Safe to re-run.
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd) || exit 1
exec python3 "$ROOT/scripts/hub.py" --repo "$ROOT" install "$@"
