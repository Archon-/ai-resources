#!/usr/bin/env python3
"""Place vendored skills into source groups under skills/.

A nested tree looks like the upstream checkout:

    nested/<source>/<skill>/SKILL.md
    nested/<source>/SKILL.md          # the source directory is itself a skill
    nested/<source>/knowledge/        # playbooks, not skills
    nested/<source>/LICENSE

Output:

    <repo>/skills/<source>/<skill>/SKILL.md
    <repo>/skills/other/<skill>/SKILL.md   # a one-skill source, or a source in OTHER_GROUPS
    <repo>/playbooks/<source>/
    <repo>/upstream/<source>/
    <repo>/docs/skill-origins.json

The client install is still one symlink per skill. Grouping is only inside this repo.
Skills marked managed=local in an existing origins file are kept, under skills/other/.
"""

import argparse
import filecmp
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path


# Two skills from one repo, kept beside the one-skill sources.
OTHER_GROUPS = {"modern-web-guidance"}


def group_name(source, counts):
    """Multi-skill catalogs keep their source id. A lone skill goes in other/."""
    source = source or "local"
    if source == "local" or source in OTHER_GROUPS or counts.get(source, 0) < 2:
        return "other"
    return source


def find_skill_dir(skills_dir, name):
    if not skills_dir.is_dir():
        return None
    direct = skills_dir / name
    if (direct / "SKILL.md").is_file():
        return direct
    for group in skills_dir.iterdir():
        if not group.is_dir():
            continue
        candidate = group / name
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


def frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    data = {}
    in_meta = False
    for line in text[4:end].splitlines():
        if line.startswith("metadata:"):
            in_meta = True
            continue
        if in_meta:
            if line and not line.startswith((" ", "\t")):
                in_meta = False
            elif line.strip().startswith("version:"):
                data["metadata.version"] = line.split(":", 1)[1].strip().strip("\"'")
                continue
        if not in_meta and line.startswith("name:"):
            data["name"] = line.split(":", 1)[1].strip().strip("\"'")
        elif not in_meta and line.startswith("version:"):
            data["version"] = line.split(":", 1)[1].strip().strip("\"'")
    return data


def skill_version(meta):
    return meta.get("metadata.version") or meta.get("version") or None


def trees_identical(left, right):
    compared = filecmp.dircmp(str(left), str(right))
    if compared.left_only or compared.right_only or compared.diff_files or compared.funny_files:
        return False
    for name in compared.common_dirs:
        if not trees_identical(left / name, right / name):
            return False
    return True


def rewrite_skill_name(skill_dir, new_name):
    path = skill_dir / "SKILL.md"
    text = path.read_text(errors="replace")
    if not text.startswith("---"):
        return
    end = text.find("\n---", 3)
    if end < 0:
        return
    body = text[4:end].splitlines()
    for index, line in enumerate(body):
        if line.startswith("name:"):
            body[index] = "name: " + new_name
            break
    path.write_text("---\n" + "\n".join(body) + text[end:])


def collect(nested):
    found = []
    for source_dir in sorted(path for path in nested.iterdir() if path.is_dir()):
        source = source_dir.name
        if (source_dir / "SKILL.md").exists():
            found.append((source, source_dir.name, source_dir))
            continue
        for child in sorted(source_dir.iterdir()):
            if child.is_dir() and (child / "SKILL.md").exists():
                found.append((source, child.name, child))
    return found


def drop_identical_duplicates(found):
    """Within one source, keep one copy when two dirs are the same tree."""
    grouped = {}
    for item in found:
        source, dirname, path = item
        meta = frontmatter((path / "SKILL.md").read_text(errors="replace")[:4000])
        key = (source, meta.get("name") or dirname)
        grouped.setdefault(key, []).append((item, meta))

    kept = []
    skipped = []
    for (_source, fm_name), group in grouped.items():
        if len(group) == 1:
            kept.append(group[0][0])
            continue
        remaining = list(group)
        while len(remaining) > 1:
            base_item, _base_meta = remaining[0]
            identical = [remaining[0]]
            rest = []
            for other in remaining[1:]:
                if trees_identical(base_item[2], other[0][2]):
                    identical.append(other)
                else:
                    rest.append(other)
            if len(identical) > 1:
                identical.sort(key=lambda pair: (pair[0][1] != fm_name, len(pair[0][1]), pair[0][1]))
                winner = identical[0][0]
                kept.append(winner)
                for loser, _meta in identical[1:]:
                    skipped.append({
                        "source": loser[0],
                        "dir": loser[1],
                        "kept": winner[1],
                        "reason": "identical copy of the same skill",
                    })
            else:
                kept.append(base_item)
            remaining = rest
        kept.extend(item for item, _meta in remaining)
    return kept, skipped


