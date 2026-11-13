#!/usr/bin/env bash
# Re-fetch vendored skills and the Dokploy MCP into this repo.
# Overwrites the destination folders below. Does not touch docs prose
# except docs/sources.lock.json (commit pins).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${TMPDIR:-/tmp}/ai-resources-fetch-$$"
mkdir -p "$SRC"
cleanup() { rm -rf "$SRC"; }
trap cleanup EXIT

clone_sparse() {
  local name="$1" url="$2"
  shift 2
  local dest="$SRC/$name"
  echo ">> clone $name"
  git clone --depth 1 --filter=blob:none --sparse "$url" "$dest" >/dev/null
  git -C "$dest" sparse-checkout set "$@"
  echo "   $(git -C "$dest" rev-parse HEAD)  $name"
}

clone_tag() {
  local name="$1" url="$2" tag="$3"
  local dest="$SRC/$name"
  echo ">> clone $name @ $tag"
  git clone --depth 1 --branch "$tag" "$url" "$dest" >/dev/null
  echo "   $(git -C "$dest" rev-parse HEAD)  $name"
}

copy_dir() {
  local from="$1" to="$2"
  mkdir -p "$to"
  rsync -a --delete \
    --exclude '.git/' \
    --exclude '*.mp4' \
    "$from/" "$to/"
}

# --- clones (public GitHub) ---
pids=()
clone_sparse taste-skill https://github.com/leonxlnx/taste-skill.git \
  skills/taste-skill & pids+=($!)
clone_sparse impeccable https://github.com/pbakaus/impeccable.git \
  plugin/skills/impeccable & pids+=($!)
clone_sparse playwright-cli https://github.com/microsoft/playwright-cli.git \
  skills/playwright-cli & pids+=($!)
clone_sparse obscura https://github.com/h4ckf0r0day/obscura.git \
  skills/obscura & pids+=($!)
clone_sparse openmontage https://github.com/OpenMontageInc/OpenMontage.git \
  .agents/skills skills .claude/skills/video_toolkit & pids+=($!)
clone_sparse ecc https://github.com/affaan-m/ECC.git \
  skills mcp-configs & pids+=($!)
clone_sparse karpathy https://github.com/multica-ai/andrej-karpathy-skills.git \
  skills/karpathy-guidelines & pids+=($!)
clone_sparse ponytail https://github.com/dietrichgebert/ponytail.git \
  skills & pids+=($!)
clone_sparse agent-skills https://github.com/addyosmani/agent-skills.git \
  skills & pids+=($!)
clone_sparse ui-ux-pro-max https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git \
  .claude/skills & pids+=($!)
clone_sparse anthropics https://github.com/anthropics/skills.git \
  skills spec template & pids+=($!)
clone_sparse humanizer https://github.com/blader/humanizer.git \
  scripts agents & pids+=($!)
clone_sparse i-have-adhd https://github.com/ayghri/i-have-adhd.git \
  skills/i-have-adhd & pids+=($!)
clone_sparse marketingskills https://github.com/coreyhaines31/marketingskills.git \
  skills & pids+=($!)
clone_sparse oomol https://github.com/oomol-lab/skills.git \
  app-skills & pids+=($!)
clone_tag modern-web-guidance https://github.com/GoogleChrome/modern-web-guidance.git v1.0.0 & pids+=($!)
clone_tag dokploy https://github.com/Dokploy/mcp.git v0.30.7 & pids+=($!)

fail=0
for pid in "${pids[@]}"; do
  wait "$pid" || fail=1
done
if [[ "$fail" -ne 0 ]]; then
  echo "one or more clones failed" >&2
  exit 1
fi

# Humanizer's SKILL.md is a root file. Sparse cone checkouts include root files.
# Make sure it is present even if a future git skips root files.
if [[ ! -f "$SRC/humanizer/SKILL.md" ]]; then
  git -C "$SRC/humanizer" sparse-checkout add SKILL.md LICENSE
fi

copy_license() {
  local name="$1" dest="$2"
  if [[ -f "$SRC/$name/LICENSE" ]]; then
    cp "$SRC/$name/LICENSE" "$dest/LICENSE"
  elif [[ -f "$SRC/$name/LICENSE.md" ]]; then
    cp "$SRC/$name/LICENSE.md" "$dest/LICENSE.md"
  fi
}

# Nested staging tree. assemble_skills.py groups it under skills/<source>/, or skills/other/ for a one-skill source.
STAGE="$SRC/nested"
mkdir -p "$STAGE"

