# Cursor

Cursor loads skills from `.agents/skills/`, `.cursor/skills/`, `~/.agents/skills/`, and `~/.cursor/skills/`. It also loads Claude and Codex compatibility paths: `.claude/skills/`, `.codex/skills/`, `~/.claude/skills/`, and `~/.codex/skills/`. Source: [Cursor Agent Skills](https://cursor.com/docs/skills).

The default install fills `~/.claude/skills` and `~/.agents/skills`. Cursor therefore sees each hub skill twice. Claude Code only reads the first. Codex only reads the second. To keep a single Cursor list, link one side only:

```bash
./scripts/install.sh --skill openconnector --clients codex
```

Cursor still sees those skills through `~/.agents/skills`. Claude Code will not, until you link `claude` too. There is no Cursor setting in this repo that disables the compatibility scan.

`~/.cursor/skills` is not filled by default. Cursor's cloud agents sync that directory, not `~/.agents/skills`. Turn on skill sync in Cursor if a cloud agent must see them, or use `--clients cursor` and accept the extra local copy. Cloud sync was not tested.

Project skills live in that project's `.agents/skills` or `.cursor/skills`. Nested skill directories are scoped to files under that folder. Rules for a project stay in `.cursor/rules/`. Cursor also reads `AGENTS.md` and `CLAUDE.md` in the project. This hub does not generate rules.

Open this repo in Cursor and the grouped `skills/` tree is just files. It is not auto-installed as project skills unless a skill directory sits under `.cursor/skills` or `.agents/skills` here. Those project directories are not created, so opening the hub does not double-register its own catalog on top of the global links.

## MCP

Copy `mcp/templates/openconnector.cursor.json` into `~/.cursor/mcp.json` or a project's `.cursor/mcp.json`. Replace the URL and token locally. Do not commit the filled-in file. If a server is already listed, merge the `openconnector` entry by hand. The installer will not write this file.

Restart the agent session after MCP or skill link changes. Discovery was not verified in this Cursor session beyond reading the docs.
