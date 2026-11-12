#!/usr/bin/env python3
"""Compare pins in docs/sources.lock.json with upstream GitHub.

A source pinned to a tag is stale when GitHub has a different newest tag
or latest release. A source pinned to a commit, with no tag, is stale when
the default branch tip has moved. Local skills are not checked.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


LIST_LIMIT = 25


def repo_slug(url):
    text = url.split("?", 1)[0].rstrip("/")
    prefix = "https://github.com/"
    if not text.startswith(prefix):
        return None
    parts = text[len(prefix):].split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1]


SEMVER = re.compile(
    r"^(?P<prefix>.*?)(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?P<rest>.*)$"
)


def parse_tag(tag):
    match = SEMVER.match(tag or "")
    if not match:
        return None
    return {
        "prefix": match.group("prefix"),
        "version": (
            int(match.group("major")),
            int(match.group("minor")),
            int(match.group("patch")),
        ),
        "prerelease": match.group("rest").startswith("-"),
    }


def newer_tag(pinned, names):
    """Highest same-prefix release tag newer than pinned. Other product lines are ignored."""
    pin = parse_tag(pinned)
    if not pin or pin["prerelease"]:
        return None
    best_name = None
    best_version = pin["version"]
    for name in names:
        parsed = parse_tag(name)
        if not parsed or parsed["prerelease"]:
            continue
        if parsed["prefix"] != pin["prefix"]:
            continue
        if parsed["version"] > best_version:
            best_version = parsed["version"]
            best_name = name
    return best_name


def decide(source, upstream):
    """Return (state, reason). state is 'stale', 'current', or 'error'."""
    if upstream.get("error"):
        return "error", upstream["error"]
    tag = source.get("tag_or_version")
    pin = source.get("commit") or ""
    tip = upstream.get("default_sha") or ""
    branch = upstream.get("default_branch") or "default branch"
    if tag:
        newer = newer_tag(tag, upstream.get("names") or [])
        if newer:
            return "stale", "newer tag {} (pinned {})".format(newer, tag)
        if upstream.get("tag_exists", True):
            return "current", "tag {}".format(tag)
    if not tip:
        return "error", "default branch tip missing"
    if tip != pin:
        return "stale", "{} moved from {} to {}".format(branch, pin[:12], tip[:12])
    if tag:
        return "current", "tag {} is not a git tag; commit {}".format(tag, pin[:12])
    return "current", "commit {}".format(pin[:12])


def _skill_lines(names, local_path):
    ordered = sorted(names)
    if not ordered:
        return ["- no skill directories (pin is not a skill catalog)"]
    if len(ordered) > LIST_LIMIT:
        return ["- {} skills under `{}`".format(len(ordered), local_path or "skills")]
    return ["- `{}`".format(name) for name in ordered]


def build_report(rows):
    """rows: dicts with id, state, reason, skills, local_path, url."""
    stale = [row for row in rows if row["state"] == "stale"]
    errors = [row for row in rows if row["state"] == "error"]
    current = [row for row in rows if row["state"] == "current"]
    if stale:
        status = "updates-found"
    elif errors:
        status = "check-failed"
    else:
        status = "up-to-date"
    lines = [
        "Status: {}".format(status),
        "",
        "A pinned tag is stale only when a newer tag shares its prefix.",
        "A pin with no git tag is compared with the default branch tip.",
        "A catalog larger than {} skills is listed as one group.".format(LIST_LIMIT),
        "",
    ]
    lines.append("## Needs update")
    lines.append("")
    if not stale:
        lines.append("None.")
        lines.append("")
    for row in stale:
        lines.append("### {}".format(row["id"]))
        lines.append("")
        lines.append(row["reason"] + ".")
        lines.append("")
        lines.append("Compare: {}".format(row["url"]))
        lines.append("")
        lines.extend(_skill_lines(row["skills"], row.get("local_path")))
        lines.append("")
    if errors:
        lines.append("## Could not check")
        lines.append("")
        for row in errors:
            lines.append("- `{}`: {}".format(row["id"], row["reason"]))
        lines.append("")
    lines.append("## Up to date")
    lines.append("")
    if not current:
        lines.append("None.")
    else:
        for row in current:
            lines.append("- `{}` — {}".format(row["id"], row["reason"]))
    lines.append("")
    return "\n".join(lines)


def _open(url, token):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-resources-update-check",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode()), None, dict(resp.headers)
    except urllib.error.HTTPError as exc:
        return None, "HTTP {}".format(exc.code), {}
    except urllib.error.URLError as exc:
        return None, "network error: {}".format(exc.reason), {}


def _request(url, token):
    body, err, _headers = _open(url, token)
    return body, err


def _next_link(headers):
    link = ""
    for key, value in headers.items():
        if key.lower() == "link":
            link = value
            break
    for part in link.split(","):
        if 'rel="next"' not in part:
            continue
        start = part.find("<")
        end = part.find(">")
        if start >= 0 and end > start:
            return part[start + 1:end]
    return None


def _request_list(url, token):
    """Follow GitHub Link headers until every page of a list endpoint is loaded."""
    items = []
    pages = 0
    while url:
        pages += 1
        if pages > 50:
            return None, "too many result pages"
        body, err, headers = _open(url, token)
        if err:
            return None, err
        if not isinstance(body, list):
            return None, "expected a list"
        items.extend(body)
        url = _next_link(headers)
    return items, None


def fetch_upstream(source, token):
    slug = repo_slug(source.get("url") or "")
    if not slug:
        return {"error": "not a github.com URL"}
    owner, repo = slug
    base = "https://api.github.com/repos/{}/{}".format(owner, repo)
    meta, err = _request(base, token)
    if err:
        return {"error": err}
    branch = meta.get("default_branch") or "HEAD"
    result = {"default_branch": branch, "tag_exists": True}
    tag = source.get("tag_or_version")
    if tag:
        ref, ref_err = _request(base + "/git/ref/tags/" + urllib.parse.quote(tag), token)
        if ref_err and ref_err != "HTTP 404":
            return {"error": "tag lookup " + ref_err}
        result["tag_exists"] = ref_err is None and bool(ref)
        names = []
        tags, tag_err = _request_list(base + "/tags?per_page=100", token)
        if tag_err:
            return {"error": "tag list " + tag_err}
        names.extend(item.get("name") for item in tags or [] if item.get("name"))
        releases, rel_err = _request_list(base + "/releases?per_page=100", token)
        if rel_err == "HTTP 404":
            releases = []
        elif rel_err:
            return {"error": "release list " + rel_err}
        names.extend(item.get("tag_name") for item in releases or [] if item.get("tag_name"))
        result["names"] = names
        # A real git tag is decided from the tag list alone. Do not drop that
        # result when the default-branch request fails.
        if result["tag_exists"]:
            return result
    commit, commit_err = _request(base + "/commits/" + urllib.parse.quote(branch), token)
    if commit_err:
        return {"error": "commit lookup " + commit_err}
    result["default_sha"] = (commit.get("sha") or "")
    return result


def skills_by_source(origins):
    grouped = {}
    for name, meta in origins.get("skills", {}).items():
        if meta.get("managed") == "local":
            continue
        grouped.setdefault(meta.get("source"), []).append(name)
    return grouped


def collect(lock, origins, token, fetch=fetch_upstream):
    grouped = skills_by_source(origins)
    rows = []
    for source in lock.get("sources", []):
        upstream = fetch(source, token)
        state, reason = decide(source, upstream)
        rows.append({
            "id": source.get("id"),
            "state": state,
            "reason": reason,
            "skills": grouped.get(source.get("id"), []),
            "local_path": source.get("local_path"),
            "url": source.get("url"),
        })
    return rows


def self_test():
    stale_state, stale_reason = decide(
        {"tag_or_version": "skill-v4.8.2", "commit": "a" * 40},
        {"names": ["skill-v4.9.0", "loop-v0.1.1"], "tag_exists": True},
    )
    ignored_state, _ignored_reason = decide(
        {"tag_or_version": "v0.180.0", "commit": "a" * 40},
        {"names": ["v0.1.24", "v0.180.0"], "tag_exists": True},
    )
    current_state, _current_reason = decide(
        {"tag_or_version": None, "commit": "abc"},
        {"default_sha": "abc", "default_branch": "main"},
    )
    moved_state, moved_reason = decide(
        {"tag_or_version": "1.0.0", "commit": "a" * 40},
        {"names": [], "tag_exists": False, "default_sha": "b" * 40, "default_branch": "main"},
    )
    report = build_report([
        {
            "id": "demo",
            "state": stale_state,
            "reason": stale_reason,
            "skills": ["alpha"],
            "local_path": "skills/other",
            "url": "https://github.com/example/demo",
        },
        {
            "id": "quiet",
            "state": current_state,
            "reason": "commit abc",
            "skills": [],
            "local_path": "skills/quiet",
            "url": "https://github.com/example/quiet",
        },
    ])
    problems = []
    if stale_state != "stale" or "skill-v4.9.0" not in stale_reason:
        problems.append("tag drift not flagged")
    if ignored_state != "current":
        problems.append("older or unrelated tag was flagged")
    if current_state != "current":
        problems.append("matching commit flagged")
    if moved_state != "stale" or "main moved" not in moved_reason:
        problems.append("branch drift not flagged")
    if "Status: updates-found" not in report or "`alpha`" not in report:
        problems.append("report missing the stale skill")
    link = _next_link({
        "Link": '<https://api.github.com/repos/a/b/tags?page=2>; rel="next", <https://api.github.com/repos/a/b/tags?page=5>; rel="last"',
    })
    if link != "https://api.github.com/repos/a/b/tags?page=2":
        problems.append("next page link was not read")
    if _next_link({"Link": '<https://api.github.com/repos/a/b/tags?page=5>; rel="last"'}) is not None:
        problems.append("last page looked like another page")
    big = _skill_lines(["s{}".format(i) for i in range(LIST_LIMIT + 1)], "skills/oomol")
    if not any(line.startswith("- {}".format(LIST_LIMIT + 1)) for line in big):
        problems.append("large catalog was expanded")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("ok")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--md", type=Path, help="write the report here as well as stdout")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    repo = args.repo or Path(__file__).resolve().parents[1]
    lock = json.loads((repo / "docs" / "sources.lock.json").read_text())
    origins = json.loads((repo / "docs" / "skill-origins.json").read_text())
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    rows = collect(lock, origins, token)
    report = build_report(rows)
    print(report)
    if args.md:
        args.md.write_text(report)
    if any(row["state"] == "error" for row in rows):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
