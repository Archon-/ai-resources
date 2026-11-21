# MCP

Client templates with placeholders are in `templates/`. `scripts/install.sh` does not write them into Claude, Codex, or Cursor. Fill them in on the machine and keep the token out of Git. See [docs/openconnector.md](../docs/openconnector.md).

## Servers

`dokploy/` is the official Dokploy MCP server, [Dokploy/mcp](https://github.com/Dokploy/mcp) `v0.30.7` (`@dokploy/mcp`). Apache-2.0. It was not in the original link list. It is here because this catalog is meant to include the Dokploy server you actually run.

Source only. No `node_modules`. Setup, transports, and tools are in `dokploy/README.md` and `dokploy/TOOLS.md`. Copy `dokploy/.env.example` to `.env` and set `DOKPLOY_URL` and `DOKPLOY_API_KEY`. The example file has placeholders, not real keys.

```bash
cd mcp/dokploy
pnpm install
pnpm build
pnpm start:stdio
```

## Contabo MCP (template only)

[kieksme/mcp-contabo](https://github.com/kieksme/mcp-contabo) (`@kieksme/contabo-mcp` on npm) manages Contabo VPS/VDS, snapshots, object storage, secrets, and domains. It is a stdio server started with `npx`, so nothing is vendored. The template is `templates/contabo.mcp.json`. It has placeholders only. Fill it in on your machine and keep real values out of Git.

It needs four values: client ID, client secret, API user (your Contabo login email), and API password.

**Where to get them.** The Client ID, Client Secret, and Username are in the API section of the new panel (`my.contabo.com/account/security`). The new panel has **no way to create the API password**. Its "Send Link" button resets your control-panel login password, which is not the API password. Set the API password in the **old Contabo UI**: <https://dedicatedserver.contabo.com/api/details>. The panel never shows it again, so store it in a password manager.

The API password is not a Secrets Manager entry. Secrets store credentials for instances.

**Check it before wiring clients.** Request a token with the password grant at `https://auth.contabo.com/auth/realms/contabo/protocol/openid-connect/token`. HTTP 200 means the four values are valid. Do not print the token.

**Register it (user-level config, outside this repo).**

Edit each client's config file by hand. Do not pass the credentials on a command line (`claude mcp add -e ...`, `codex mcp add --env ...`). Command-line arguments land in shell history and are visible in the process list to other local users while the command runs. Typing the values into a file in your editor avoids both.

Restrict each file to your own user first, then add the entry below to it. Check the current mode with `ls -l`. `~/.claude.json` is often created world-readable (`644`).

```bash
chmod 600 ~/.claude.json ~/.codex/config.toml ~/.cursor/mcp.json
```

Each client keeps the values in plain text. Replace the placeholders. Escape `"` and `\` inside JSON and TOML strings. A password with `$` is safe, because no shell reads these files.

**Claude Code** (`~/.claude.json`): add the entry under the top-level `mcpServers` object. Quit Claude Code first, since it rewrites this file.

```json
"contabo": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@kieksme/contabo-mcp"],
  "env": {
    "CONTABO_CLIENT_ID": "YOUR_CONTABO_CLIENT_ID",
    "CONTABO_CLIENT_SECRET": "YOUR_CONTABO_CLIENT_SECRET",
    "CONTABO_API_USER": "YOUR_CONTABO_LOGIN_EMAIL",
    "CONTABO_API_PASSWORD": "YOUR_CONTABO_API_PASSWORD"
  }
}
```

**Codex** (`~/.codex/config.toml`): append these tables.

```toml
[mcp_servers.contabo]
command = "npx"
args = ["-y", "@kieksme/contabo-mcp"]

[mcp_servers.contabo.env]
CONTABO_CLIENT_ID = "YOUR_CONTABO_CLIENT_ID"
CONTABO_CLIENT_SECRET = "YOUR_CONTABO_CLIENT_SECRET"
CONTABO_API_USER = "YOUR_CONTABO_LOGIN_EMAIL"
CONTABO_API_PASSWORD = "YOUR_CONTABO_API_PASSWORD"
```

**Cursor** (`~/.cursor/mcp.json`): merge the `contabo` entry from `templates/contabo.mcp.json` into `mcpServers`.

Then restart the client and confirm with `claude mcp list` or `codex mcp list`. The API password can reach the whole account, so never commit these files.

## Catalogs, not servers

`catalogs/` holds MCP *client configs* found inside the linked repos. They name commands (`npx`, hosted servers). They are not the server source.

- `catalogs/ecc-mcp-servers.json` — 34 server entries from [affaan-m/ECC](https://github.com/affaan-m/ECC) `mcp-configs/mcp-servers.json` (GitHub, Supabase, Playwright, Railway, Cloudflare, and others).
- `catalogs/ui-ux-pro-max.mcp.json` — from [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) `stack/.mcp.json`. Points at `@playwright/mcp`, `chrome-devtools-mcp`, and `shadcn mcp`.

None of the other linked repos shipped an MCP server implementation. Playwright’s MCP server is a different project from the [playwright-cli](https://github.com/microsoft/playwright-cli) skill copied under `skills/playwright-cli`.