# --- skills ---
copy_dir "$SRC/taste-skill/skills/taste-skill" "$STAGE/taste-skill"
copy_license taste-skill "$STAGE/taste-skill"

copy_dir "$SRC/impeccable/plugin/skills/impeccable" "$STAGE/impeccable"
copy_license impeccable "$STAGE/impeccable"

copy_dir "$SRC/playwright-cli/skills/playwright-cli" "$STAGE/playwright-cli"
copy_license playwright-cli "$STAGE/playwright-cli"

copy_dir "$SRC/obscura/skills/obscura" "$STAGE/obscura"
copy_license obscura "$STAGE/obscura"

copy_dir "$SRC/openmontage/.agents/skills" "$STAGE/openmontage"
mkdir -p "$STAGE/openmontage/knowledge" "$STAGE/openmontage/video_toolkit"
copy_dir "$SRC/openmontage/skills" "$STAGE/openmontage/knowledge"
if [[ -d "$SRC/openmontage/.claude/skills/video_toolkit" ]]; then
  copy_dir "$SRC/openmontage/.claude/skills/video_toolkit" "$STAGE/openmontage/video_toolkit"
fi
copy_license openmontage "$STAGE/openmontage"

copy_dir "$SRC/ecc/skills" "$STAGE/ecc"
copy_license ecc "$STAGE/ecc"

copy_dir "$SRC/karpathy/skills/karpathy-guidelines" "$STAGE/karpathy-guidelines"

copy_dir "$SRC/ponytail/skills" "$STAGE/ponytail"
copy_license ponytail "$STAGE/ponytail"

copy_dir "$SRC/agent-skills/skills" "$STAGE/agent-skills"
copy_license agent-skills "$STAGE/agent-skills"

copy_dir "$SRC/ui-ux-pro-max/.claude/skills" "$STAGE/ui-ux-pro-max"
copy_license ui-ux-pro-max "$STAGE/ui-ux-pro-max"
if [[ -f "$SRC/ui-ux-pro-max/skill.json" ]]; then
  cp "$SRC/ui-ux-pro-max/skill.json" "$STAGE/ui-ux-pro-max/skill.json"
fi

copy_dir "$SRC/anthropics/skills" "$STAGE/anthropics"
if [[ -d "$SRC/anthropics/template" ]]; then
  copy_dir "$SRC/anthropics/template" "$STAGE/anthropics/template"
fi
if [[ -f "$SRC/anthropics/THIRD_PARTY_NOTICES.md" ]]; then
  cp "$SRC/anthropics/THIRD_PARTY_NOTICES.md" "$STAGE/anthropics/THIRD_PARTY_NOTICES.md"
fi
copy_license anthropics "$STAGE/anthropics"
mkdir -p "$ROOT/specs/agent-skills"
copy_dir "$SRC/anthropics/spec" "$ROOT/specs/agent-skills"

mkdir -p "$STAGE/humanizer"
cp "$SRC/humanizer/SKILL.md" "$STAGE/humanizer/SKILL.md"
copy_license humanizer "$STAGE/humanizer"
if [[ -d "$SRC/humanizer/scripts" ]]; then
  copy_dir "$SRC/humanizer/scripts" "$STAGE/humanizer/scripts"
fi
if [[ -d "$SRC/humanizer/agents" ]]; then
  copy_dir "$SRC/humanizer/agents" "$STAGE/humanizer/agents"
fi

copy_dir "$SRC/i-have-adhd/skills/i-have-adhd" "$STAGE/i-have-adhd"
copy_license i-have-adhd "$STAGE/i-have-adhd"

copy_dir "$SRC/marketingskills/skills" "$STAGE/marketingskills"
copy_license marketingskills "$STAGE/marketingskills"

copy_dir "$SRC/oomol/app-skills" "$STAGE/oomol"
copy_license oomol "$STAGE/oomol"

copy_dir "$SRC/modern-web-guidance/skills" "$STAGE/modern-web-guidance"
copy_license modern-web-guidance "$STAGE/modern-web-guidance"

python3 "$ROOT/scripts/assemble_skills.py" --nested "$STAGE" --repo "$ROOT"

# --- mcp ---
mkdir -p "$ROOT/mcp/dokploy" "$ROOT/mcp/catalogs"
rsync -a --delete \
  --exclude '.git/' \
  --exclude '.github/' \
  --exclude 'node_modules/' \
  "$SRC/dokploy/" "$ROOT/mcp/dokploy/"

