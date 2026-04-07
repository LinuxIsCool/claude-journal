#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""
Session-start hook: surface the most recent N journal entries as context.

Prevents the "forgetting last Friday" failure mode where a fresh session
has no awareness of recent work. Reads the last N markdown files from
~/.claude/local/journal/ (sorted by mtime) and emits a compact summary
with title, date, and body preview.

Outputs JSON with systemMessage (visible to user) and additionalContext
(available to Claude).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

JOURNAL_ROOT = Path.home() / ".claude" / "local" / "journal"
MAX_ENTRIES = 5
PREVIEW_CHARS = 180


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text_after_frontmatter)."""
    try:
        content = path.read_text()
    except (OSError, UnicodeDecodeError):
        return {}, ""
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content
    try:
        fm = yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        fm = {}
    body = content[end + 3 :].lstrip()
    return fm, body


def body_preview(body: str, n: int = PREVIEW_CHARS) -> str:
    """Take the first non-heading paragraph of body as a preview."""
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if lines:
                break
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith(">"):
            continue
        lines.append(stripped)
        if sum(len(l) for l in lines) > n:
            break
    preview = " ".join(lines)
    if len(preview) > n:
        preview = preview[: n - 1].rsplit(" ", 1)[0] + "…"
    return preview


def recent_entries(root: Path, limit: int) -> list[Path]:
    """Return the most recent `limit` markdown files under root, by mtime."""
    if not root.exists():
        return []
    candidates = []
    for path in root.rglob("*.md"):
        if path.name.startswith("."):
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        candidates.append((mtime, path))
    candidates.sort(reverse=True)
    return [p for _, p in candidates[:limit]]


def format_entry(path: Path) -> str:
    fm, body = parse_frontmatter(path)
    title = fm.get("title") or path.stem
    title = str(title).strip()
    if len(title) > 90:
        title = title[:88] + "…"
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        ts = mtime.astimezone().strftime("%b %d %H:%M")
    except OSError:
        ts = "?"
    preview = body_preview(body)
    rel = path.relative_to(Path.home())
    line = f"- **{ts}** — *{title}*"
    if preview:
        line += f"\n  > {preview}"
    line += f"\n  `~/{rel}`"
    return line


def build_context() -> str:
    paths = recent_entries(JOURNAL_ROOT, MAX_ENTRIES)
    if not paths:
        return ""
    lines = [f"## Recent journal entries (last {len(paths)})"]
    lines.extend(format_entry(p) for p in paths)
    lines.append(
        "\n_These are the most recent things you worked on. "
        "Consider reading any that seem relevant before starting new work._"
    )
    return "\n".join(lines)


def output(msg: str):
    print(
        json.dumps(
            {
                "systemMessage": msg,
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": msg,
                },
            }
        )
    )


def main():
    # Consume stdin (Claude Code may pipe hook input)
    try:
        json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        pass

    context = build_context()
    if context:
        output(context)
    else:
        # Empty output — no journal yet, don't nag
        print(json.dumps({}))


if __name__ == "__main__":
    main()
