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

## Catalogs, not servers

`catalogs/` holds MCP *client configs* found inside the linked repos. They name commands (`npx`, hosted servers). They are not the server source.

- `catalogs/ecc-mcp-servers.json` — 34 server entries from [affaan-m/ECC](https://github.com/affaan-m/ECC) `mcp-configs/mcp-servers.json` (GitHub, Supabase, Playwright, Railway, Cloudflare, and others).
- `catalogs/ui-ux-pro-max.mcp.json` — from [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) `stack/.mcp.json`. Points at `@playwright/mcp`, `chrome-devtools-mcp`, and `shadcn mcp`.

None of the other linked repos shipped an MCP server implementation. Playwright’s MCP server is a different project from the [playwright-cli](https://github.com/microsoft/playwright-cli) skill copied under `skills/playwright-cli`.
