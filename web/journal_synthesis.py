"""journal_synthesis.py — display-only LLM synthesis for the journal webui (Phase 4.5).

Read-side AI. Gathers entries for a scope, sends a compact corpus to TELUS
(Gemma, OpenAI-compatible chat completions), returns a markdown narrative.
**Never writes to disk** — summary-file authoring stays the scribe agent's job;
this surface only reflects.

Exposed through the MutationCatalog (the kernel's sole POST path) as a single
`synthesize` tool with a `kind` arg:
    week      — digest of the last 7 days
    month     — synthesis of the current calendar month
    patterns  — recurring themes across recent entries
    openloops — commitments / open questions not yet resolved

Graceful degradation: missing creds / network error → MutationError(UPSTREAM)
with a human message; the browser shows a toast and the view stays usable.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from claude_webui.dispatcher import MutationCatalog, MutationError

_SECRETS = Path.home() / ".claude" / "local" / "secrets" / "telus-api.env"
_TIMEOUT = 80
_MAX_CORPUS_CHARS = 14_000
_MAX_ENTRIES = 90
_VALID_KINDS = {"week", "month", "patterns", "openloops"}


def _load_telus() -> tuple[str, str, str]:
    env = dict(os.environ)
    if _SECRETS.is_file():
        for line in _SECRETS.read_text().splitlines():
            line = line.strip()
            if line.startswith("TELUS_GEMMA_") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return (env.get("TELUS_GEMMA_URL", ""), env.get("TELUS_GEMMA_KEY", ""),
            env.get("TELUS_GEMMA_MODEL", "google/gemma-4-31b-it"))


def _complete(system: str, user: str, max_tokens: int = 900) -> str:
    url, key, model = _load_telus()
    if not url or not key:
        raise MutationError(
            "UPSTREAM", "TELUS completion endpoint not configured",
            details={"hint": "set TELUS_GEMMA_URL / TELUS_GEMMA_KEY"},
        )
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }).encode()
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            data = json.loads(r.read())
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, IndexError, ValueError, OSError) as e:
        raise MutationError(
            "UPSTREAM", f"synthesis upstream failed: {type(e).__name__}",
            details={"error": str(e)[:200]},
            rollback_hint="try again, or check TELUS connectivity",
        )


def _corpus(records: list[dict[str, Any]]) -> str:
    lines, total = [], 0
    for r in records[:_MAX_ENTRIES]:
        line = f"- [{(r.get('ts') or '')[:10]}] ({r.get('author','')}) {r.get('title','')} — {(r.get('excerpt') or '')[:180]}"
        if total + len(line) > _MAX_CORPUS_CHARS:
            break
        lines.append(line)
        total += len(line)
    return "\n".join(lines)


_SYSTEM = (
    "You are a reflective journaling synthesist. You read a person's journal "
    "entries and produce concise, honest, useful markdown. No flattery, no "
    "filler. Surface real patterns, tensions, and signal. Use short sections "
    "and bullet points. Never invent facts not present in the entries."
)

_PROMPTS: dict[str, tuple[str, str]] = {
    "week": ("digest of the last 7 days",
             "Write a weekly digest from these journal entries. Cover: the throughline "
             "of the week, what shipped, what stalled, the emotional tone, and 2-3 "
             "things worth attention next week. Entries:\n\n{corpus}"),
    "month": ("synthesis of this month",
              "Write a month-in-review from these journal entries. Cover: major arcs, "
              "recurring themes, decisions made, and what changed from start to end. "
              "Entries:\n\n{corpus}"),
    "patterns": ("recurring patterns",
                 "Identify the recurring patterns across these journal entries — themes "
                 "that repeat, tensions that resurface, habits visible in the cadence. "
                 "Be specific and cite dates. Entries:\n\n{corpus}"),
    "openloops": ("open loops",
                  "From these journal entries, extract OPEN LOOPS: commitments made but "
                  "not clearly closed, questions raised but unanswered, and things the "
                  "writer said they'd do. List each with its date and a short status guess. "
                  "Entries:\n\n{corpus}"),
}


def _filter_for(kind: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select journal-class records relevant to the scope (newest first)."""
    recs = [r for r in records if r.get("source_class") == "journal"]
    now = datetime.now()
    if kind == "week":
        cut = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        return [r for r in recs if (r.get("ts") or "")[:10] >= cut]
    if kind == "month":
        mk = now.strftime("%Y-%m")
        return [r for r in recs if (r.get("ts") or "")[:7] == mk]
    # patterns / openloops → most recent ~60
    return recs[:60]


def make_handler(records_fn: Callable[[], list[dict[str, Any]]]):
    def synthesize(args: dict[str, Any]) -> dict[str, Any]:
        kind = str(args.get("kind") or "").strip()
        if kind not in _VALID_KINDS:
            raise MutationError(
                MutationError.INVALID_ARGS,
                f"kind must be one of {sorted(_VALID_KINDS)}",
                details={"received": kind},
            )
        records = records_fn()
        scoped = _filter_for(kind, records)
        if not scoped:
            return {"kind": kind, "markdown": "_No entries in scope to synthesize._",
                    "entry_count": 0}
        label, tmpl = _PROMPTS[kind]
        md = _complete(_SYSTEM, tmpl.format(corpus=_corpus(scoped)))
        return {"kind": kind, "label": label, "markdown": md,
                "entry_count": len(scoped)}
    return synthesize


def register_synthesis(catalog: MutationCatalog,
                       records_fn: Callable[[], list[dict[str, Any]]]) -> None:
    catalog.register(
        "synthesize", make_handler(records_fn),
        args_schema={"kind": {"type": "string", "required": True,
                              "enum": sorted(_VALID_KINDS)}},
    )
