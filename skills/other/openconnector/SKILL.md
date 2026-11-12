---
name: openconnector
description: Use the self-hosted OpenConnector MCP server to find a connected app, read an action's contract, and run that action. Use when the user wants GitHub, Gmail, Notion, Slack, or another external service through OpenConnector. Do not use for Dokploy deploys, and do not use the oo CLI skills when this MCP server is connected.
---

# OpenConnector

OpenConnector is the MCP gateway for external services. This skill teaches the call sequence. It does not connect the server. If the tools below are missing from this session, stop and say OpenConnector is not configured. Do not invent endpoints, tokens, or action ids, and do not fall back to `curl` with a credential.

Upstream reference: [runtime API](https://github.com/oomol-lab/open-connector/blob/main/docs/runtime-api.md) and [client onboarding](https://github.com/oomol-lab/open-connector/blob/main/docs/client-onboarding.md). Read the live tool schema this server advertises before filling arguments. Schema details can change.

## Tools

Use only these MCP tools, and only with arguments the live schema accepts:

1. `list_apps` — which providers exist.
2. `list_connections` — which accounts are connected. Results omit stored credentials.
3. `search_actions` — find candidate actions. Use a real query from the user's task.
4. `get_action_guide` — contract for one action id returned by search.
5. `execute_action` — run that action.

If a page includes `nextCursor`, call the same tool again with that cursor and the same filters. Stop when there is no cursor.

## Calling an action

1. Search, then read the guide for the chosen id.
2. Build `input` from the guide. Do not guess fields.
3. Omit `connectionName` to use that provider's default connection.
4. Pass `connectionName` only when `list_connections` listed that name. An unknown name is an error. The server does not silently switch accounts.
5. Show the user the action id and the account name before a write, send, delete, or pay call. Wait for confirmation unless the user already asked for that exact call.

A missing connection is a configuration problem. Do not ask the user to paste an OAuth token into the chat. Point them at the OpenConnector console.

## What this skill is not

- Not Dokploy. Deploying or managing the VPS uses the Dokploy MCP server, if that one is connected.
- Not the vendored `oo-*` skills. Those drive the `oo` CLI. When OpenConnector's MCP tools are available, use those tools for external services instead of `oo`.
