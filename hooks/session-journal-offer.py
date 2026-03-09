#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""
Stop hook: suggest journaling after significant sessions.
Outputs a suggestion if the session likely involved meaningful work.
"""

import json
import os
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
    # Read hook input from stdin if available
    hook_input = {}
    if not sys.stdin.isatty():
        try:
            hook_input = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            pass

    # Simple heuristic: if the stop reason suggests real work was done
    stop_reason = hook_input.get("stop_reason", "")
    transcript_turns = hook_input.get("transcript_turns", 0)

    # If very few turns, probably not worth journaling about
    if transcript_turns < 5:
        return

    print("This session involved significant work. Consider /journal to capture what happened.")


if __name__ == "__main__":
    main()
