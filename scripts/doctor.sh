#!/bin/sh
# Check skill links without changing them.
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd) || exit 1
exec python3 "$ROOT/scripts/hub.py" --repo "$ROOT" doctor "$@"
