# Architecture

Two systems, not one.

```text
this repo                         Dokploy
skills + MCP templates            OpenConnector
        |                               |
        +---- Claude / Codex / Cursor --+
                      MCP
                       |
              GitHub, Gmail, Notion, ...
```

This repo is files in Git. OpenConnector is the integration gateway: OAuth, connections, action execution. A skill does not replace an MCP connection, and an MCP connection does not install `SKILL.md` files.

## Layout

| Path | Role |
| --- | --- |
| `skills/<source>/<name>/` | One Agent Skill inside its catalog. A one-skill source is `skills/other/<name>/`. |
| `docs/skill-origins.json` | Folder, upstream source, version, and whether fetch may replace it. |
| `docs/sources.md` | URLs that were vendored, and what was left behind. |
| `playbooks/openmontage/` | Notes that are not skills. Kept out of `skills/` so clients do not scan them. |
| `upstream/<source>/` | License and bundle files that are not part of a skill. |
| `mcp/dokploy/` | Dokploy MCP server source. Separate from OpenConnector. |
| `mcp/templates/` | Client snippets. Placeholders only. |
| `mcp/catalogs/` | MCP *client* configs found inside vendored repos. Not servers. |

No `instructions/`, `rules/`, or `prompts/` tree. Those files belong in the project that needs them (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`). Adding empty directories here would imply a second copy of instructions the clients already load from the project.

## Why symlinks, per skill

Do not symlink `skills/` or a group such as `skills/ecc/`. Clients only discover a skill when `SKILL.md` is one level under their skills directory. `enabled-skills.txt` is the set that gets linked. `install.sh --skill <name>` links `skills/<group>/<name>` as `~/.claude/skills/<name>` and `~/.agents/skills/<name>`. `install.sh --skip-source oomol --skip-source ecc` is the bulk shortcut that still leaves those two catalogs out. The installer refuses to replace a real directory or a symlink that points outside this repo.

Default targets, checked against current docs:

- Claude Code personal skills: `~/.claude/skills/<name>/SKILL.md` ([Claude Code skills](https://code.claude.com/docs/en/skills)).
- Codex personal skills: `~/.agents/skills` ([Codex customization](https://learn.chatgpt.com/docs/customization/overview)). `~/.codex/skills` is the older Codex path and is not used.
- Cursor reads `~/.agents/skills`, `~/.cursor/skills`, and, for compatibility, `~/.claude/skills` ([Cursor skills](https://cursor.com/docs/skills)). The installer does not also fill `~/.cursor/skills`.

Project skills stay in that project's `.claude/skills` or `.agents/skills`. This hub does not copy itself into application repos.

## Third-party skills

Vendored copies, pinned by commit in `docs/sources.lock.json`. Not submodules: the upstream repos are tools, and we keep only the skill slices. Not the Skills CLI as the installer: `npx skills add -g` writes straight into client directories and skips review. Use it to look, then copy into `skills/` and record the source.

## What is intentionally absent

- A server or database for skill files.
- Automatic MCP login.
- A second copy of each skill per client inside this repo.
- Changes to the deployed Dokploy or OpenConnector instance.
