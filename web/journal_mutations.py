"""journal_mutations.py — write surface for the claude-journal webui (Phase 4).

Two handlers, both writing the plugin's canonical atomic-entry contract
(see claude-journal/CLAUDE.md):

    ~/.claude/local/journal/{author}/YYYY/MM/DD/HH-MM-slug.md

  - create_entry  — new atomic entry (composer / quick-capture / templates /
                    daily-prompt all funnel here; the client prefills body).
  - append_today  — append a timestamped block to the author's running daily
                    entry, creating it if absent.

Safety invariants:
  - author + slug are strictly sanitized (`^[a-z0-9-]+$` / kebab) → no path
    traversal, no escaping the journal root.
  - writes are atomic (temp file + os.replace) and never overwrite an
    existing file (filename disambiguated with seconds, then a counter).
  - all writes stay under the journal root; resolved paths are re-checked
    against it (defense-in-depth).
  - frontmatter always carries `source: webui` provenance + a `web-capture`
    tag so these entries are distinguishable from agent/scribe output.
"""
from __future__ import annotations

import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from claude_webui.dispatcher import MutationCatalog, MutationError

_ROOT = Path.home() / ".claude" / "local" / "journal"
_MACHINE = "legion"
_RE_AUTHOR = re.compile(r"^[a-z0-9][a-z0-9-]{0,30}$")
_MAX_TITLE = 200
_MAX_BODY = 50_000
_DEFAULT_AUTHOR = "shawn"


def _now() -> datetime:
    return datetime.now().astimezone()


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:60] or "entry"


def _clean_author(raw: Any) -> str:
    a = str(raw or _DEFAULT_AUTHOR).strip().lower()
    if not _RE_AUTHOR.match(a):
        raise MutationError(
            MutationError.INVALID_ARGS,
            "author must match ^[a-z0-9][a-z0-9-]{0,30}$",
            details={"received": repr(raw)},
        )
    return a


def _clean_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = re.split(r"[,\s]+", raw)
    if not isinstance(raw, (list, tuple)):
        return []
    out, seen = [], set()
    for t in raw:
        t = re.sub(r"[^a-z0-9-]+", "", str(t).lower())
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _ensure_within_root(path: Path) -> None:
    try:
        path.resolve().relative_to(_ROOT.resolve())
    except ValueError:
        raise MutationError(
            MutationError.INVALID_ARGS,
            "refusing to write outside the journal root",
            details={"path": str(path)},
        )


def _atomic_write(path: Path, text: str) -> None:
    _ensure_within_root(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _frontmatter(d: dict[str, Any]) -> str:
    body = d.pop("_body", "")
    fm = yaml.safe_dump(d, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm}\n---\n\n{body}\n"


def _unique_path(folder: Path, base_slug: str, now: datetime) -> Path:
    """HH-MM-slug.md, disambiguated with seconds then a counter on collision."""
    hhmm = now.strftime("%H-%M")
    cand = folder / f"{hhmm}-{base_slug}.md"
    if not cand.exists():
        return cand
    hhmmss = now.strftime("%H-%M-%S")
    cand = folder / f"{hhmmss}-{base_slug}.md"
    i = 2
    while cand.exists():
        cand = folder / f"{hhmmss}-{base_slug}-{i}.md"
        i += 1
    return cand


def _validate_text(title: str, body: str) -> tuple[str, str]:
    title = (title or "").strip()
    body = (body or "").strip()
    if not title and not body:
        raise MutationError(
            MutationError.INVALID_ARGS, "entry needs a title or a body"
        )
    if len(title) > _MAX_TITLE:
        raise MutationError(MutationError.INVALID_ARGS, f"title exceeds {_MAX_TITLE} chars")
    if len(body) > _MAX_BODY:
        raise MutationError(MutationError.INVALID_ARGS, f"body exceeds {_MAX_BODY} chars")
    if not title:
        title = body.splitlines()[0][:80]
    return title, body


# ── handlers ─────────────────────────────────────────────────────────────


def create_entry(args: dict[str, Any]) -> dict[str, Any]:
    """Create a new atomic journal entry. args: {title, body, tags?, author?}."""
    author = _clean_author(args.get("author"))
    title, body = _validate_text(args.get("title", ""), args.get("body", ""))
    tags = _clean_tags(args.get("tags"))
    if "web-capture" not in tags:
        tags.append("web-capture")

    now = _now()
    folder = _ROOT / author / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
    path = _unique_path(folder, _slugify(title), now)

    doc = {
        "title": title,
        "created": now.isoformat(timespec="seconds"),
        "machine": _MACHINE,
        "author": author,
        "tags": tags,
        "type": "atomic",
        "source": "webui",
        "_body": body,
    }
    _atomic_write(path, _frontmatter(doc))
    return {
        "ok": True,
        "author": author,
        "title": title,
        "path": str(path),
        "relpath": str(path.relative_to(_ROOT)),
        "created": doc["created"],
    }


def append_today(args: dict[str, Any]) -> dict[str, Any]:
    """Append a timestamped block to the author's running daily entry.

    args: {author?, text}. Creates `HH-MM-...` is NOT used here — instead a
    stable daily file `YYYY-MM-DD-running.md` per author so appends coalesce.
    """
    author = _clean_author(args.get("author"))
    text = (args.get("text") or "").strip()
    if not text:
        raise MutationError(MutationError.INVALID_ARGS, "text is required")
    if len(text) > _MAX_BODY:
        raise MutationError(MutationError.INVALID_ARGS, f"text exceeds {_MAX_BODY} chars")

    now = _now()
    folder = _ROOT / author / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
    path = folder / f"{now.strftime('%Y-%m-%d')}-running.md"
    stamp = now.strftime("%H:%M")
    block = f"\n## {stamp}\n\n{text}\n"

    if path.exists():
        _ensure_within_root(path)
        existing = path.read_text(encoding="utf-8", errors="replace")
        _atomic_write(path, existing.rstrip() + "\n" + block)
        created = False
    else:
        doc = {
            "title": f"{now.strftime('%Y-%m-%d')} — running notes",
            "created": now.isoformat(timespec="seconds"),
            "machine": _MACHINE,
            "author": author,
            "tags": ["running", "web-capture"],
            "type": "atomic",
            "source": "webui",
            "_body": block.lstrip(),
        }
        _atomic_write(path, _frontmatter(doc))
        created = True

    return {
        "ok": True, "author": author, "appended_at": stamp,
        "created": created, "path": str(path),
        "relpath": str(path.relative_to(_ROOT)),
    }


# ── registration ─────────────────────────────────────────────────────────


def register_handlers(catalog: MutationCatalog) -> None:
    catalog.register(
        "create_entry", create_entry,
        args_schema={
            "title": {"type": "string", "required": False},
            "body": {"type": "string", "required": False},
            "tags": {"type": "array", "required": False},
            "author": {"type": "string", "required": False},
        },
    )
    catalog.register(
        "append_today", append_today,
        args_schema={
            "text": {"type": "string", "required": True},
            "author": {"type": "string", "required": False},
        },
    )
