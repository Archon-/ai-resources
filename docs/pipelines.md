# Pipelines

Two GitHub Actions workflows. Both use the Python in the runner. No extra packages.

## Skill security

File: `.github/workflows/skill-security.yml`.

Runs on every pull request, every push to `main`, and every Monday at 07:00 UTC.

```bash
python3 scripts/scan_skills.py
```

The scan reads `skills/`. It fails the job when it finds:

- A private key, or a token that has the shape of a real GitHub, AWS, Slack, or Anthropic credential. Placeholders such as `ghp_xxx` and `sk-proj-xxxxx` are too short to match.
- In a code file: a `curl` or `wget` piped into a shell, a process substitution that does the same, a reverse shell, `base64 -d` piped into a shell, or `rm -rf /`.
- In a `SKILL.md` or other text file: a URL piped into a shell, unless the host is `cli.oomol.com` or `static.heygen.ai`. Those two installers are already in the vendored catalogs. A line that only warns about `curl | sh`, with no URL, is not a failure.

`python3 scripts/scan_skills.py /path/to/a/fixture` scans that tree instead of this repo.

## Skill updates

File: `.github/workflows/skill-updates.yml`.

Runs every Monday at 08:00 UTC, and when someone starts it by hand from the Actions tab.

```bash
python3 scripts/check_updates.py
```

The check reads `docs/sources.lock.json` and `docs/skill-origins.json`.

- A source with a tag is stale when a newer tag with the same prefix exists. `skill-v4.9.0` is newer than `skill-v4.8.2`. `loop-v0.1.1` is a different line, and `v0.1.24` is older than `v0.180.0`, so neither is an update. A version that is not a git tag falls through to the commit check.
- A source with no tag is stale when the default branch tip is no longer the pinned commit. Moving `main` does not, by itself, flag a source that is still on its newest matching tag.
- A catalog with more than 25 skills is one row (`1707 skills under skills/oomol`). Smaller catalogs list each skill name.
- `dokploy-mcp` is included. It has no skill directory, so the report says that.
- Skills with `"managed": "local"` are skipped.

When something is stale, the workflow opens or updates one issue titled "Skills to update" with the label `skill-updates`. The next clean run closes that issue. The same report is written to the job summary. A network or API failure fails the job. Upstream being ahead does not, because the issue is the flag.

`python3 scripts/check_updates.py --self-test` checks the report builder without calling GitHub.
