# ChatGPT

ChatGPT chat and Codex are different surfaces. This repo links skills for Codex. It does not sync them into a ChatGPT conversation.

| Surface | Reads `skills/` from this repo? | MCP |
| --- | --- | --- |
| Codex CLI, IDE, desktop Codex | Yes, after `install.sh --skill <name>`, from `~/.agents/skills` | `~/.codex/config.toml` via `codex mcp add` |
| ChatGPT on the web or in the desktop chat | No | A plugin you add in ChatGPT, not a symlink |

ChatGPT Plus is enough for Codex, including Codex MCP. That does not mean the chat product loads `SKILL.md` from disk.

OpenAI's current chat docs describe skills and plugins as something you install in ChatGPT, including from a shared plugin directory ([Skills and plugins](https://learn.chatgpt.com/docs/skills-and-plugins)). They also describe adding a remote MCP server as a plugin ([custom MCP server](https://developers.openai.com/api/docs/guides/custom-mcp-server)). Plan and workspace rules decide who can create that plugin. Check the plan you are on before expecting a custom OpenConnector URL to appear in chat. This was not verified by adding a server to an account.

What you can do from chat without a connector:

- Paste a single skill's instructions into a Project or into custom instructions.
- Upload a file for one conversation.

What you should not expect:

- `git pull` updating ChatGPT.
- The `openconnector` skill running in chat unless that chat is actually connected to the MCP server.
- Dokploy or OpenConnector credentials living in this repo.

Codex setup stays in [codex.md](codex.md).
