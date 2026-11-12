# Cursor

Cursor loads skills from `.agents/skills/`, `.cursor/skills/`, `~/.agents/skills/`, and `~/.cursor/skills/`. It also loads Claude and Codex compatibility paths: `.claude/skills/`, `.codex/skills/`, `~/.claude/skills/`, and `~/.codex/skills/`. Source: [Cursor Agent Skills](https://cursor.com/docs/skills).

Cursor's global skills live in `~/.cursor/skills/<name>`. That directory stays on this machine, and it is the one Cursor can sync to cloud agents. `~/.agents/skills` is not copied to cloud agents.

When Cursor is installed, `./scripts/install.sh --skill <name>` links `~/.cursor/skills` and also Claude Code and Codex if those are installed too. Cursor reads all three, plus `~/.codex/skills`, so one skill can show up more than once. `doctor` reports that. To fill only Cursor:

```bash
./scripts/install.sh --skill openconnector --cursor
```

There is no Cursor setting in this repo that turns the compatibility scan off. Cloud sync of `~/.cursor/skills` was not tested from here.

Project skills live in that project's `.agents/skills` or `.cursor/skills`. Nested skill directories are scoped to files under that folder. Rules for a project stay in `.cursor/rules/`. Cursor also reads `AGENTS.md` and `CLAUDE.md` in the project. This hub does not generate rules.

Open this repo in Cursor and the grouped `skills/` tree is just files. It is not auto-installed as project skills unless a skill directory sits under `.cursor/skills` or `.agents/skills` here. Those project directories are not created, so opening the hub does not double-register its own catalog on top of the global links.

## MCP

Copy `mcp/templates/openconnector.cursor.json` into `~/.cursor/mcp.json` or a project's `.cursor/mcp.json`. Replace the URL and token locally. Do not commit the filled-in file. If a server is already listed, merge the `openconnector` entry by hand. The installer will not write this file.

Restart the agent session after MCP or skill link changes. Discovery was not verified in this Cursor session beyond reading the docs.
