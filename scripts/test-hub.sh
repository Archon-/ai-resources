#!/bin/sh
# Exercise install, sync, doctor, and uninstall against a fake home.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
HUB="$ROOT/scripts/hub.py"
TMP=$(mktemp -d)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

export AI_RESOURCES_HOME="$TMP/home"
export AI_RESOURCES_STATE_DIR="$TMP/state"
mkdir -p "$AI_RESOURCES_HOME"

fail() { echo "FAIL: $*" >&2; exit 1; }

# --- fixture repo ---
FIX="$TMP/repo"
mkdir -p "$FIX/skills/fixture/alpha" "$FIX/skills/oomol/beta" "$FIX/docs"
printf '%s\n' '---' 'name: alpha' 'description: alpha skill' '---' > "$FIX/skills/fixture/alpha/SKILL.md"
printf '%s\n' '---' 'name: beta' 'description: beta skill' '---' > "$FIX/skills/oomol/beta/SKILL.md"
printf '%s\n' '{"version":1,"skills":{"alpha":{"source":"fixture","managed":"upstream"},"beta":{"source":"oomol","managed":"upstream"}}}' > "$FIX/docs/skill-origins.json"

run() { python3 "$HUB" --repo "$FIX" "$@"; }

run install --skill alpha --dry-run >/dev/null
[ ! -e "$AI_RESOURCES_HOME/.claude/skills/alpha" ] || fail "dry-run created a link"
if [ -f "$FIX/enabled-skills.txt" ] && grep -q '^alpha$' "$FIX/enabled-skills.txt"; then
  fail "dry-run wrote the enabled list"
fi

run install --skill alpha >/dev/null
[ -L "$AI_RESOURCES_HOME/.claude/skills/alpha" ] || fail "claude alpha missing"
[ ! -e "$AI_RESOURCES_HOME/.agents/skills/beta" ] || fail "unselected beta was linked"
[ ! -e "$AI_RESOURCES_HOME/.cursor/skills/alpha" ] || fail "cursor linked by default"
grep -q '^alpha$' "$FIX/enabled-skills.txt" || fail "alpha not saved"

# one skill from a source that bulk install skips
run install --skill beta >/dev/null
[ -L "$AI_RESOURCES_HOME/.agents/skills/beta" ] || fail "explicit oomol skill was not linked"
grep -q '^beta$' "$FIX/enabled-skills.txt" || fail "beta not saved"

before=$(find "$AI_RESOURCES_HOME" -type l | wc -l | tr -d ' ')
run install >/dev/null
after=$(find "$AI_RESOURCES_HOME" -type l | wc -l | tr -d ' ')
[ "$before" = "$after" ] || fail "second install changed link count"

# unrelated skill and a real directory conflict
mkdir -p "$AI_RESOURCES_HOME/.claude/skills/mine"
ln -s /tmp "$AI_RESOURCES_HOME/.agents/skills/foreign"
rm "$AI_RESOURCES_HOME/.claude/skills/beta"
mkdir -p "$AI_RESOURCES_HOME/.claude/skills/beta"
if run install >/dev/null; then
  fail "install should fail on a real-directory conflict"
fi
[ -d "$AI_RESOURCES_HOME/.claude/skills/beta" ] && [ ! -L "$AI_RESOURCES_HOME/.claude/skills/beta" ] || fail "conflict dir was replaced"
[ -L "$AI_RESOURCES_HOME/.agents/skills/foreign" ] || fail "foreign symlink removed"

# removal via sync
rm -rf "$FIX/skills/fixture/alpha"
run sync --dry-run | grep -q "unlink  claude alpha" || fail "dry-run did not plan unlink"
[ -L "$AI_RESOURCES_HOME/.claude/skills/alpha" ] || fail "dry-run unlinked"
if run sync >/dev/null; then
  fail "sync should still report the beta conflict"
fi
[ ! -e "$AI_RESOURCES_HOME/.claude/skills/alpha" ] || fail "alpha link survived sync"
[ -d "$AI_RESOURCES_HOME/.claude/skills/mine" ] || fail "unrelated dir removed"

# broken link
mkdir -p "$FIX/skills/fixture/gone"
printf '%s\n' '---' 'name: gone' 'description: gone' '---' > "$FIX/skills/fixture/gone/SKILL.md"
run install --skill gone --clients claude >/dev/null || true
rm -rf "$FIX/skills/fixture/gone"
if run doctor >/dev/null; then
  fail "doctor should notice a broken link"
