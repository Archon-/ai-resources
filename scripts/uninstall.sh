#!/bin/sh
# Remove only symlinks that point into this repo.
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd) || exit 1
exec python3 "$ROOT/scripts/hub.py" --repo "$ROOT" uninstall "$@"
