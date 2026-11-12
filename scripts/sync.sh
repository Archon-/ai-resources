#!/bin/sh
# Reconcile client skill links with this repo. Supports --dry-run.
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd) || exit 1
exec python3 "$ROOT/scripts/hub.py" --repo "$ROOT" sync "$@"
