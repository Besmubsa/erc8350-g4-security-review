#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from Git history using only the standard library."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from pathlib import Path
from typing import Iterable

SECTIONS = ("Added", "Fixed", "Changed", "Removed")


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def last_tag() -> str | None:
    tags = run_git("tag", "--sort=-creatordate")
    return tags.splitlines()[0] if tags else None


def classify(subject: str) -> str:
    """Map a commit subject to one of the four requested changelog sections."""
    text = subject.strip().lower()
    prefix = text.split(":", 1)[0]
    if prefix.startswith(("feat", "add", "feature")) or text.startswith(("add ", "added ", "introduce ")):
        return "Added"
    if prefix.startswith(("fix", "bugfix", "hotfix")) or text.startswith(("fix ", "resolve ", "correct ")):
        return "Fixed"
    if prefix.startswith(("remove", "delete")) or text.startswith(("remove ", "delete ", "drop ")):
        return "Removed"
    return "Changed"


def collect_commits(base_tag: str | None) -> list[tuple[str, str]]:
    revision = f"{base_tag}..HEAD" if base_tag else "HEAD"
    raw = run_git(
        "log",
        "--no-merges",
        "--pretty=format:%h%x09%s",
        revision,
    )
    commits: list[tuple[str, str]] = []
    for line in raw.splitlines():
        if "\t" not in line:
            continue
        short_hash, subject = line.split("\t", 1)
        if subject.strip():
            commits.append((short_hash, subject.strip()))
    return commits


def render(commits: Iterable[tuple[str, str]], version: str, date: str) -> str:
    grouped: dict[str, list[tuple[str, str]]] = {section: [] for section in SECTIONS}
    for short_hash, subject in commits:
        grouped[classify(subject)].append((short_hash, subject))

    lines = [f"# Changelog", "", f"## {version} — {date}", ""]
    found = False
    for section in SECTIONS:
        entries = grouped[section]
        if not entries:
            continue
        found = True
        lines.extend([f"### {section}", ""])
        lines.extend(f"- {subject} (`{short_hash}`)" for short_hash, subject in entries)
        lines.append("")
    if not found:
        lines.extend(["No commits found for this release.", ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="CHANGELOG.md", help="output path (default: CHANGELOG.md)")
    parser.add_argument("--version", help="release heading; defaults to the latest Git tag or Unreleased")
    parser.add_argument("--since", help="tag or revision to start after; defaults to the latest tag")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="release date (default: today)")
    args = parser.parse_args()

    try:
        base = args.since if args.since is not None else last_tag()
        commits = collect_commits(base)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or "Git command failed."
        parser.exit(2, f"error: {detail}\n")

    version = args.version or (last_tag() if base else "Unreleased")
    if args.version is None and base:
        version = f"Unreleased (since {base})"
    output = Path(args.output)
    output.write_text(render(commits, version, args.date), encoding="utf-8")
    print(f"Wrote {len(commits)} commit(s) to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
