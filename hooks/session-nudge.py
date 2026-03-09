#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""
Session-start hook: check when the last journal entry was written.
Outputs JSON with systemMessage (visible banner) and additionalContext (Claude sees).
"""

import json
import sys
from datetime import date
from pathlib import Path

import yaml

JOURNAL_ROOT = Path.home() / ".claude" / "local" / "journal"
CONFIG_PATH = JOURNAL_ROOT / "config.yml"

DEFAULT_CONFIG = {
    "default_machine": "legion",
    "nudge_after_days": 3,
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return {**DEFAULT_CONFIG, **(yaml.safe_load(f) or {})}
    return DEFAULT_CONFIG


def parse_frontmatter(path: Path) -> dict:
    content = path.read_text()
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    return yaml.safe_load(content[3:end]) or {}


def output(msg: str):
    """Output as JSON with both systemMessage and additionalContext."""
    print(json.dumps({
        "systemMessage": msg,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": msg,
        },
    }))


def main():
    # Consume stdin (Claude Code may pipe hook input)
    try:
        json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        pass

    config = load_config()
    machine = config["default_machine"]
    machine_dir = JOURNAL_ROOT / machine
    if not machine_dir.exists():
        return

    today = date.today()
    today_dir = machine_dir / str(today.year) / f"{today.month:02d}" / f"{today.day:02d}"

    # Check today's entries
    today_entries = []
    if today_dir.exists():
        today_entries = sorted(today_dir.glob("*.md"))
        # Exclude summary files (YYYY-MM-DD.md pattern)
        today_entries = [
            e for e in today_entries
            if not e.stem.startswith(str(today.year))
        ]

    if today_entries:
        latest = today_entries[-1]
        fm = parse_frontmatter(latest)
        title = fm.get("title", latest.stem)
        time_part = latest.stem[:5].replace("-", ":")
        output(f"[journal] {len(today_entries)} entries today · latest: \"{title}\" ({time_part})")
        return

    # Find the most recent entry across all dates
    latest_date = None
    for year_dir in sorted(machine_dir.iterdir(), reverse=True):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for month_dir in sorted(year_dir.iterdir(), reverse=True):
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue
            for day_dir in sorted(month_dir.iterdir(), reverse=True):
                if not day_dir.is_dir() or not day_dir.name.isdigit():
                    continue
                entries = [
                    e for e in day_dir.glob("*.md")
                    if not e.stem.startswith(year_dir.name)
                ]
                if entries:
                    y, m, d = int(year_dir.name), int(month_dir.name), int(day_dir.name)
                    latest_date = date(y, m, d)
                    break
            if latest_date:
                break
        if latest_date:
            break

    if latest_date is None:
        output("[journal] no entries yet · /journal to start")
        return

    days_ago = (today - latest_date).days
    nudge_threshold = config["nudge_after_days"]

    if days_ago >= nudge_threshold:
        output(f"[journal] last entry {days_ago}d ago ({latest_date.isoformat()}) · /journal to capture recent work")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
