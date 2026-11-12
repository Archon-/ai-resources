#!/usr/bin/env python3
"""Regenerate docs/versions.md and docs/skills-index.md."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "docs" / "sources.lock.json"
ORIGINS = ROOT / "docs" / "skill-origins.json"
ORDER = [
    "taste-skill",
    "impeccable",
    "playwright-cli",
    "obscura",
    "openmontage",
    "ecc",
    "karpathy-guidelines",
    "ponytail",
    "agent-skills",
    "ui-ux-pro-max",
    "anthropics",
    "humanizer",
    "i-have-adhd",
    "marketingskills",
    "oomol",
    "modern-web-guidance",
    "local",
]


def main():
    lock = json.loads(LOCK.read_text())
    origins = json.loads(ORIGINS.read_text())
    by_id = {source["id"]: source for source in lock["sources"]}

    versions = [
        "# Versions",
        "",
        "Generated from `docs/sources.lock.json`. Fetched {}.".format(lock["fetched_at"]),
        "Skills live in `skills/<group>/<name>/`. A source with one skill is under `skills/other/`. The per-skill map is `docs/skill-origins.json`.",
        "Commit is the exact tree that was copied. Tag is the latest release known at fetch time; `—` means the repo had no release tag.",
        "",
        "| Source | Version | Commit | License |",
        "| --- | --- | --- | --- |",
    ]
    for source in lock["sources"]:
        tag = source["tag_or_version"] or "—"
        versions.append(
            "| [{id}]({url}) | `{tag}` | `{commit}` | {license} |".format(
                id=source["id"],
                url=source["url"],
                tag=tag,
                commit=source["commit"],
                license=source["license"].replace("|", "\\|"),
            )
        )
    versions.append("")
    (ROOT / "docs" / "versions.md").write_text("\n".join(versions))

    grouped = {key: [] for key in ORDER}
    for name, meta in origins.get("skills", {}).items():
        source = meta.get("source") or "local"
        if source not in grouped:
            grouped.setdefault(source, [])
        version = meta.get("version") or ""
        group = meta.get("group") or "other"
        rel = "skills/{}/{}/SKILL.md".format(group, name)
        grouped.setdefault(source, []).append((name, version, rel, meta))

    lines = [
        "# Skills index",
        "",
        "Generated from `skills/<group>/<name>/`. A one-skill source is in `skills/other/`. Fetched {}.".format(lock["fetched_at"]),
        "{} skills.".format(len(origins.get("skills", {}))),
        "Bundle version and commit: [versions.md](versions.md). Folder origin: [skill-origins.json](skill-origins.json).",
        "",
    ]
    seen = []
    for source_id in ORDER + [key for key in grouped if key not in ORDER]:
        if source_id in seen:
            continue
        seen.append(source_id)
        rows = sorted(grouped.get(source_id, []))
        if source_id == "dokploy-mcp":
            continue
        source = by_id.get(source_id)
        lines.append("## {}".format(source_id))
        lines.append("")
        if source:
            tag = source["tag_or_version"] or "no release tag"
            lines.append("[{url}]({url}) · `{tag}` · `{commit}` · {n} skills".format(
                url=source["url"],
                tag=tag,
                commit=source["commit"][:12],
                n=len(rows),
            ))
        else:
            lines.append("Local skills, not vendored. {} skills".format(len(rows)))
        lines.append("")
        for name, version, rel, _meta in rows:
            if version:
                lines.append("- `{name}` `{version}` — `{rel}`".format(name=name, version=version, rel=rel))
            else:
                lines.append("- `{name}` — `{rel}`".format(name=name, rel=rel))
        if source_id == "openmontage":
            notes = sorted(
                path.relative_to(ROOT).as_posix()
                for path in (ROOT / "playbooks" / "openmontage").rglob("*.md")
            ) if (ROOT / "playbooks" / "openmontage").exists() else []
            lines.append("")
            lines.append("Playbooks (not skills): {}".format(len(notes)))
            lines.append("")
            for rel in notes:
                lines.append("- `{}`".format(rel))
        lines.append("")

    skipped = origins.get("skipped_duplicates") or []
    if skipped:
        lines.append("## Skipped duplicates")
        lines.append("")
        for item in skipped:
            lines.append("- `{source}/{dir}` dropped; kept `{kept}` ({reason})".format(**item))
        lines.append("")

    (ROOT / "docs" / "skills-index.md").write_text("\n".join(lines))
    print("skills", len(origins.get("skills", {})))


if __name__ == "__main__":
    main()
