# OpenConnector

I suggest configuring each client to call [OpenConnector](https://github.com/oomol-lab/open-connector) over MCP. This repo only holds the skill and the templates. It does not host the server. Where you run OpenConnector is your choice. See the [proposed architecture](architecture.md).

```text
Claude Code, Codex, Cursor
        |  one MCP server each, same URL
        v
https://openconnector.example.com/mcp
        |
        v
GitHub, Gmail, Notion, Slack, ...
```

Replace the example host with your deployment when you configure a client. Do not put that hostname, or the token, in Git.

## MCP tools versus skills

MCP tools are the live API: list apps, search actions, run an action. The `openconnector` skill is text that tells the agent to use those tools in order and to stop when the tools are missing. Installing the skill does not create the connection. Connecting the server does not install the skill.

The vendored `oo-*` skills call the `oo` CLI. That is a different product. If OpenConnector is connected, skip those skills:

```bash
./scripts/install.sh --skip-source oomol --skip-source ecc
```

To keep one `oo-*` skill anyway: `./scripts/install.sh --skill oo-github`.

## Configure a client

Use a runtime token from OpenConnector. Least privilege: restrict `allowedActions` and `allowedConnections` on that token. Do not reuse the admin token (`OOMOL_CONNECT_ADMIN_TOKEN`) as the agent token.

| Client | Where the secret lives | Template |
| --- | --- | --- |
| Claude Code | Claude's user MCP config, or a gitignored `.mcp.json` | `mcp/templates/openconnector.claude.json` |
| Codex | `~/.codex/config.toml` | command in [codex.md](codex.md) |
| Cursor | `~/.cursor/mcp.json` | `mcp/templates/openconnector.cursor.json` |

Official shape, from OpenConnector:

```json
{
  "mcpServers": {
    "open-connector": {
      "url": "https://openconnector.example.com/mcp",
      "headers": { "Authorization": "Bearer YOUR_RUNTIME_TOKEN" }
    }
  }
}
```

The endpoint is `POST /mcp`. It is stateless HTTP, not a long-lived SSE stream.

## How the agent should call it

`skills/other/openconnector/SKILL.md` is the procedure:

1. `list_apps`
2. `list_connections`
3. `search_actions`
4. `get_action_guide`
5. `execute_action`

Action ids come from search and the guide, not from memory. `connectionName` is optional and must be a name `list_connections` returned. Connection payloads do not include stored credentials.

These steps configure the client on your machine. They do not change a running OpenConnector server.
