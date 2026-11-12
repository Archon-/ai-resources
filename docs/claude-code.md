# Claude Code

Personal skills: `~/.claude/skills/<name>/SKILL.md`. Project skills: `.claude/skills/` in the repo you start Claude in. Source: [Extend Claude with skills](https://code.claude.com/docs/en/skills).

`./scripts/install.sh --skill <name>` links that one skill into the personal directory. It does not link the rest of `skills/`, and it does not create or edit `~/.claude/CLAUDE.md`. Project instructions stay in that project's `CLAUDE.md` and `.claude/rules/`. Claude Code also still loads `.claude/commands/` as the older single-file command shape. This hub does not generate those.

A skill is available when its folder contains `SKILL.md`. The slash name comes from the frontmatter `name`, or from the directory name. Invoke it with `/name`, or let Claude load it when the description matches. Personal skills apply to local projects. They do not apply to Cowork or cloud sessions unless the skill is also enabled on the claude.ai account. That sync is separate and was not set up here.

Check after install: start `claude` in any project and type `/` to look for a skill you expect, such as `openconnector`. This was not run against a live Claude session.

## MCP

User-level servers are stored by Claude Code, not in this repo. From [OpenConnector's client docs](https://github.com/oomol-lab/open-connector/blob/main/docs/client-onboarding.md), the server is remote HTTP:

```bash
claude mcp add --transport http --scope user openconnector \
  https://openconnector.example.com/mcp \
  --header "Authorization: Bearer YOUR_RUNTIME_TOKEN"
```

Confirm the flags with `claude mcp add --help` before running it. A project can instead commit a copy of `mcp/templates/openconnector.claude.json` as `.mcp.json` after you replace the placeholders. Do not commit a filled-in token. The template's `type` and `headers` fields match the current Claude Code HTTP shape; re-check them if the command rejects the file.

Dokploy, if you want that server too, is a local stdio process. See `mcp/templates/dokploy.mcp.json`. Build it from `mcp/dokploy` first (`pnpm install && pnpm build`). That template is not installed automatically.

## Global versus this project

Global skills from this hub are visible in every local project. A project's own `.claude/skills` and `CLAUDE.md` are the right place for that repo's build commands and business rules. You do not need to copy the hub into the project.
