# AI resources

One Git repo for agent skills and MCP templates. Claude Code, Codex, and Cursor read the same skill files through symlinks. [OpenConnector](https://github.com/oomol-lab/open-connector), on Dokploy, is the separate MCP gateway for GitHub, Gmail, Notion, Slack, and other APIs. This repo does not store those credentials and it does not run OpenConnector.

## What this replaces

Personal copies of the same skill under `~/.claude/`, `~/.codex/`, `~/.agents/`, and `~/.cursor/`, each edited by hand. Project repos keep their own `AGENTS.md`, `CLAUDE.md`, and `.cursor/rules`. They do not get a full copy of this hub.

## Clients

| Client | Skills this installer links | MCP config |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/<name>` | `claude mcp add` — [docs/claude-code.md](docs/claude-code.md) |
| Codex | `~/.agents/skills/<name>` | `codex mcp add` — [docs/codex.md](docs/codex.md) |
| Cursor | no third directory by default | `~/.cursor/mcp.json` — [docs/cursor.md](docs/cursor.md) |
| ChatGPT web/desktop | not linked | not automatic — [docs/chatgpt.md](docs/chatgpt.md) |

Cursor also reads `~/.claude/skills` and `~/.agents/skills`. Linking both, which is the default, can list each skill twice in Cursor. Claude Code and Codex do not.

## Install on a new Mac

```bash
git clone <this-repo> ~/Projects/GitHub/ai-resources
cd ~/Projects/GitHub/ai-resources
./scripts/install.sh --skill openconnector
./scripts/doctor.sh
```

`install.sh` with no arguments links only the names in `enabled-skills.txt`. That file starts empty, so a plain install does not symlink the catalog. Skills are stored as `skills/<source>/<name>/`, and a one-skill source is `skills/other/<name>/`. Each `--skill` links that one folder into Claude Code and Codex. It does not link the source directory. Cursor reads those two client directories. The script does not replace a real folder or someone else's symlink, and it does not edit `CLAUDE.md`, `AGENTS.md`, or MCP settings.

Link one OOMOL skill and one ECC skill without the rest of those catalogs:

```bash
./scripts/install.sh --skill oo-github
./scripts/install.sh --skill design-system
```

Link every skill except those two large catalogs (~45k tokens of descriptions instead of ~134k):

```bash
./scripts/install.sh --skip-source oomol --skip-source ecc
```

## Add a skill

Put `skills/other/<name>/SKILL.md` in this repo. For a skill you wrote, add an entry to `docs/skill-origins.json` with `"managed": "local"` so `fetch-sources.sh` will not delete it. Then:

```bash
./scripts/install.sh --skill <name>
```

Review third-party skills before vendoring them. [skills.sh](https://skills.sh/) and `npx skills add` are fine for discovery. Do not point that CLI at your home directory if this repo is the copy you track. Copy the skill into `skills/other/<name>/`, record the URL and commit in `docs/sources.md`, then `./scripts/install.sh --skill <name>`. Details: [docs/installation.md](docs/installation.md).

## Update

```bash
git pull
./scripts/fetch-sources.sh   # only when refreshing vendored upstream skills
./scripts/sync.sh            # relink whatever enabled-skills.txt still lists
```

`sync.sh --dry-run` prints link and unlink actions and changes nothing. A name removed from `enabled-skills.txt`, or a folder removed from `skills/`, loses its symlink on sync.

## Remove a skill

Remove one linked skill and leave the others:

```bash
./scripts/uninstall.sh --skill oo-github
```

`./scripts/uninstall.sh` with no arguments drops every symlink this repo created. It does not delete skills inside the repo, and it does not touch a skill you installed some other way.

## OpenConnector

Connect each client to the same server. Templates with placeholders, not real tokens: `mcp/templates/`. The skill that teaches the tool sequence is `skills/other/openconnector`. It does not open the connection by itself. Steps: [docs/openconnector.md](docs/openconnector.md).

## Limits

- ChatGPT's chat UI does not read this repo. Codex does, and ChatGPT Plus includes Codex. Those are different products. See [docs/chatgpt.md](docs/chatgpt.md).
- About 2,200 skills ship vendored. Clients load name and description for each one. That catalog is large. Skip sources you do not want linked.
- OpenMontage skills are AGPL-3.0 (`upstream/openmontage/LICENSE`).
- Symlinks are a macOS and Linux mechanism. Windows needs Developer Mode or a different link type. Not set up here.
- Nothing here was executed inside Claude Code, Codex, or Cursor. The linker was tested in a temporary home directory.

More: [docs/architecture.md](docs/architecture.md), [docs/sources.md](docs/sources.md), [docs/skills-index.md](docs/skills-index.md), [docs/pipelines.md](docs/pipelines.md).

## Pipelines

Pull requests, pushes to `main`, and a Monday 07:00 UTC run all execute `python3 scripts/scan_skills.py`. That fails if a skill contains a live secret or a URL piped into a shell. Monday at 08:00 UTC, `python3 scripts/check_updates.py` compares the pins in `docs/sources.lock.json` with GitHub and opens a "Skills to update" issue when a newer same-prefix tag exists, or an untagged branch tip has moved. Details: [docs/pipelines.md](docs/pipelines.md).
