#!/usr/bin/env python3
"""Fail if a vendored skill contains a secret or a remote-exec payload.

Markdown may mention the two installer URLs already shipped by upstream
catalogs. Any other URL piped into a shell is a failure. Code files are
stricter: a pipe into a shell fails even without a URL.
"""

import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {
    ".md", ".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts", ".tsx",
    ".ps1", ".rb", ".php", ".json", ".yml", ".yaml", ".txt", ".toml", ".html",
    ".css", ".csv", ".xml", ".env", ".example", ".command",
}
CODE_SUFFIXES = {
    ".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts", ".tsx",
    ".ps1", ".rb", ".php", ".command",
}
# Installers that already ship inside the vendored catalogs.
ALLOWED_INSTALL_HOSTS = {
    "cli.oomol.com",
    "static.heygen.ai",
}

SECRET_RULES = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |PGP )?PRIVATE KEY-----")),
    ("github-token", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    ("github-pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{82,}\b")),
    ("aws-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[0-9]{8,}-[0-9A-Za-z-]{20,}")),
    ("anthropic-key", re.compile(r"\bsk-ant-(?:api03|admin01)-[A-Za-z0-9_-]{20,}\b")),
)
REMOTE_URL = re.compile(
    r"(?:curl|wget)\b[^\n]{0,220}https?://([^/\s\"'`]+)[^\n]{0,220}\|\s*(?:ba)?sh\b",
    re.I,
)
REMOTE_ANY = re.compile(r"(?:curl|wget)\b[^\n]{0,220}\|\s*(?:ba)?sh\b", re.I)
PROCESS_SUB = re.compile(
    r"(?:bash|sh|eval)\b[^\n]{0,60}(?:<\(|\$\()\s*(?:curl|wget)\b",
    re.I,
)
REVERSE_SHELL = re.compile(
    r"/dev/tcp/|bash\s+-i\b|\bnc\b[^\n]{0,80}\s-e\s|\bncat\b[^\n]{0,80}\s-e\s",
    re.I,
)
DECODE_EXEC = re.compile(
    r"base64\s+(?:-d|--decode)\b[^\n]{0,80}\|\s*(?:ba)?sh\b",
    re.I,
)
DESTRUCTIVE_RM = re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+/(?:\s|$|\*)")
MAX_BYTES = 2_000_000


def skills_dir(path):
    path = Path(path)
    if path.name != "skills" and (path / "skills").is_dir():
        return path / "skills"
    return path


def looks_like_code(path, first_line):
    if path.suffix.lower() in CODE_SUFFIXES:
        return True
    return first_line.startswith("#!") and ("sh" in first_line or "bash" in first_line or "python" in first_line)


def scan_text(rel, text, code):
    findings = []
    for name, pattern in SECRET_RULES:
        match = pattern.search(text)
        if match:
            findings.append((rel, _line_of(text, match.start()), name, _snippet(match.group(0))))
    if code:
        for name, pattern in (
            ("remote-shell", REMOTE_ANY),
            ("remote-exec", PROCESS_SUB),
            ("reverse-shell", REVERSE_SHELL),
            ("decode-exec", DECODE_EXEC),
            ("destructive-rm", DESTRUCTIVE_RM),
        ):
            match = pattern.search(text)
            if match:
                findings.append((rel, _line_of(text, match.start()), name, _snippet(match.group(0))))
        return findings
    for match in REMOTE_URL.finditer(text):
        host = match.group(1).lower()
        if host in ALLOWED_INSTALL_HOSTS:
            continue
        findings.append((rel, _line_of(text, match.start()), "remote-shell", _snippet(match.group(0))))
    return findings


def _line_of(text, index):
    return text.count("\n", 0, index) + 1


def _snippet(text):
    return " ".join(text.split())[:120]


def scan(root):
    root = skills_dir(root)
    findings = []
    files = 0
    if not root.is_dir():
        raise SystemExit("no skills directory at {}".format(root))
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.stat().st_size > MAX_BYTES:
            continue
        suffix = path.suffix.lower()
        if suffix not in TEXT_SUFFIXES and suffix != "":
            continue
        raw = path.read_bytes()
        if b"\0" in raw[:800]:
            continue
        text = raw.decode("utf-8", errors="replace")
        first = text.splitlines()[0] if text else ""
        if suffix == "" and not looks_like_code(path, first):
            continue
        files += 1
        rel = str(path.relative_to(root.parent if root.name == "skills" else root))
        findings.extend(scan_text(rel, text, looks_like_code(path, first)))
    return files, findings


def main(argv):
    target = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1]
    files, findings = scan(target)
    if findings:
        for rel, line, name, snippet in findings:
            print("{}:{}: {}: {}".format(rel, line, name, snippet), file=sys.stderr)
        print("failed {} finding(s) in {} file(s)".format(len(findings), files), file=sys.stderr)
        return 1
    print("ok {} file(s)".format(files))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
