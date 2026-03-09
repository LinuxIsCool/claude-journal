#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""
Stop hook: suggest journaling after significant sessions.
Outputs JSON with systemMessage (visible) and additionalContext (Claude sees).
"""

import json
import sys
from pathlib import Path

import yaml

JOURNAL_ROOT = Path.home() / ".claude" / "local" / "journal"
CONFIG_PATH = JOURNAL_ROOT / "config.yml"


def load_config() -> dict:
    defaults = {"stop_hook_threshold_minutes": 30}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return {**defaults, **(yaml.safe_load(f) or {})}
    return defaults


def main():
    # Read hook input from stdin
    hook_input = {}
    try:
        hook_input = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        pass

    transcript_turns = hook_input.get("transcript_turns", 0)

    # If very few turns, not worth journaling about
    if transcript_turns < 5:
        return

    msg = "This session involved significant work. Consider /journal to capture what happened."
    print(json.dumps({
        "systemMessage": msg,
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": msg,
        },
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
