"""journal_search.py — FTS5 sidecar for the journal corpus.

A derived cache (NOT a second source of truth): an SQLite FTS5 index built
from the JournalAccessor's already-parsed records. Rebuilt only when the
accessor signature changes. Lives OUTSIDE the journal root so writing it
never perturbs the accessor's directory-mtime signature.

Public API:
    idx = JournalFTS(records_fn, signature_fn)
    hits = idx.search("query terms", limit=80)   # → [{"id","snippet","rank"}]

`records_fn()` returns the list of parsed records (dicts with id/title/tags/
author/ts/body_md). `signature_fn()` returns the accessor signature tuple.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import threading
from pathlib import Path
from typing import Any, Callable

_CACHE_DIR = Path.home() / ".claude" / "local" / "journal-webui-cache"
_DB_PATH = _CACHE_DIR / "fts.db"
_FTS_SPECIAL = re.compile(r'["*()]')


def _sig_hash(sig: tuple) -> str:
    return hashlib.sha1(repr(sig).encode()).hexdigest()


def _sanitize_query(q: str) -> str:
    """Turn free text into a safe FTS5 MATCH expression (prefix-AND).

    Strips FTS operators, splits on whitespace, ANDs the terms with a
    trailing prefix-* on the last token for as-you-type feel.
    """
    q = _FTS_SPECIAL.sub(" ", q or "").strip()
    toks = [t for t in q.split() if t]
    if not toks:
        return ""
    # quote each token to neutralize FTS keywords (AND/OR/NEAR); prefix last
    quoted = [f'"{t}"' for t in toks[:-1]]
    quoted.append(f'"{toks[-1]}"*')
    return " ".join(quoted)


class JournalFTS:
    def __init__(
        self,
        records_fn: Callable[[], list[dict[str, Any]]],
        signature_fn: Callable[[], tuple],
        db_path: Path | None = None,
    ) -> None:
        self._records_fn = records_fn
        self._signature_fn = signature_fn
        self._db_path = db_path or _DB_PATH
        self._built_sig: str | None = None
        self._lock = threading.Lock()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self._db_path)
        con.row_factory = sqlite3.Row
        return con

    def _ensure(self) -> None:
        """Rebuild the FTS index if the accessor signature changed."""
        sig = _sig_hash(self._signature_fn())
        if sig == self._built_sig and self._db_path.exists():
            return
        with self._lock:
            if sig == self._built_sig and self._db_path.exists():
                return
            records = self._records_fn()
            con = self._connect()
            try:
                con.execute("DROP TABLE IF EXISTS fts")
                # id/author/ts unindexed columns ride along for retrieval;
                # title/tags/body are tokenized + searchable.
                con.execute(
                    "CREATE VIRTUAL TABLE fts USING fts5("
                    "id UNINDEXED, author UNINDEXED, ts UNINDEXED, "
                    "title, tags, body, tokenize='porter unicode61')"
                )
                con.executemany(
                    "INSERT INTO fts(id, author, ts, title, tags, body) "
                    "VALUES (?,?,?,?,?,?)",
                    [
                        (r["id"], r["author"], r["ts"], r["title"],
                         " ".join(r.get("tags") or []), r.get("body_md") or "")
                        for r in records
                    ],
                )
                con.commit()
            finally:
                con.close()
            self._built_sig = sig

    def search(self, query: str, limit: int = 80) -> list[dict[str, Any]]:
        """Return ranked hits with a highlighted snippet.

        Ranking: FTS5 bm25 with title/tags weighted above body. Snippet is
        drawn from the body (falls back to title) with <mark> highlights.
        """
        match = _sanitize_query(query)
        if not match:
            return []
        self._ensure()
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT id, "
                "snippet(fts, 5, '<mark>', '</mark>', '…', 12) AS snip, "
                "snippet(fts, 3, '<mark>', '</mark>', '', 8)  AS tsnip, "
                "bm25(fts, 0, 0, 0, 8.0, 4.0, 1.0) AS rank "
                "FROM fts WHERE fts MATCH ? ORDER BY rank LIMIT ?",
                (match, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        finally:
            con.close()
        out = []
        for i, row in enumerate(rows):
            snip = (row["snip"] or "").strip() or (row["tsnip"] or "").strip()
            out.append({"id": row["id"], "snippet": snip, "rank": i})
        return out
