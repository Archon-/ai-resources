#!/usr/bin/env python3
"""Link skills from this repo into local AI clients.

Per-skill symlinks. Never replaces a real file or someone else's symlink.
Does not edit MCP configs, CLAUDE.md, or AGENTS.md.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

CLIENTS = {
    "claude": Path(".claude") / "skills",
    "codex": Path(".agents") / "skills",
    "cursor": Path(".cursor") / "skills",
}
DEFAULT_CLIENTS = ("claude", "codex")


def repo_root(explicit):
    if explicit:
        return Path(explicit).resolve()
    env = os.environ.get("AI_RESOURCES_REPO")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[1]


def home_dir():
    override = os.environ.get("AI_RESOURCES_HOME")
    if override:
        return Path(override).resolve()
    return Path.home()


def state_path():
    override = os.environ.get("AI_RESOURCES_STATE_DIR")
    if override:
        return Path(override) / "manifest.json"
    return home_dir() / ".local" / "share" / "ai-resources" / "manifest.json"


def load_origins(repo):
    path = repo / "docs" / "skill-origins.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("skills", {})


ENABLED_FILE = "enabled-skills.txt"


def iter_skill_dirs(skills_root):
    """Yield each skill directory.

    Catalog layout is skills/<group>/<name>/SKILL.md. A skill whose SKILL.md
    sits directly under skills/ is still accepted.
    """
    if not skills_root.is_dir():
        return
    for group in sorted(skills_root.iterdir()):
        if not group.is_dir() or group.is_symlink():
            continue
        if (group / "SKILL.md").is_file():
            yield group
            continue
        for child in sorted(group.iterdir()):
            if child.is_dir() and not child.is_symlink() and (child / "SKILL.md").is_file():
                yield child


def skill_dirs(repo, skip_sources=None, only_names=None):
    skip_sources = skip_sources or set()
    origins = load_origins(repo)
    found = []
    for child in iter_skill_dirs(repo / "skills"):
        if only_names is not None and child.name not in only_names:
            continue
        source = origins.get(child.name, {}).get("source")
        if source and source in skip_sources:
            continue
        found.append(child)
    return found


def enabled_path(repo):
    return repo / ENABLED_FILE


def read_enabled(repo):
    path = enabled_path(repo)
    if not path.exists():
        return []
    names = []
    for line in path.read_text().splitlines():
        name = line.split("#", 1)[0].strip()
        if name:
            names.append(name)
    return names


def write_enabled(repo, names):
    path = enabled_path(repo)
    header = [
        "# Skills this repo links into Claude Code and Codex.",
        "# One directory name per line. Cursor reads both of those directories.",
        "# Add one skill: ./scripts/install.sh --skill <name>",
        "# Lean bulk:    ./scripts/install.sh --skip-source oomol --skip-source ecc",
        "",
    ]
    if path.exists():
        kept = []
        for line in path.read_text().splitlines():
            if line.startswith("#") or not line.strip():
                kept.append(line)
            else:
                break
        if kept:
            header = kept
            if header[-1] != "":
                header.append("")
    body = sorted(set(names))
    path.write_text("\n".join(header + body) + "\n")


def known_names(repo):
    return {skill.name for skill in skill_dirs(repo)}


def require_known(repo, names):
    missing = [name for name in names if name not in known_names(repo)]
    if missing:
        raise SystemExit("unknown skill: {}".format(", ".join(missing)))


def selection(repo, args):
    """Return (skill dirs, replace_enabled_file).

    --skill adds those skills to the saved list.
    --skip-source replaces the saved list with every other skill.
    Neither flag uses the saved list as-is.
    """
    chosen = list(args.skill or [])
    skipped = set(args.skip_source or [])
    if chosen and skipped:
        raise SystemExit("use either --skill or --skip-source, not both")
    if chosen:
        require_known(repo, chosen)
        names = list(dict.fromkeys(read_enabled(repo) + chosen))
        return skill_dirs(repo, only_names=set(names)), True
    if skipped:
        return skill_dirs(repo, skipped), True
    names = read_enabled(repo)
    missing = [name for name in names if name not in known_names(repo)]
    for name in missing:
        print("missing skill in {}: {}".format(ENABLED_FILE, name))
    return skill_dirs(repo, only_names=set(names) - set(missing)), False


def readlink(path):
    return Path(os.readlink(path))


def is_ours(path, repo):
    if not path.is_symlink():
        return False
    raw = readlink(path)
    skills = (repo / "skills").resolve()
    target = raw if raw.is_absolute() else (path.parent / raw)
    text = str(target)
    prefix = str(skills)
    if text == prefix or text.startswith(prefix + os.sep):
        return True
    try:
        target.resolve().relative_to(skills)
        return True
    except (ValueError, OSError):
        return False


def parse_clients(value):
    if not value or value == "default":
        return list(DEFAULT_CLIENTS)
    names = [part.strip() for part in value.split(",") if part.strip()]
    unknown = [name for name in names if name not in CLIENTS]
    if unknown:
        raise SystemExit("unknown client: {}".format(", ".join(unknown)))
    return names


def client_root(client):
    return home_dir() / CLIENTS[client]


def plan_links(clients, skills):
    """Return actions: link, relink, ok, conflict."""
    actions = []
    for client in clients:
        root = client_root(client)
        for skill in skills:
            dest = root / skill.name
            target = skill.resolve()
            if dest.is_symlink():
                current = readlink(dest)
                current_abs = current if current.is_absolute() else (dest.parent / current)
                try:
                    same = current_abs.resolve() == target
                except OSError:
                    same = False
                if same:
                    actions.append(("ok", client, skill.name, dest, target))
                elif is_ours(dest, repo):
                    actions.append(("relink", client, skill.name, dest, target))
                else:
                    actions.append(("conflict", client, skill.name, dest, target))
            elif dest.exists():
                actions.append(("conflict", client, skill.name, dest, target))
            else:
                actions.append(("link", client, skill.name, dest, target))
    return actions


def plan_removals(repo, clients, skills):
    desired = {skill.name for skill in skills}
    removals = []
    for client in clients:
        root = client_root(client)
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if entry.name in desired:
                continue
            if is_ours(entry, repo):
                removals.append((client, entry.name, entry))
    return removals


def apply_links(actions, dry_run):
    conflicts = 0
    for kind, client, name, dest, target in actions:
        if kind == "ok":
            print("ok      {} {}".format(client, name))
            continue
        if kind == "conflict":
            conflicts += 1
            print("conflict {} {} — left in place: {}".format(client, name, dest))
            continue
        print("{} {} {}".format(kind, client, name))
        if dry_run:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink() or dest.exists():
            dest.unlink()
        dest.symlink_to(target)
    return conflicts


def apply_removals(removals, dry_run):
    for client, name, path in removals:
        print("unlink  {} {}".format(client, name))
        if not dry_run:
            path.unlink()


def write_manifest(repo, clients):
    links = []
    for client in clients:
        root = client_root(client)
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if is_ours(entry, repo):
                links.append({
                    "client": client,
                    "name": entry.name,
                    "path": str(entry),
                })
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "repo": str(repo),
        "links": links,
    }, indent=2) + "\n")


def command_install(args):
    clients = parse_clients(args.clients)
    skills, save = selection(args.repo, args)
    if not skills and not (args.skill or args.skip_source):
        print("no skills selected. Add one with --skill <name>, or bulk-link with --skip-source.")
        print("saved list: {}".format(enabled_path(args.repo)))
        return 0
    actions = plan_links(clients, skills)
    conflicts = apply_links(actions, args.dry_run)
    # A bulk skip replaces the set, so links for the skipped sources come back off.
    removals = plan_removals(args.repo, clients, skills) if args.skip_source else []
    apply_removals(removals, args.dry_run)
    if not args.dry_run and save:
        write_enabled(args.repo, [skill.name for skill in skills])
        write_manifest(args.repo, list(CLIENTS))
    elif not args.dry_run:
        write_manifest(args.repo, list(CLIENTS))
    return 1 if conflicts else 0


def command_sync(args):
    clients = parse_clients(args.clients)
    if not args.skill and not args.skip_source and not read_enabled(args.repo):
        print("enabled-skills.txt has no skills. Nothing to sync.")
        print("Add one with --skill, or bulk-link with --skip-source.")
        return 0
    skills, save = selection(args.repo, args)
    actions = plan_links(clients, skills)
    removals = plan_removals(args.repo, clients, skills)
    conflicts = apply_links(actions, args.dry_run)
    apply_removals(removals, args.dry_run)
    if not args.dry_run:
        if save or args.skip_source or args.skill:
            write_enabled(args.repo, [skill.name for skill in skills])
        elif read_enabled(args.repo):
            # Drop names whose folders disappeared.
            write_enabled(args.repo, [skill.name for skill in skills])
        write_manifest(args.repo, list(CLIENTS))
    return 1 if conflicts else 0


def command_uninstall(args):
    """Remove symlinks that point into this repo. Scan every known client."""
    chosen = set(args.skill or [])
    if chosen:
        require_known(args.repo, list(chosen))
    removed = 0
    for client in CLIENTS:
        root = client_root(client)
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if chosen and entry.name not in chosen:
                continue
            if not is_ours(entry, args.repo):
                continue
            print("unlink  {} {}".format(client, entry.name))
            if not args.dry_run:
                entry.unlink()
            removed += 1
    if not args.dry_run:
        if chosen:
            write_enabled(args.repo, [name for name in read_enabled(args.repo) if name not in chosen])
        else:
            write_enabled(args.repo, [])
            path = state_path()
            if path.exists():
                path.unlink()
        write_manifest(args.repo, list(CLIENTS))
    print("removed {}".format(removed))
    return 0


def command_doctor(args):
    problems = 0
    home = home_dir()
    print("repo  {}".format(args.repo))
    print("home  {}".format(home))
    skills = list(iter_skill_dirs(args.repo / "skills"))
    enabled = read_enabled(args.repo)
    print("skills in repo  {}".format(len(skills)))
    print("enabled         {}".format(len(enabled)))
    for binary in ("claude", "codex", "cursor"):
        found = shutil.which(binary) is not None
        print("binary {}  {}".format(binary, "found" if found else "not on PATH"))

    linked = {client: [] for client in CLIENTS}
    for client in CLIENTS:
        root = client_root(client)
        print("dir {}  {}".format(client, root))
        if not root.exists():
            print("  missing")
            continue
        if not root.is_dir():
            print("  not a directory")
            problems += 1
            continue
        for entry in sorted(root.iterdir()):
            if not is_ours(entry, args.repo):
                continue
            linked[client].append(entry.name)
            if not entry.exists():
                print("  broken {}".format(entry.name))
                problems += 1
        print("  linked {}".format(len(linked[client])))

    ours = set(enabled)
    for client in DEFAULT_CLIENTS:
        root = client_root(client)
        if not root.is_dir():
            continue
        for name in sorted(ours):
            dest = root / name
            if dest.exists() and not dest.is_symlink():
                print("conflict {} {} is a real file".format(client, name))
                problems += 1
            elif dest.is_symlink() and not is_ours(dest, args.repo):
                print("conflict {} {} points elsewhere".format(client, name))
                problems += 1

    if linked["claude"] and linked["codex"]:
        print("note  Cursor reads both {} and {}, so each skill linked to claude and codex can show up twice in Cursor. Claude Code and Codex each read only their own directory.".format(
            home / CLIENTS["claude"], home / CLIENTS["codex"]
        ))
    if linked["cursor"] and (linked["claude"] or linked["codex"]):
        print("note  ~/.cursor/skills is also populated. Cursor already reads the Claude and Codex skill directories, so this is a third copy.")

    state = state_path()
    print("manifest  {}".format(state if state.exists() else "none"))
    if problems:
        print("problems  {}".format(problems))
        return 1
    print("ok")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(command):
        command.add_argument("--clients", default="default", help="comma list: claude,codex,cursor")
        command.add_argument("--skill", action="append", default=[], help="link this skill too; repeat for more than one")
        command.add_argument("--skip-source", action="append", default=[], help="bulk-link every skill except this source; repeatable")
        command.add_argument("--dry-run", action="store_true")

    install = sub.add_parser("install", help="link selected skills, never overwrite unrelated files")
    add_common(install)
    sync = sub.add_parser("sync", help="make client links match enabled-skills.txt")
    add_common(sync)
    uninstall = sub.add_parser("uninstall", help="remove symlinks that point into this repo")
    uninstall.add_argument("--skill", action="append", default=[], help="remove only this skill; repeatable")
    uninstall.add_argument("--dry-run", action="store_true")
    sub.add_parser("doctor", help="report broken links and conflicts")
    return parser


def main(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.repo = repo_root(args.repo)
    if not (args.repo / "skills").is_dir():
        print("no skills directory at {}".format(args.repo / "skills"), file=sys.stderr)
        return 1
    if args.command == "install":
        return command_install(args)
    if args.command == "sync":
        return command_sync(args)
    if args.command == "uninstall":
        return command_uninstall(args)
    if args.command == "doctor":
        return command_doctor(args)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
