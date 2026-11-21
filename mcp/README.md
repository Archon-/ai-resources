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

Read the values into shell variables first. `read -rs` keeps them out of shell history, hides them on screen, and does not expand `$`, quotes, or backslashes in what you type. Run these in a shell session you close afterwards. Use `read` with the same flags for each variable.

```bash
read -rp  'Client ID: '     CONTABO_CLIENT_ID
read -rsp 'Client secret: ' CONTABO_CLIENT_SECRET; echo
read -rp  'API user: '      CONTABO_API_USER
read -rsp 'API password: '  CONTABO_API_PASSWORD; echo
```

In zsh, `read -rp` means something else (`-p` reads from a coprocess). Use `vared -p 'Client ID: ' -c CONTABO_CLIENT_ID`, or `read -r "CONTABO_CLIENT_ID?Client ID: "` and `read -rs "CONTABO_CLIENT_SECRET?Client secret: "`.

Then register the server. Always wrap the variables in double quotes, so a password such as `P$word` or one with spaces reaches the client unchanged:

```bash
# Claude Code
claude mcp add -s user contabo \
  -e CONTABO_CLIENT_ID="$CONTABO_CLIENT_ID" -e CONTABO_CLIENT_SECRET="$CONTABO_CLIENT_SECRET" \
  -e CONTABO_API_USER="$CONTABO_API_USER" -e CONTABO_API_PASSWORD="$CONTABO_API_PASSWORD" \
  -- npx -y @kieksme/contabo-mcp

# Codex
codex mcp add contabo \
  --env CONTABO_CLIENT_ID="$CONTABO_CLIENT_ID" --env CONTABO_CLIENT_SECRET="$CONTABO_CLIENT_SECRET" \
  --env CONTABO_API_USER="$CONTABO_API_USER" --env CONTABO_API_PASSWORD="$CONTABO_API_PASSWORD" \
  -- npx -y @kieksme/contabo-mcp

unset CONTABO_CLIENT_ID CONTABO_CLIENT_SECRET CONTABO_API_USER CONTABO_API_PASSWORD
```

The values never enter shell history this way. The shell expands them into the client's arguments, so other local users could see them in the process list for the second or two the command runs. On a shared machine, edit the config file by hand instead.

Where each client stores the values, in plain text. Restrict each file to your own user:

| Client | File | Command |
|---|---|---|
| Claude Code (user scope) | `~/.claude.json` | `chmod 600 ~/.claude.json` |
| Codex | `~/.codex/config.toml` | `chmod 600 ~/.codex/config.toml` |
| Cursor | `~/.cursor/mcp.json` | `chmod 600 ~/.cursor/mcp.json` |

Check the current mode with `ls -l`. `~/.claude.json` is often created world-readable (`644`).

Cursor: merge the `contabo` entry from the template into `~/.cursor/mcp.json` and type the values in by hand. Escape `"` and `\` inside JSON strings. The API password can reach the whole account.

## Catalogs, not servers

`catalogs/` holds MCP *client configs* found inside the linked repos. They name commands (`npx`, hosted servers). They are not the server source.

- `catalogs/ecc-mcp-servers.json` — 34 server entries from [affaan-m/ECC](https://github.com/affaan-m/ECC) `mcp-configs/mcp-servers.json` (GitHub, Supabase, Playwright, Railway, Cloudflare, and others).
- `catalogs/ui-ux-pro-max.mcp.json` — from [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) `stack/.mcp.json`. Points at `@playwright/mcp`, `chrome-devtools-mcp`, and `shadcn mcp`.

None of the other linked repos shipped an MCP server implementation. Playwright’s MCP server is a different project from the [playwright-cli](https://github.com/microsoft/playwright-cli) skill copied under `skills/playwright-cli`.
