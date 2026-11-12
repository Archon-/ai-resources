# Sources

Fetched 2026-11-12. Pins (version, full commit, license) are in [versions.md](versions.md) and [sources.lock.json](sources.lock.json). Every skill is listed in [skills-index.md](skills-index.md). Which folder came from which upstream repo is in [skill-origins.json](skill-origins.json).

Skills are grouped: `skills/<source>/<name>/SKILL.md`. A source that contains one skill lives in `skills/other/<name>/` (humanizer, taste-skill, impeccable, and the local `openconnector` skill). `scripts/install.sh --skill <name>` symlinks that one skill directory into the client. It does not symlink the group. The saved set is `enabled-skills.txt`.

Refresh everything with `scripts/fetch-sources.sh`. That vendors upstream again, regroups `skills/`, and keeps skills marked `"managed": "local"`. It also refreshes `mcp/dokploy/`, `mcp/catalogs/ecc-mcp-servers.json`, `specs/agent-skills/`, the lock, `versions.md`, and `skills-index.md`. It does not rewrite this file.

One copy of each skill. Host mirrors (`.cursor`, `.claude`, `.agents`, translations) were not copied again. The source id on each row is the `source` field in `skill-origins.json`. The folder above the skill is the `group` field.

## Links

| # | You sent | Source id |
| --- | --- | --- |
| 1 | https://github.com/leonxlnx/taste-skill | `taste-skill` |
| 2 | https://github.com/pbakaus/impeccable | `impeccable` |
| 3 | https://github.com/microsoft/playwright-cli | `playwright-cli` |
| 4 | https://github.com/h4ckf0r0day/obscura | `obscura` |
| 5 | https://github.com/OpenMontageInc/OpenMontage?ref=aitoolnet.com | `openmontage` |
| 6 | https://github.com/affaan-m/ECC/tree/main | `ecc` (MCP client catalog also in `mcp/catalogs/ecc-mcp-servers.json`) |
| 7 | https://github.com/multica-ai/andrej-karpathy-skills | `karpathy-guidelines` |
| 8 | https://github.com/dietrichgebert/ponytail | `ponytail` |
| 9 | https://github.com/addyosmani/agent-skills | `agent-skills` |
| 10 | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | `ui-ux-pro-max` (client catalog also in `mcp/catalogs/ui-ux-pro-max.mcp.json`) |
| 11 | https://github.com/anthropics/skills | `anthropics` (spec pointer in `specs/agent-skills`) |
| 12 | https://github.com/blader/humanizer | `humanizer` |
| 13 | https://github.com/ayghri/i-have-adhd | `i-have-adhd` |
| 14 | https://github.com/coreyhaines31/marketingskills | `marketingskills` |
| 15 | https://github.com/oomol-lab/skills?utm_source=chatgpt.com | `oomol` |
| 16 | https://github.com/GoogleChrome/modern-web-guidance/tree/main/skills | `modern-web-guidance` |

Extra, not in that list: official Dokploy MCP at https://github.com/Dokploy/mcp tag `v0.30.7`, copied to `mcp/dokploy`. See [mcp/README.md](../mcp/README.md).

## What was copied, and what was left

Upstream tools stayed upstream. Only skill folders (and, for Dokploy, the MCP server itself) were copied. A multi-skill source is a directory under `skills/`, and each skill is one level below that. `skills/ecc/accessibility/SKILL.md` is one ECC skill. `skills/other/humanizer/SKILL.md` is the humanizer skill.

### taste-skill

`v2.5.1`, MIT. The repo is a skill. Copied `skills/taste-skill` (instructions, reference library, scripts, and the asset pack, about 37MB of reference images and captured pages). Left `install.sh`, tests, examples, and plugin wrappers.

### impeccable

Release `skill-v4.8.2`, Apache-2.0. Skill frontmatter version is `4.8.2`. `scripts/VERSION` inside the skill is `0.1.22` (launcher), which is not the skill release. Copied the canonical skill at `plugin/skills/impeccable`. The same skill is mirrored into about twenty host folders (`.cursor`, `.claude`, `.agents`, and others); those copies were skipped. The rest of the repo is the design tool and was not copied.

### playwright-cli

`v0.180.0`, Apache-2.0. That tag is the CLI release. Copied `skills/playwright-cli` only. The CLI binary/source and the internal `.claude/skills/dev` skill were not copied. This repo is not the Playwright MCP server. That project is https://github.com/microsoft/playwright-mcp and is not vendored here.

### obscura

`v0.2.6`, Apache-2.0. Copied `skills/obscura/SKILL.md`. The headless browser (Rust crates, vendor trees) was not copied.

### OpenMontage

No release tag. Pinned to commit `fecb9a1e3cc2`. **AGPL-3.0.** If you distribute this catalog, that license applies to `skills/openmontage`.

Copied:

