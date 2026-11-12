# Proposed architecture

This is a suggestion for how to configure the clients. It is not a system this repo deploys. Dokploy is not part of it.

```text
this repo                         OpenConnector
skills + MCP templates            MCP gateway you run
        |                               |
        | symlink, per skill            | MCP
        v                               v
        +---- Claude / Codex / Cursor --+
                                        |
                                        | MCP
                                        v
                              GitHub, Gmail, Notion, ...
```

I suggest configuring it this way. Keep the skill files in this repo and link the ones you want into each client. Point those same clients at one OpenConnector server for GitHub, Gmail, Notion, Slack, and the other APIs. Host that server wherever you already run services. This repo does not install it, and it does not store the token.

This repo is files in Git. OpenConnector is the integration gateway: OAuth, connections, action execution. A skill does not replace an MCP connection, and an MCP connection does not install `SKILL.md` files.

## Layout

| Path | Role |
| --- | --- |
| `skills/<source>/<name>/` | One Agent Skill inside its catalog. A one-skill source is `skills/other/<name>/`. |
| `docs/skill-origins.json` | Folder, upstream source, version, and whether fetch may replace it. |
| `docs/sources.md` | URLs that were vendored, and what was left behind. |
| `playbooks/openmontage/` | Notes that are not skills. Kept out of `skills/` so clients do not scan them. |
| `upstream/<source>/` | License and bundle files that are not part of a skill. |
| `mcp/templates/` | Client snippets for the suggested OpenConnector setup. Placeholders only. |
| `mcp/catalogs/` | MCP *client* configs found inside vendored repos. Not servers. |

No `instructions/`, `rules/`, or `prompts/` tree. Those files belong in the project that needs them (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`). Adding empty directories here would imply a second copy of instructions the clients already load from the project.

## How the symlinks work

One skill is one directory, and `SKILL.md` sits inside that directory. In this repo the directory is nested under a group:

```text
skills/ecc/accessibility/SKILL.md
skills/other/openconnector/SKILL.md
```

Claude Code, Codex, and Cursor do not walk `skills/`. Each client looks in its own skills directory and treats every *immediate* child as one skill. That child has to contain `SKILL.md`:

```text
~/.claude/skills/<name>/SKILL.md
~/.agents/skills/<name>/SKILL.md
```

`<name>` is the skill directory (`openconnector`, `accessibility`), not the group (`other`, `ecc`).

A symlink of `skills/` or of a group such as `skills/ecc/` would put the group name where the client expects a skill. `SKILL.md` would be one directory too deep, so the skill would not load. The installer therefore never links a group. It links one skill directory, under the skill's own name.

`enabled-skills.txt` is the list of those names. It starts with no names, so a plain `./scripts/install.sh` creates nothing. `./scripts/install.sh --skill openconnector` appends that name and creates one symlink per default client. The link is absolute, and it points at the directory in this repo. Nothing is copied:

```text
~/.claude/skills/openconnector -> <this-repo>/skills/other/openconnector
~/.agents/skills/openconnector -> <this-repo>/skills/other/openconnector
```

Both links are the same folder. Edit `SKILL.md` in the repo and both clients read that edit. The client opens `~/.claude/skills/openconnector/SKILL.md` and follows the link to `skills/other/openconnector/SKILL.md`.

With no harness flag, the installer links every harness it finds on the machine. Claude Code, Codex, and Cursor are the usual three. `./scripts/install.sh --skill <name> --cursor` links only Cursor. Cursor's own global directory is `~/.cursor/skills/<name>`. Cursor also reads `~/.claude/skills` and `~/.agents/skills`, so the same skill can appear more than once. `doctor` reports that.

`./scripts/sync.sh` makes the client directories match `enabled-skills.txt` when that file lists names. A name removed while other names remain, or a skill folder removed while its name is still listed, loses its symlink. With no names in the file, sync returns before it plans removals, and the links already present stay. Sync removes a symlink only when its target resolves within this repo's `skills/` directory. A link that resolves outside that directory stays in place.

The installer will not replace a real directory at the destination, and it will not replace a symlink that resolves outside `skills/`. Move that copy aside, then re-run. `./scripts/install.sh --skip-source oomol --skip-source ecc` is the bulk shortcut that still leaves those two catalogs out.

Default targets, checked against current docs:

- Claude Code personal skills: `~/.claude/skills/<name>/SKILL.md` ([Claude Code skills](https://code.claude.com/docs/en/skills)).
- Codex personal skills: `~/.agents/skills` ([Codex customization](https://learn.chatgpt.com/docs/customization/overview)). `~/.codex/skills` is the older Codex path and is not used.
- Cursor's global skills are `~/.cursor/skills/<name>/SKILL.md` ([Cursor skills](https://cursor.com/docs/skills)). The installer fills that directory when Cursor is installed. Cursor also reads `~/.agents/skills`, `~/.claude/skills`, and `~/.codex/skills`.

Project skills stay in that project's `.claude/skills` or `.agents/skills`. This hub does not copy itself into application repos.

## Third-party skills

Vendored copies, pinned by commit in `docs/sources.lock.json`. Not submodules: the upstream repos are tools, and we keep only the skill slices. Not the Skills CLI as the installer: `npx skills add -g` writes straight into client directories and skips review. Use it to look, then copy into `skills/` and record the source.

## What is intentionally absent

- A server or database for skill files.
- Automatic MCP login.
- A second copy of each skill per client inside this repo.
- A deployment of OpenConnector. The skill and the templates are here. The running server is not.