fi
run sync --clients claude >/dev/null || true
[ ! -e "$AI_RESOURCES_HOME/.claude/skills/gone" ] || fail "broken link survived sync"

run uninstall >/dev/null
find "$AI_RESOURCES_HOME" -type l > "$TMP/links"
while read -r link; do
  target=$(readlink "$link")
  case "$target" in
    "$FIX"/skills/*|"$ROOT"/skills/*) fail "uninstall left $link -> $target" ;;
  esac
done < "$TMP/links"
[ -d "$AI_RESOURCES_HOME/.claude/skills/mine" ] || fail "uninstall removed unrelated dir"
[ -L "$AI_RESOURCES_HOME/.agents/skills/foreign" ] || fail "uninstall removed foreign symlink"

# skip-source drops oomol even after it was explicitly linked, and keeps the other skill
mkdir -p "$FIX/skills/fixture/alpha"
printf '%s\n' '---' 'name: alpha' 'description: alpha skill' '---' > "$FIX/skills/fixture/alpha/SKILL.md"
run install --skip-source oomol >/dev/null || fail "skip-source install failed"
grep -q '^alpha$' "$FIX/enabled-skills.txt" || fail "skip-source dropped alpha"
grep -q '^beta$' "$FIX/enabled-skills.txt" && fail "skip-source kept oomol beta" || true
[ -L "$AI_RESOURCES_HOME/.agents/skills/beta" ] && fail "codex still links skipped source" || true
[ -L "$AI_RESOURCES_HOME/.claude/skills/alpha" ] || fail "skip-source removed alpha"

# assemble keeps a local skill
NEST="$TMP/nested/demo"
mkdir -p "$NEST/demo-skill"
printf '%s\n' '---' 'name: demo-skill' 'description: demo' '---' > "$NEST/demo-skill/SKILL.md"
mkdir -p "$NEST/knowledge"
echo "note" > "$NEST/knowledge/note.md"
mkdir -p "$FIX/skills/other/keepme"
printf '%s\n' '---' 'name: keepme' 'description: local' '---' > "$FIX/skills/other/keepme/SKILL.md"
python3 - << PY
import json
p="$FIX/docs/skill-origins.json"
d=json.load(open(p))
d["skills"]["keepme"]={"source":"local","managed":"local","version":None}
json.dump(d, open(p,"w"))
PY
python3 "$ROOT/scripts/assemble_skills.py" --nested "$TMP/nested" --repo "$FIX" >/dev/null
[ -f "$FIX/skills/other/demo-skill/SKILL.md" ] || fail "assemble missed upstream skill"
[ -f "$FIX/skills/other/keepme/SKILL.md" ] || fail "assemble dropped local skill"
[ ! -d "$FIX/skills/demo" ] || fail "one-skill source was not placed in other"
[ -f "$FIX/playbooks/demo/note.md" ] || fail "playbook not moved"

# real catalog: dry-run only, so enabled-skills.txt in this repo is not rewritten
before=$(cksum "$ROOT/enabled-skills.txt")
out=$(python3 "$HUB" --repo "$ROOT" install --dry-run --skip-source oomol --skip-source ecc)
after=$(cksum "$ROOT/enabled-skills.txt")
[ "$before" = "$after" ] || fail "dry-run changed enabled-skills.txt"
python3 - "$out" "$ROOT/docs/skill-origins.json" << 'PY'
import json, sys
out, path = sys.argv[1], sys.argv[2]
origins = json.load(open(path))["skills"]
wanted = {name for name, meta in origins.items() if meta.get("source") not in {"oomol", "ecc"}}
linked = set()
for line in out.splitlines():
    parts = line.split()
    if len(parts) >= 3 and parts[0] in ("link", "ok") and parts[1] == "claude":
        linked.add(parts[2])
missing = wanted - linked
extra = linked - wanted
if missing or extra:
    raise SystemExit("skip-source set mismatch missing={} extra={}".format(len(missing), len(extra)))
print("bulk skip links", len(linked))
PY
one=$(python3 "$HUB" --repo "$ROOT" install --dry-run --skill oo-github --clients claude)
echo "$one" | grep -qx "link claude oo-github" || fail "single oomol skill was not planned"
echo "$one" | grep -qx "link claude design-system" && fail "single skill also planned design-system" || true
[ "$(cksum "$ROOT/enabled-skills.txt")" = "$before" ] || fail "skill dry-run changed enabled-skills.txt"

echo "ok"
