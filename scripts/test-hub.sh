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
mkdir -p "$AI_RESOURCES_HOME" "$TMP/bin"
# Only binaries linked here are visible. A harness binary in /usr/bin must not count.
# python3 may be a pyenv shim. Point at the real interpreter so the shim's bash is not required.
ln -s "$(python3 -c 'import sys; print(sys.executable)')" "$TMP/bin/python3"
for cmd in find grep wc tr ln rm mkdir cp readlink cksum awk env rmdir; do
  ln -s "$(command -v "$cmd")" "$TMP/bin/$cmd"
done
export PATH="$TMP/bin"
mkdir -p "$AI_RESOURCES_HOME/.claude" "$AI_RESOURCES_HOME/.codex"
printf '%s\n' '{}' > "$AI_RESOURCES_HOME/.claude/settings.json"
printf '%s\n' '' > "$AI_RESOURCES_HOME/.codex/config.toml"

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
[ ! -e "$AI_RESOURCES_HOME/.cursor/skills/alpha" ] || fail "cursor linked without Cursor installed"
grep -q '^alpha$' "$FIX/enabled-skills.txt" || fail "alpha not saved"

# one skill from a source that bulk install skips
run install --skill beta >/dev/null
[ -L "$AI_RESOURCES_HOME/.agents/skills/beta" ] || fail "explicit oomol skill was not linked"
grep -q '^beta$' "$FIX/enabled-skills.txt" || fail "beta not saved"

before=$(find "$AI_RESOURCES_HOME" -type l | wc -l | tr -d ' ')
run install >/dev/null
after=$(find "$AI_RESOURCES_HOME" -type l | wc -l | tr -d ' ')
[ "$before" = "$after" ] || fail "second install changed link count"

# owned symlink pointed at another skill in this repo is relinked
ln -sfn "$FIX/skills/oomol/beta" "$AI_RESOURCES_HOME/.claude/skills/alpha"
out=$(run install --clients claude)
echo "$out" | grep -E -q "relink[[:space:]]+claude-code[[:space:]]+alpha" || fail "owned mismatch was not relinked"
alpha_real=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$FIX/skills/fixture/alpha")
[ "$(readlink "$AI_RESOURCES_HOME/.claude/skills/alpha")" = "$alpha_real" ] || fail "relink target"

# empty enabled list returns before any removal
cp "$FIX/enabled-skills.txt" "$TMP/enabled.bak"
printf '%s\n' '# none' > "$FIX/enabled-skills.txt"
out=$(run sync)
echo "$out" | grep -q "Nothing to sync" || fail "empty sync planned removals"
[ -L "$AI_RESOURCES_HOME/.claude/skills/alpha" ] || fail "empty sync removed alpha"
cp "$TMP/enabled.bak" "$FIX/enabled-skills.txt"

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
skills_real=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$FIX/skills")
mkdir -p "$TMP/outside"
ln -s "$skills_real/../../outside" "$AI_RESOURCES_HOME/.claude/skills/escape"
ln -s "$skills_real/fixture/../fixture/alpha" "$AI_RESOURCES_HOME/.claude/skills/nested"
ln -s loop "$AI_RESOURCES_HOME/.claude/skills/loop"
rm -rf "$FIX/skills/fixture/alpha"
run sync --dry-run | grep -E -q "unlink[[:space:]]+claude-code[[:space:]]+alpha" || fail "dry-run did not plan unlink"
[ -L "$AI_RESOURCES_HOME/.claude/skills/alpha" ] || fail "dry-run unlinked"
[ -L "$AI_RESOURCES_HOME/.claude/skills/escape" ] || fail "dry-run unlinked escaped symlink"
if run sync >/dev/null; then
  fail "sync should still report the beta conflict"