def assign_names(found):
    """Return (source, dirname, path, dest_name, renamed)."""
    used = set()
    assigned = []
    for source, dirname, path in sorted(found, key=lambda item: (item[1], item[0])):
        dest = dirname
        if dest in used:
            dest = "{}-{}".format(dirname, source)
            suffix = 2
            while dest in used:
                dest = "{}-{}-{}".format(dirname, source, suffix)
                suffix += 1
        used.add(dest)
        assigned.append((source, dirname, path, dest, dest != dirname))
    return assigned


def move_side_files(source_dir, upstream_dir, playbook_dir):
    upstream_dir.mkdir(parents=True, exist_ok=True)
    for child in sorted(source_dir.iterdir()):
        if child.is_file():
            target = upstream_dir / child.name
            if target.exists():
                target.unlink()
            shutil.move(str(child), str(target))
        elif child.is_dir() and not (child / "SKILL.md").exists():
            if child.name == "knowledge":
                if playbook_dir.exists():
                    shutil.rmtree(playbook_dir)
                playbook_dir.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(child), str(playbook_dir))
            else:
                target = upstream_dir / child.name
                if target.exists():
                    shutil.rmtree(target)
                shutil.move(str(child), str(target))


def preserve_local(repo, origins_path):
    if not origins_path.exists():
        return []
    origins = json.loads(origins_path.read_text())
    saved = []
    skills_dir = repo / "skills"
    hold = Path(tempfile.mkdtemp(prefix="ai-resources-local-"))
    for name, meta in origins.get("skills", {}).items():
        if meta.get("managed") != "local":
            continue
        source = find_skill_dir(skills_dir, name)
        if source is not None:
            shutil.copytree(source, hold / name)
            saved.append((name, meta, hold / name))
    return saved


def assemble(nested, repo):
    nested = nested.resolve()
    repo = repo.resolve()
    origins_path = repo / "docs" / "skill-origins.json"
    aside = None
    if nested == (repo / "skills").resolve():
        aside = repo / ".skills-nested-aside"
        if aside.exists():
            shutil.rmtree(aside)
        os.rename(str(nested), str(aside))
        nested = aside

    local_skills = preserve_local(repo, origins_path)
    found, skipped = drop_identical_duplicates(collect(nested))
    assigned = assign_names(found)
    counts = Counter(source for source, _dirname, _path, _dest, _renamed in assigned)

    tree = Path(tempfile.mkdtemp(prefix="ai-resources-grouped-"))
    origins = {
        "version": 1,
        "skills": {},
        "skipped_duplicates": skipped,
        "playbooks": {},
    }

    for source, dirname, path, dest, renamed in assigned:
        group = group_name(source, counts)
        target = tree / group / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(target))
        meta = frontmatter((target / "SKILL.md").read_text(errors="replace")[:4000])
        if renamed:
            rewrite_skill_name(target, dest)
            meta["name"] = dest
        origins["skills"][dest] = {
            "source": source,
            "group": group,
            "upstream_dir": dirname,
            "managed": "upstream",
            "version": skill_version(meta),
            "renamed_from": dirname if renamed else None,
        }

    for source_dir in sorted(path for path in nested.iterdir() if path.is_dir()):
        move_side_files(
            source_dir,
            repo / "upstream" / source_dir.name,
            repo / "playbooks" / source_dir.name,
        )
        if (repo / "playbooks" / source_dir.name).exists():
            origins["playbooks"][source_dir.name] = "playbooks/{}".format(source_dir.name)
        try:
            source_dir.rmdir()
        except OSError:
            pass

    for name, meta, held in local_skills:
        target = tree / "other" / name
        if target.exists():
            raise SystemExit("local skill {} clashes with an upstream skill".format(name))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(held), str(target))
        kept = dict(meta)
        kept["group"] = "other"
        origins["skills"][name] = kept
    if local_skills:
        shutil.rmtree(local_skills[0][2].parent, ignore_errors=True)

    skills_dir = repo / "skills"
    if skills_dir.exists():
        shutil.rmtree(skills_dir)
    shutil.move(str(tree), str(skills_dir))

    if aside is not None and aside.exists():
        shutil.rmtree(aside, ignore_errors=True)
    if nested.exists():
        shutil.rmtree(nested, ignore_errors=True)

    origins_path.parent.mkdir(parents=True, exist_ok=True)
    origins_path.write_text(json.dumps(origins, indent=2) + "\n")
    print("grouped skills", len(origins["skills"]))
    print("renamed", sum(1 for item in origins["skills"].values() if item.get("renamed_from")))
    print("skipped duplicates", len(skipped))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nested", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args()
    assemble(args.nested, args.repo)


if __name__ == "__main__":
    main()