if [[ -f "$SRC/ecc/mcp-configs/mcp-servers.json" ]]; then
  cp "$SRC/ecc/mcp-configs/mcp-servers.json" "$ROOT/mcp/catalogs/ecc-mcp-servers.json"
fi

# --- lock ---
python3 - "$ROOT" "$SRC" <<'PY'
import json, subprocess, sys
from pathlib import Path
root = Path(sys.argv[1])
src = Path(sys.argv[2])

clone_dirs = {
    "karpathy-guidelines": "karpathy",
    "dokploy-mcp": "dokploy",
}

def sha(name):
    folder = clone_dirs.get(name, name)
    return subprocess.check_output(["git", "-C", str(src/folder), "rev-parse", "HEAD"], text=True).strip()

origins = json.loads((root / "docs" / "skill-origins.json").read_text())
group_by_source = {}
for meta in origins.get("skills", {}).values():
    group_by_source.setdefault(meta.get("source"), meta.get("group") or "other")

def local_for(source_id, fallback):
    if source_id == "dokploy-mcp":
        return fallback
    return "skills/" + group_by_source.get(source_id, "other")

sources = [
    ("taste-skill", "https://github.com/leonxlnx/taste-skill", "v2.5.1", "MIT", "skills/", ["skills/taste-skill"]),
    ("impeccable", "https://github.com/pbakaus/impeccable", "skill-v4.8.2", "Apache-2.0", "skills/", ["plugin/skills/impeccable"]),
    ("playwright-cli", "https://github.com/microsoft/playwright-cli", "v0.180.0", "Apache-2.0", "skills/", ["skills/playwright-cli"]),
    ("obscura", "https://github.com/h4ckf0r0day/obscura", "v0.2.6", "Apache-2.0", "skills/", ["skills/obscura"]),
    ("openmontage", "https://github.com/OpenMontageInc/OpenMontage", None, "AGPL-3.0", "skills/", [".agents/skills", "skills", ".claude/skills/video_toolkit"]),
    ("ecc", "https://github.com/affaan-m/ECC", "v2.2.3", "MIT", "skills/", ["skills"]),
    ("karpathy-guidelines", "https://github.com/multica-ai/andrej-karpathy-skills", "1.0.0", "MIT (plugin.json; no LICENSE file)", "skills/", ["skills/karpathy-guidelines"]),
    ("ponytail", "https://github.com/dietrichgebert/ponytail", "v5.3.3", "MIT", "skills/", ["skills"]),
    ("agent-skills", "https://github.com/addyosmani/agent-skills", "0.6.15", "MIT", "skills/", ["skills"]),
    ("ui-ux-pro-max", "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill", "v2.15.0", "MIT", "skills/", [".claude/skills"]),
    ("anthropics", "https://github.com/anthropics/skills", None, "per-skill (mostly Apache-2.0); see THIRD_PARTY_NOTICES.md", "skills/", ["skills", "template", "spec"]),
    ("humanizer", "https://github.com/blader/humanizer", "v4.0.0", "MIT", "skills/", ["SKILL.md", "scripts", "agents"]),
    ("i-have-adhd", "https://github.com/ayghri/i-have-adhd", "v0.4.1", "MIT", "skills/", ["skills/i-have-adhd"]),
    ("marketingskills", "https://github.com/coreyhaines31/marketingskills", "v2.14.12", "MIT", "skills/", ["skills"]),
    ("oomol", "https://github.com/oomol-lab/skills", None, "MIT", "skills/", ["app-skills"]),
    ("modern-web-guidance", "https://github.com/GoogleChrome/modern-web-guidance", "v1.0.0", "Apache-2.0", "skills/", ["skills"]),
    ("dokploy-mcp", "https://github.com/Dokploy/mcp", "v0.30.7", "see mcp/dokploy/LICENSE", "mcp/dokploy", ["."]),
]
lock = {
    "fetched_at": "2026-11-12",
    "sources": [
        {
            "id": i,
            "url": url,
            "tag_or_version": tag,
            "commit": sha(i),
            "license": lic,
            "local_path": local_for(i, local),
            "upstream_paths": paths,
        }
        for i, url, tag, lic, local, paths in sources
    ],
}
out = root / "docs" / "sources.lock.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(lock, indent=2) + "\n")
print(f"wrote {out}")
PY

python3 "$ROOT/scripts/build-catalog.py"
echo "fetch done"