- `.agents/skills` — the agent skill packages (92)
- `.claude/skills/video_toolkit` — the one skill that existed only on the Claude side
- upstream `skills/` markdown playbooks, stored at `skills/openmontage/knowledge` (158 files, not `SKILL.md` packages)

Skipped the production app (pipelines, Remotion composer, tools, tests) and two example `.mp4` files under hyperframes (about 37MB).

### ECC

`v2.2.3`, MIT. Copied the canonical English set in `skills/` (314 skills). This matches the plugin manifest. Skipped translated copies under `docs/`, and the repeats in `.agents`, `.cursor`, `.kiro`, and `pi/`. Also skipped the harness itself: hooks, agents, commands, and scripts. The MCP *client* catalog is in `mcp/catalogs/ecc-mcp-servers.json` (34 entries). ECC does not contain those MCP servers.

### Karpathy guidelines

Plugin version `1.0.0`. No `LICENSE` file in the repo; `plugin.json` says MIT, and the skill frontmatter says MIT. Copied `skills/karpathy-guidelines`. `CLAUDE.md`, `CURSOR.md`, and `EXAMPLES.md` repeat the same guidelines for other hosts and were not copied again.

### ponytail

`v5.3.3`, MIT. Copied `skills/` (ponytail plus audit, debt, gain, help, review). Skipped the per-host copies under `.openclaw` and the plugin manifests.

### agent-skills

`0.6.15`, MIT. Addy Osmani’s engineering skills. Copied `skills/` (25 skills).

### ui-ux-pro-max

`v2.15.0`, MIT. Copied `.claude/skills` (7 skills, including the data files the skills read). `cli/assets/skills` is the same set packaged for the CLI and was not copied again. The CLI, gallery, and preview sites were not copied. `skill.json` is kept next to the skills so the bundle version stays visible. Client MCP config: `mcp/catalogs/ui-ux-pro-max.mcp.json`.

### anthropics/skills

No release tag. Pinned to commit `2c5958ecac7c`. Copied `skills/` plus the root `template/` skill (20 `SKILL.md` files, including document skills and `mcp-builder`). Licenses are per skill; start at `skills/anthropics/THIRD_PARTY_NOTICES.md`. Upstream `spec/agent-skills-spec.md` is only a pointer. It is at `specs/agent-skills/agent-skills-spec.md`. The live spec is https://agentskills.io/specification.

### humanizer

`v4.0.0`, MIT. The skill is the repo-root `SKILL.md` (frontmatter version `4.0.0`), plus `scripts/` and `agents/`. Issue templates and CI were not copied.

### i-have-adhd

`v0.4.1`, MIT. Copied `skills/i-have-adhd`. The repo also has hooks and install scripts that enforce the style outside the skill text. Those were not copied. The skill instructions are complete without them.

### marketingskills

`v2.14.12`, MIT. Copied `skills/` (53 skills). Each skill carries its own `metadata.version`.

### oomol

No release tag. Pinned to commit `136cef67a41a`. MIT. Copied `app-skills/` (1707 skills). Each has `metadata.version`. These are instructions for the [`oo` CLI](https://github.com/oomol-lab/oo-cli). They do not include credentials or connector code. Names that end in `-mcp` are still oo-cli skills, not MCP servers. Registry publish tooling (`contrib/`, package manifests) was not copied.

### modern-web-guidance

`v1.0.0`, Apache-2.0. Pinned to commit `4dd968349e54`. Two skills. Copied `skills/chrome-extensions` (Manifest V3 and Chrome Web Store references) and `skills/modern-web-guidance` (the guide corpus and the skill that searches it). Left the host plugin wrappers, `policies/`, and `assets/`. The `modern-web-guidance` skill searches through `npx -y modern-web-guidance@latest`. The same guides are in the vendored folder.

## Layout

```
skills/<source>/<name>/SKILL.md   one catalog, many skills
skills/other/<name>/SKILL.md      a source that shipped one skill
playbooks/openmontage/            OpenMontage notes that are not SKILL.md packages
upstream/<source>/                license and bundle files that are not skills
mcp/dokploy/                      Dokploy MCP server source
mcp/templates/                    client config templates, no secrets
mcp/catalogs/                     MCP client configs found in the linked repos
docs/skill-origins.json           folder name -> source, group, version, rename
```

Two name clashes were resolved when the trees were merged:

- `design-system` exists in both ECC and UI/UX Pro Max. ECC kept `skills/ecc/design-system`. The UI/UX copy is `skills/ui-ux-pro-max/design-system-ui-ux-pro-max` and its frontmatter `name` was changed to match. Install still uses the directory name, so the two skills do not share one symlink.
- OpenMontage shipped `video-toolkit` twice (`video-toolkit` and `video_toolkit`) with the same files. The extra copy was not kept.

Individual skill versions, when upstream set them, are in the index. The commit in the lock is what you compare on the next update. `./scripts/fetch-sources.sh` vendors upstream again and regroups. Skills with `"managed": "local"` in the origins file, including `openconnector`, are kept under `skills/other/`.
