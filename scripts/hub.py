#!/usr/bin/env python3
"""Link skills from this repo into local AI harnesses.

Per-skill symlinks. Never replaces a real file or someone else's symlink.
Does not edit MCP configs, CLAUDE.md, or AGENTS.md.

Global paths follow the public agent table in
https://github.com/vercel-labs/skills/blob/main/docs/agents.md
plus the Cursor and Codex docs this repo already checked.
Codex skills go to ~/.agents/skills. ~/.codex/skills is the old path and is not used.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# id, label, skills path, config markers, binaries.
# Markers are the app's own config directory. A directory that contains only
# "skills" does not count: that is the directory this tool creates.
HARNESSES = (
    ("claude-code", "Claude Code", ".claude/skills", (".claude",), ("claude",)),
    ("codex", "Codex", ".agents/skills", (".codex",), ("codex",)),
    ("cursor", "Cursor", ".cursor/skills", (".cursor",), ("cursor",)),
    ("github-copilot", "GitHub Copilot", ".copilot/skills", (".copilot",), ()),
    ("windsurf", "Windsurf", ".codeium/windsurf/skills", (".codeium/windsurf", ".windsurf"), ("windsurf",)),
    ("cline", "Cline", ".agents/skills", (".cline",), ("cline",)),
    ("gemini-cli", "Gemini CLI", ".gemini/skills", (".gemini",), ("gemini",)),
    ("opencode", "OpenCode", ".config/opencode/skills", (".config/opencode", ".local/share/opencode"), ("opencode",)),
    ("continue", "Continue", ".continue/skills", (".continue",), ()),
    ("amp", "Amp", ".config/agents/skills", (".config/amp", ".amp"), ("amp",)),
    ("roo", "Roo Code", ".roo/skills", (".roo",), ()),
    ("kilo", "Kilo Code", ".kilo/skills", (".kilo", ".kilocode"), ("kilo",)),
    ("augment", "Augment", ".augment/skills", (".augment",), ()),
    ("zed", "Zed", ".agents/skills", (".config/zed",), ("zed",)),
)

ALIASES = {
    "claude": "claude-code",
    "copilot": "github-copilot",
    "gemini": "gemini-cli",
}

# Cursor's global directory plus the compatibility directories it also scans.
CURSOR_READS = (
    Path(".claude") / "skills",
    Path(".agents") / "skills",
    Path(".cursor") / "skills",
)

ENABLED_FILE = "enabled-skills.txt"

_COLOR = False


# Names left behind by a skill installer. They are not the app itself.
DROP_NAMES = frozenset({"skills", "rules", "global_skills"})


class Harness(object):
    def __init__(self, harness_id, label, skills, markers, binaries):
        self.id = harness_id
        self.label = label
        self.skills = Path(skills)
        self.markers = tuple(Path(marker) for marker in markers)
        self.binaries = tuple(binaries)
        self.ignore = set(DROP_NAMES)

    @property
    def attr(self):
        return "harness_" + self.id.replace("-", "_")


HARNESS_LIST = tuple(Harness(*row) for row in HARNESSES)
HARNESS_BY_ID = {harness.id: harness for harness in HARNESS_LIST}
# Antigravity keeps its own tree under ~/.gemini. That must not look like Gemini CLI.
HARNESS_BY_ID["gemini-cli"].ignore.add("antigravity")


def configure_color():
    global _COLOR
    if os.environ.get("NO_COLOR") is not None:
        _COLOR = False
        return
    mode = os.environ.get("AI_RESOURCES_COLOR", "").strip().lower()
    if mode in ("always", "1", "yes"):
        _COLOR = True
        return
    if mode in ("never", "0", "no"):
        _COLOR = False
        return
    _COLOR = sys.stdout.isatty()


def paint(code, text):
    if not _COLOR or not code:
        return text
    return "\033[{}m{}\033[0m".format(code, text)


def kind_color(kind):
    return {
        "link": "32",
        "ok": "2",
        "relink": "33",
        "unlink": "33",
        "conflict": "31",
    }.get(kind, "")


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
        "# Skills this repo links into harnesses it finds on this machine.",
        "# One directory name per line.",
        "# Add one skill: ./scripts/install.sh --skill <name>",
        "# One harness:  ./scripts/install.sh --skill <name> --cursor",
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
        print(paint("33", "missing skill in {}: {}".format(ENABLED_FILE, name)))
    return skill_dirs(repo, only_names=set(names) - set(missing)), False


def readlink(path):
    return Path(os.readlink(path))


def is_ours(path, repo):
    """True when path is a symlink whose resolved target is within repo/skills."""
    if not path.is_symlink():
        return False
    raw = readlink(path)
    skills = (repo / "skills").resolve()
    target = raw if raw.is_absolute() else (path.parent / raw)
    try:
        resolved = target.resolve(strict=False)
        resolved.relative_to(skills)
    except (ValueError, OSError, RuntimeError):
        return False
    return True


def resolve_harness_name(name):
    key = ALIASES.get(name, name)
    if key not in HARNESS_BY_ID:
        known = ", ".join(harness.id for harness in HARNESS_LIST)
        raise SystemExit("unknown harness: {} (known: {})".format(name, known))
    return key


def explicit_harnesses(args):
    chosen = []
    raw = getattr(args, "clients", None)
    if raw and raw != "default":
        for part in raw.split(","):
            part = part.strip()
            if part:
                chosen.append(resolve_harness_name(part))
    for harness in HARNESS_LIST:
        if getattr(args, harness.attr, False):
            chosen.append(harness.id)
    seen = set()
    ordered = []
    for name in chosen:
        if name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    if ordered:
        wanted = set(ordered)
        return [harness.id for harness in HARNESS_LIST if harness.id in wanted]
    return []


def marker_in_use(path, ignore):
    """True when this config directory belongs to an installed app.

    A directory that only holds skill drop folders is not the app.
    """
    if not path.exists():
        return False
    if not path.is_dir():
        return True
    try:
        names = {child.name for child in path.iterdir()} - set(ignore)
    except OSError:
        return False
    return bool(names)


def harness_present(harness):
    home = home_dir()
    for marker in harness.markers:
        if marker_in_use(home / marker, harness.ignore):
            return True
    for binary in harness.binaries:
        if shutil.which(binary):
            return True
    return False


def presence_reason(harness):
    home = home_dir()
    reasons = []
    for marker in harness.markers:
        if marker_in_use(home / marker, harness.ignore):
            reasons.append("~/{}".format(marker))
    for binary in harness.binaries:
        if shutil.which(binary):
            reasons.append("binary {}".format(binary))
    return reasons


def target_harnesses(args):
    chosen = explicit_harnesses(args)
    if chosen:
        return chosen
    return [harness.id for harness in HARNESS_LIST if harness_present(harness)]


def client_root(harness_id):
    return home_dir() / HARNESS_BY_ID[harness_id].skills


def group_by_root(ids):
    """Yield (root, [harness ids]) in harness-list order, one group per directory."""
    groups = []
    index = {}
    for harness_id in ids:
        root = client_root(harness_id)
        key = str(root)
        if key not in index:
            index[key] = len(groups)
            groups.append((root, []))
        groups[index[key]][1].append(harness_id)
    return groups


def print_heading(text):
    print(paint("1", text))


def print_targets(ids):
    print_heading("targets")
    for root, hids in group_by_root(ids):
        primary = hids[0]
        print("  {}  {}".format(paint("1", "{:<16}".format(primary)), paint("2", str(root))))
        extra = hids[1:]
        if extra:
            print(paint("2", "    also read by {}".format(", ".join(extra))))
    print()


def print_no_harness():
    print(paint("33", "no harness detected on this machine."))
    print("Pass --claude-code, --codex, --cursor, or another harness flag.")


def print_action(kind, harness_id, name, extra=""):
    kind_text = paint(kind_color(kind), "{:<8}".format(kind))
    id_text = paint("1", "{:<16}".format(harness_id))
    line = "  {}  {}  {}".format(kind_text, id_text, name)
    if extra:
        line += "  " + paint("2", extra)
    print(line)


def plan_links(ids, skills, repo):
    """Return actions: link, relink, ok, conflict. One action per skills directory."""
    actions = []
    for root, hids in group_by_root(ids):
        harness_id = hids[0]
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
                    actions.append(("ok", harness_id, skill.name, dest, target))
                elif is_ours(dest, repo):
                    actions.append(("relink", harness_id, skill.name, dest, target))
                else:
                    actions.append(("conflict", harness_id, skill.name, dest, target))
            elif dest.exists():
                actions.append(("conflict", harness_id, skill.name, dest, target))
            else:
                actions.append(("link", harness_id, skill.name, dest, target))
    return actions


def plan_removals(repo, ids, skills):
    desired = {skill.name for skill in skills}
    removals = []
    for root, hids in group_by_root(ids):
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if entry.name in desired:
                continue
            if is_ours(entry, repo):
                removals.append((hids[0], entry.name, entry))
    return removals


def apply_links(actions, dry_run):
    conflicts = set()
    applied = set()
    for kind, harness_id, name, dest, target in actions:
        extra = ""
        if kind == "conflict":
            conflicts.add(str(dest))
            extra = "left in place: {}".format(dest)
        print_action(kind, harness_id, name, extra)
        if dry_run or kind in ("ok", "conflict"):
            continue
        key = str(dest)
        if key in applied:
            continue
        applied.add(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink() or dest.exists():
            dest.unlink()
        dest.symlink_to(target)
    return len(conflicts)


def apply_removals(removals, dry_run):
    done = set()
    for harness_id, name, path in removals:
        print_action("unlink", harness_id, name)
        key = str(path)
        if dry_run or key in done:
            continue
        done.add(key)
        path.unlink()


def finish(conflicts):
    print()
    if conflicts:
        noun = "conflict" if conflicts == 1 else "conflicts"
        print(paint("31", "  {} {}. Existing files were left in place.".format(conflicts, noun)))
        return 1
    print(paint("32", "  ok"))
    return 0


def write_manifest(repo):
    links = []
    seen = set()
    for harness in HARNESS_LIST:
        root = client_root(harness.id)
        key = str(root)
        if key in seen or not root.is_dir():
            continue
        seen.add(key)
        for entry in sorted(root.iterdir()):
            if is_ours(entry, repo):
                links.append({
                    "client": harness.id,
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
    skills, save = selection(args.repo, args)
    if not skills and not (args.skill or args.skip_source):
        print("no skills selected. Add one with --skill <name>, or bulk-link with --skip-source.")
        print("saved list: {}".format(enabled_path(args.repo)))
        return 0
    ids = target_harnesses(args)
    if not ids:
        print_no_harness()
        return 1
    print_targets(ids)
    actions = plan_links(ids, skills, args.repo)
    conflicts = apply_links(actions, args.dry_run)
    removals = plan_removals(args.repo, ids, skills) if args.skip_source else []
    apply_removals(removals, args.dry_run)
    if not args.dry_run and save:
        write_enabled(args.repo, [skill.name for skill in skills])
        write_manifest(args.repo)
    elif not args.dry_run:
        write_manifest(args.repo)
    return finish(conflicts)


def command_sync(args):
    if not args.skill and not args.skip_source and not read_enabled(args.repo):
        print("enabled-skills.txt has no skills. Nothing to sync.")
        print("Add one with --skill, or bulk-link with --skip-source.")
        return 0
    skills, save = selection(args.repo, args)
    ids = target_harnesses(args)
    if not ids:
        print_no_harness()
        return 1
    print_targets(ids)
    actions = plan_links(ids, skills, args.repo)
    removals = plan_removals(args.repo, ids, skills)
    conflicts = apply_links(actions, args.dry_run)
    apply_removals(removals, args.dry_run)
    if not args.dry_run:
        if save or args.skip_source or args.skill or read_enabled(args.repo):
            write_enabled(args.repo, [skill.name for skill in skills])
        write_manifest(args.repo)
    return finish(conflicts)


def command_uninstall(args):
    """Remove symlinks that point into this repo."""
    chosen = set(args.skill or [])
    if chosen:
        require_known(args.repo, list(chosen))
    explicit = explicit_harnesses(args)
    ids = explicit if explicit else [harness.id for harness in HARNESS_LIST]
    if explicit:
        print_targets(ids)
    removed = set()
    for root, hids in group_by_root(ids):
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if chosen and entry.name not in chosen:
                continue
            if not is_ours(entry, args.repo):
                continue
            print_action("unlink", hids[0], entry.name)
            key = str(entry)
            if args.dry_run or key in removed:
                removed.add(key)
                continue
            entry.unlink()
            removed.add(key)
    if not args.dry_run:
        if chosen:
            write_enabled(args.repo, [name for name in read_enabled(args.repo) if name not in chosen])
        elif not explicit:
            write_enabled(args.repo, [])
            path = state_path()
            if path.exists():
                path.unlink()
        write_manifest(args.repo)
    print()
    print("  removed {}".format(len(removed)))
    return 0


def wrap_ids(ids, width=68):
    lines = []
    current = ""
    for harness_id in ids:
        piece = harness_id if not current else ", " + harness_id
        if current and len(current) + len(piece) > width:
            lines.append(current)
            current = harness_id
        else:
            current += piece
    if current:
        lines.append(current)
    return lines or [""]


def command_doctor(args):
    problems = 0
    home = home_dir()
    repo = args.repo
    print_heading("repo")
    print("  {}".format(repo))
    print()
    print_heading("home")
    print("  {}".format(home))
    print()
    skills = list(iter_skill_dirs(repo / "skills"))
    enabled = read_enabled(repo)
    print_heading("catalog")
    print("  {} skills".format(len(skills)))
    print("  {} enabled".format(len(enabled)))

    print()
    print_heading("harnesses")
    absent = []
    for harness in HARNESS_LIST:
        if not harness_present(harness):
            absent.append(harness.id)
            continue
        print("  {}".format(paint("32", harness.id)))
        print("    {}".format(paint("2", "~/" + harness.skills.as_posix())))
        reasons = presence_reason(harness)
        if reasons:
            print("    {}".format(paint("2", ", ".join(reasons))))
        print()
    if absent:
        print("  {}".format(paint("2", "not installed")))
        for line in wrap_ids(absent):
            print("    {}".format(paint("2", line)))

    print()
    print_heading("links")
    ours = set(enabled)
    seen_roots = set()
    any_links = False
    for root, hids in group_by_root([harness.id for harness in HARNESS_LIST]):
        key = str(root)
        if key in seen_roots:
            continue
        seen_roots.add(key)
        present = [harness_id for harness_id in hids if harness_present(HARNESS_BY_ID[harness_id])]
        exists = root.exists()
        owned = []
        if root.is_dir():
            for entry in sorted(root.iterdir()):
                if is_ours(entry, repo):
                    owned.append(entry)
        if not present and not owned:
            continue
        any_links = True
        label = ", ".join(present or hids[:1])
        print("  {}".format(paint("1", label)))
        if not exists:
            print("    {}".format(paint("2", "directory not created yet")))
            print()
            continue
        if not root.is_dir():
            print("    {}".format(paint("31", "not a directory")))
            problems += 1
            print()
            continue
        print("    {} linked".format(len(owned)))
        for entry in owned:
            if not entry.exists():
                print("    {}".format(paint("31", "broken  {}".format(entry.name))))
                problems += 1
        if present:
            for name in sorted(ours):
                dest = root / name
                if dest.exists() and not dest.is_symlink():
                    print("    {}".format(paint("31", "conflict  {} is a real file".format(name))))
                    problems += 1
                elif dest.is_symlink() and not is_ours(dest, repo):
                    print("    {}".format(paint("31", "conflict  {} points elsewhere".format(name))))
                    problems += 1
        print()
    if not any_links:
        print("  {}".format(paint("2", "none")))
        print()

    populated = []
    for rel in CURSOR_READS:
        root = home / rel
        if root.is_dir() and any(is_ours(entry, repo) for entry in root.iterdir()):
            populated.append("~/" + rel.as_posix())
    if len(populated) >= 2:
        print_heading("notes")
        print(paint("33", "  Cursor reads ~/.claude/skills, ~/.agents/skills, and ~/.cursor/skills."))
        print(paint("33", "  Hub links are in more than one of those, so Cursor can list a skill more than once."))
        print()

    state = state_path()
    print_heading("manifest")
    print("  {}".format(state if state.exists() else "none"))
    print()
    if problems:
        noun = "problem" if problems == 1 else "problems"
        print(paint("31", "  {} {}".format(problems, noun)))
        return 1
    print(paint("32", "  ok"))
    return 0


def add_target_flags(command):
    command.add_argument(
        "--clients",
        default="default",
        help="comma list of harness ids. Aliases: claude, copilot, gemini",
    )
    for harness in HARNESS_LIST:
        flags = ["--" + harness.id]
        for alias, target in ALIASES.items():
            if target == harness.id:
                flags.append("--" + alias)
        command.add_argument(
            *flags,
            dest=harness.attr,
            action="store_true",
            help="select {} ({})".format(harness.label, "~/" + harness.skills.as_posix()),
        )


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_skill_flags(command):
        command.add_argument("--skill", action="append", default=[], help="link this skill too; repeat for more than one")
        command.add_argument("--skip-source", action="append", default=[], help="bulk-link every skill except this source; repeatable")
        command.add_argument("--dry-run", action="store_true")

    install = sub.add_parser("install", help="link selected skills, never overwrite unrelated files")
    add_target_flags(install)
    add_skill_flags(install)
    sync = sub.add_parser("sync", help="make harness links match enabled-skills.txt")
    add_target_flags(sync)
    add_skill_flags(sync)
    uninstall = sub.add_parser("uninstall", help="remove symlinks that point into this repo")
    add_target_flags(uninstall)
    uninstall.add_argument("--skill", action="append", default=[], help="remove only this skill; repeatable")
    uninstall.add_argument("--dry-run", action="store_true")
    sub.add_parser("doctor", help="report broken links and conflicts")
    return parser


def main(argv):
    configure_color()
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
