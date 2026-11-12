# Installation and sync

The catalog stays in `skills/`. Nothing is linked until you name it. The chosen names are saved in `enabled-skills.txt` so the next machine, and `sync.sh`, can repeat the same set.

Scripts never write MCP config. They create one symlink per selected skill. `<name>` is the skill directory (`openconnector`), not the group (`other`). The client opens `~/.claude/skills/openconnector/SKILL.md`, the symlink resolves into this repo, and the bytes it reads are `skills/other/openconnector/SKILL.md`. Same file. No copy.

| Client | Link |
| --- | --- |
| Claude Code | `~/.claude/skills/<name>` → `<this-repo>/skills/<group>/<name>` |
| Codex | `~/.agents/skills/<name>` → `<this-repo>/skills/<group>/<name>` |
| Cursor | `~/.cursor/skills/<name>` → the same directory, when Cursor is installed |

Linking `skills/` or `skills/<group>/` does not work. Clients only look one level down, and `SKILL.md` would sit one directory too deep. Detail: [architecture.md](architecture.md).

```bash
./scripts/install.sh --skill openconnector
./scripts/install.sh --skill oo-github --skill design-system
./scripts/install.sh --dry-run --skill oo-gmail
./scripts/doctor.sh
./scripts/sync.sh
./scripts/uninstall.sh --skill oo-github
./scripts/uninstall.sh
```

`--skill` can be repeated. It adds those skills and leaves every other link alone. `oo-github` is one OOMOL skill. `design-system` is one ECC skill. You do not have to take the rest of either catalog.

A plain `./scripts/install.sh` links whatever is already listed in `enabled-skills.txt`. The file ships with no names, so that command links nothing until you add one.

## Bulk, except the large catalogs

This links every skill except `oomol` (1,707 skills) and `ecc` (314). It also removes links this repo already made for those two sources, and rewrites `enabled-skills.txt` to the new set.

```bash
./scripts/install.sh --skip-source oomol --skip-source ecc
```

Do not combine `--skill` and `--skip-source` in one command. Use `--skill` to add a single skill from a catalog you otherwise skip:

```bash
./scripts/install.sh --skip-source oomol --skip-source ecc
./scripts/install.sh --skill oo-github
```

`--dry-run` prints the links and changes neither the home directory nor `enabled-skills.txt`.

## Harnesses

No flag links every harness found on this machine. A flag limits the run to that harness. `--clients` still takes a comma list. `claude`, `copilot`, and `gemini` are aliases for the longer ids.

A harness is installed when its binary is on `PATH`, or its config directory exists and contains something besides skill drop folders (`skills`, `rules`, `global_skills`). An empty config directory does not count. `~/.gemini` does not count as Gemini CLI when the only other folder is `antigravity`. Passing the flag links that harness even when it is not detected.

```bash
./scripts/install.sh --skill openconnector --claude-code
./scripts/install.sh --skill openconnector --cursor
./scripts/install.sh --skill openconnector --clients claude,codex
```

Paths below are the global skill directories. Project skill directories are not touched. Codex uses `~/.agents/skills`. `~/.codex/skills` is the older Codex path and is not written. Warp, Pi, and Kimi Code CLI also read `~/.agents/skills`, so a Codex or Cline link covers them.

| Flag | Global directory | Detected from |
| --- | --- | --- |
| `--claude-code` | `~/.claude/skills` | `claude`, or `~/.claude` |
| `--codex` | `~/.agents/skills` | `codex`, or `~/.codex` |
| `--cursor` | `~/.cursor/skills` | `cursor`, or `~/.cursor` |
| `--github-copilot` | `~/.copilot/skills` | `~/.copilot` |
| `--windsurf` | `~/.codeium/windsurf/skills` | `windsurf`, `~/.codeium/windsurf`, or `~/.windsurf` |
| `--cline` | `~/.agents/skills` | `cline`, or `~/.cline` |
| `--gemini-cli` | `~/.gemini/skills` | `gemini`, or `~/.gemini` |
| `--opencode` | `~/.config/opencode/skills` | `opencode`, `~/.config/opencode`, or `~/.local/share/opencode` |
| `--continue` | `~/.continue/skills` | `~/.continue` |
| `--amp` | `~/.config/agents/skills` | `amp`, `~/.config/amp`, or `~/.amp` |
| `--roo` | `~/.roo/skills` | `~/.roo` |
| `--kilo` | `~/.kilo/skills` | `kilo`, `~/.kilo`, or `~/.kilocode` |
| `--augment` | `~/.augment/skills` | `~/.augment` |
| `--zed` | `~/.agents/skills` | `zed`, or `~/.config/zed` |

Codex, Cline, and Zed share one directory. The installer creates that symlink once and says who else reads it. Cursor reads `~/.cursor/skills`, and also `~/.claude/skills` and `~/.agents/skills`. Links in more than one of those can show the skill more than once in Cursor. `doctor` reports that. Cursor cloud agents sync `~/.cursor/skills`, not `~/.agents/skills`.

`install` and `doctor` color their status when stdout is a terminal. `NO_COLOR` turns that off. A pipe stays plain.

## Conflicts

If `~/.claude/skills/foo` is already a real directory, or a symlink to another place, the script leaves it and exits non-zero. Move that copy aside, then re-run.

A broken symlink that still points into this repo is replaced on install. `sync` removes it when the skill is gone from `enabled-skills.txt` or from `skills/`.

State for this machine is `~/.local/share/ai-resources/manifest.json` unless `AI_RESOURCES_STATE_DIR` is set. Uninstall decides what it owns by the symlink target, not only by that file. A skill you installed some other way is left in place.

## Add a skill you wrote

```bash
mkdir -p skills/other/my-skill
# write skills/other/my-skill/SKILL.md
```

A catalog with several skills of your own uses `skills/<group>/<name>/` instead of `other`.

Add `my-skill` to `docs/skill-origins.json` with `"managed": "local"` and `"group": "other"`. Then `./scripts/install.sh --skill my-skill`.

## Vendor someone else's skill

1. Read the skill, its scripts, and its license.
2. Copy the skill directory into `skills/other/<name>/`, or into `skills/<source>/<name>/` when you are vendoring a whole catalog. Do not run upstream `curl | sh` installers.
3. Add the URL, version, and commit to `docs/sources.md`.
4. Add an origins entry. Use `"managed": "local"` if `fetch-sources.sh` does not know this source. A skill without that flag is removed the next time upstream is reassembled.
5. `./scripts/install.sh --skill <name>`.

`npx skills add <owner>/<repo> --list` can show what a repo contains. Do not use `-g` if this hub is the copy you want to keep.

## Refresh vendored skills

```bash
./scripts/fetch-sources.sh
./scripts/sync.sh
```

`sync.sh` makes the client directories match `enabled-skills.txt`. It does not add the rest of the catalog. If that file has no names, sync does nothing.

Fetch reclones the pinned upstream repos, groups them under `skills/<source>/` (or `skills/other/` when the source has one skill), and keeps `managed: local` skills. It overwrites vendored skill files, including local edits inside those folders. Keep your own changes in a `local` skill instead of editing a vendored one in place.

## Another machine

Clone the repo and run `./scripts/install.sh`. That replays `enabled-skills.txt` onto this machine. Commit that file when the set should follow you. MCP tokens stay in each machine's client config, not in Git.

## Tests

The linker was run against a temporary `HOME` only. Re-run that check with:

```bash
./scripts/test-hub.sh
```
