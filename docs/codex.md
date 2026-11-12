# Codex

Codex is the coding agent in the CLI, the IDE extension, and the Codex desktop app. It is not the ChatGPT conversation window. ChatGPT Plus includes Codex. A skill linked for Codex is still not loaded by ChatGPT chat. See [chatgpt.md](chatgpt.md).

Personal skills: `~/.agents/skills/<name>/SKILL.md`. Project skills: `.agents/skills/` in the repo. Source: [Codex customization](https://learn.chatgpt.com/docs/customization/overview). `~/.codex/skills` is an older location. This installer does not write there, so a skill installed by Codex's own skill installer can sit in a different folder. `./scripts/doctor.sh` only reports the directories this hub uses.

Instructions for every Codex session in a repo go in `AGENTS.md`. Global preferences go in `~/.codex/AGENTS.md`. Closer files win, and Codex stops after about 32KiB of project docs ([AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)). This hub's `AGENTS.md` applies only when Codex is working inside this repo. It is not your global Codex prompt. The installer does not touch either file.

Codex reads skill metadata first and loads `SKILL.md` when the skill is chosen. You can mention a skill explicitly or let the description match. After `./scripts/install.sh --skill <name>` or `./scripts/sync.sh`, start a new Codex session so it rescans the folder. That rescan was not verified in a live Codex session.

## MCP

Codex stores MCP servers in `~/.codex/config.toml`. Add the OpenConnector URL with the CLI rather than pasting a guessed table into Git:

```bash
codex mcp add openconnector --url https://openconnector.example.com/mcp
```

Run `codex mcp add --help` and add the `Authorization: Bearer` header the way that command accepts it. The token stays in `~/.codex/config.toml` on that machine. Do not copy that file into this repo.

ChatGPT Plus login is how the Codex CLI authenticates to OpenAI. It is unrelated to the OpenConnector runtime token.

## Global versus a project

Hub skills are the personal set. A project that needs its own skill commits `.agents/skills/<name>` in that project. Repo rules stay in that repo's `AGENTS.md`.