fi
[ ! -e "$AI_RESOURCES_HOME/.claude/skills/alpha" ] || fail "alpha link survived sync"
[ ! -e "$AI_RESOURCES_HOME/.claude/skills/nested" ] || fail "in-skills link survived sync"
[ -L "$AI_RESOURCES_HOME/.claude/skills/escape" ] || fail "sync removed escaped symlink"
[ -L "$AI_RESOURCES_HOME/.claude/skills/loop" ] || fail "sync removed symlink loop"
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
[ ! -e "$AI_RESOURCES_STATE_DIR/manifest.json" ] || fail "full uninstall recreated the manifest"
find "$AI_RESOURCES_HOME" -type l > "$TMP/links"
fix_skills=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$FIX/skills")
root_skills=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$ROOT/skills")
while read -r link; do
  [ -n "$link" ] || continue
  resolved=$(python3 -c 'import os, sys
try:
    print(os.path.realpath(sys.argv[1]))
except OSError:
    print("")
' "$link")
  [ -n "$resolved" ] || continue
  case "$resolved" in
    "$fix_skills"|"$fix_skills"/*|"$root_skills"|"$root_skills"/*)
      fail "uninstall left $link -> $resolved" ;;
  esac
done < "$TMP/links"
[ -d "$AI_RESOURCES_HOME/.claude/skills/mine" ] || fail "uninstall removed unrelated dir"
[ -L "$AI_RESOURCES_HOME/.agents/skills/foreign" ] || fail "uninstall removed foreign symlink"
[ -L "$AI_RESOURCES_HOME/.claude/skills/escape" ] || fail "uninstall removed escaped symlink"
[ -L "$AI_RESOURCES_HOME/.claude/skills/loop" ] || fail "uninstall removed symlink loop"

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
    if len(parts) >= 3 and parts[0] in ("link", "ok") and parts[1] == "claude-code":
        linked.add(parts[2])
missing = wanted - linked
extra = linked - wanted
if missing or extra:
    raise SystemExit("skip-source set mismatch missing={} extra={}".format(len(missing), len(extra)))
print("bulk skip links", len(linked))
PY
one=$(python3 "$HUB" --repo "$ROOT" install --dry-run --skill oo-github --clients claude)
echo "$one" | awk '{print $1, $2, $3}' | grep -qx "link claude-code oo-github" || fail "single oomol skill was not planned"
echo "$one" | awk '{print $1, $2, $3}' | grep -qx "link claude-code design-system" && fail "single skill also planned design-system" || true
[ "$(cksum "$ROOT/enabled-skills.txt")" = "$before" ] || fail "skill dry-run changed enabled-skills.txt"

# An empty config directory is not an installed harness.
mkdir -p "$AI_RESOURCES_HOME/.cursor"
out=$(run install --dry-run --skill keepme)
echo "$out" | awk '{print $1, $2, $3}' | grep -qx "link cursor keepme" && fail "empty .cursor counted as installed" || true
rmdir "$AI_RESOURCES_HOME/.cursor"

# A rules/ directory left by another installer is not the Augment app.
mkdir -p "$AI_RESOURCES_HOME/.augment/rules"
printf '%s\n' 'x' > "$AI_RESOURCES_HOME/.augment/rules/note.md"
out=$(run install --dry-run --skill keepme)
echo "$out" | awk '{print $1, $2, $3}' | grep -qx "link augment keepme" && fail "rules-only .augment counted as installed" || true
rm -rf "$AI_RESOURCES_HOME/.augment"

# --cursor is global ~/.cursor/skills, and it does not link the other harnesses.
mkdir -p "$FIX/skills/fixture/gamma"
printf '%s\n' '---' 'name: gamma' 'description: gamma skill' '---' > "$FIX/skills/fixture/gamma/SKILL.md"
run install --skill gamma --cursor >/dev/null
[ -L "$AI_RESOURCES_HOME/.cursor/skills/gamma" ] || fail "cursor global link missing"
[ ! -e "$AI_RESOURCES_HOME/.claude/skills/gamma" ] || fail "--cursor also linked claude"
[ ! -e "$AI_RESOURCES_HOME/.agents/skills/gamma" ] || fail "--cursor also linked codex"
gamma_real=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$FIX/skills/fixture/gamma")
[ "$(readlink "$AI_RESOURCES_HOME/.cursor/skills/gamma")" = "$gamma_real" ] || fail "cursor link target"
run uninstall --skill gamma >/dev/null
[ -f "$AI_RESOURCES_STATE_DIR/manifest.json" ] || fail "filtered uninstall removed the manifest"
python3 - "$AI_RESOURCES_STATE_DIR/manifest.json" << 'PY' || fail "filtered uninstall manifest"
import json, sys
names = {item["name"] for item in json.load(open(sys.argv[1]))["links"]}
if "gamma" in names:
    raise SystemExit("gamma still listed")
if "alpha" not in names:
    raise SystemExit("alpha missing")
PY

# Cline and Zed share Codex's directory. One symlink, named once.
mkdir -p "$AI_RESOURCES_HOME/.cline"
printf '%s\n' '{}' > "$AI_RESOURCES_HOME/.cline/config.json"
out=$(run install --dry-run --skill gamma)
echo "$out" | grep -q "also read by cline" || fail "shared directory was not reported"
echo "$out" | awk '{print $1, $2, $3}' | grep -qx "link cline gamma" && fail "shared directory was linked twice" || true
rm -rf "$AI_RESOURCES_HOME/.cline"

esc=$(printf '\033')
colored=$(env -u NO_COLOR AI_RESOURCES_COLOR=always python3 "$HUB" --repo "$FIX" doctor || true)
case "$colored" in
  *"$esc"*) ;;
  *) fail "color not applied" ;;
esac
plain=$(env -u NO_COLOR -u AI_RESOURCES_COLOR python3 "$HUB" --repo "$FIX" doctor || true)
case "$plain" in
  *"$esc"*) fail "color leaked into a pipe" ;;
esac
muted=$(NO_COLOR=1 AI_RESOURCES_COLOR=always python3 "$HUB" --repo "$FIX" doctor || true)
case "$muted" in
  *"$esc"*) fail "NO_COLOR ignored" ;;
esac

echo "ok"
