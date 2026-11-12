#!/bin/sh
# Show harnesses, skill links, and conflicts. Changes nothing.
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd) || exit 1
exec python3 "$ROOT/scripts/hub.py" --repo "$ROOT" doctor "$@"
