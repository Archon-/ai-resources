# AI resources hub

This repository is the canonical copy of shared agent skills.

- Edit skills in `skills/<group>/<name>/`. One-skill sources live in `skills/other/`. Link one with `scripts/install.sh --skill <name>`. The chosen set is `enabled-skills.txt`. Do not symlink `skills/` or a whole group into a client.
- `docs/skill-origins.json` maps each folder to its upstream source. Local skills need `"managed": "local"` or the next fetch deletes them.
- Do not commit tokens, `.env` files, or machine-specific MCP configs. Templates live in `mcp/templates/` and use placeholders.
- OpenConnector is an MCP server the user runs on Dokploy. `skills/other/openconnector` only documents how to call it. The `oo-*` skills are a different interface.
- Do not run `scripts/install.sh` against the real home directory while experimenting. Set `AI_RESOURCES_HOME` to a temp directory.
- `scripts/scan_skills.py` is the security check. `scripts/check_updates.py` compares lock pins with upstream. See `docs/pipelines.md`.
