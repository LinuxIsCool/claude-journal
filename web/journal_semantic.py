"""journal_semantic.py — optional semantic leg for hybrid journal search.

Embeds the query with TELUS NV-E5 (asymmetric, input_type=query), runs a
pgvector cosine-KNN over the journal embeddings already in personal_koi
(`embeddings_telus_e5_1024`), then maps the matched KOI bundle RIDs back to
JournalAccessor record ids via a (date, HH-MM) key derived from both sides.

DESIGN: best-effort + graceful degradation. Any failure (no creds, network
down, psycopg/pgvector missing, no key match) returns [] so the caller falls
back to FTS-only. Never raises into the request path.

RID shape (observed):  orn:legion.claude-journal:2026-03-12/08-00-morning-brief
Record key:            "2026-03-12|08-00"  (date + filename HH-MM)
"""
from __future__ import annotations

import os
import re
import time
import urllib.request
import urllib.error
import json
from pathlib import Path
from typing import Any

_SECRETS = Path.home() / ".claude" / "local" / "secrets" / "telus-api.env"
_DSN = os.environ.get("PERSONAL_KOI_DSN", "dbname=personal_koi")
_NAMESPACE = "legion.claude-journal"
_RE_RID_TAIL = re.compile(r":(\d{4}-\d{2}-\d{2})/(\d{2}-\d{2})")
_RE_TS = re.compile(r"^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})")
_EMBED_TIMEOUT = 20
_CACHE_TTL = 600  # query-embedding cache, seconds


def _load_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k.startswith("TELUS_EMBED")}
    if _SECRETS.is_file():
        for line in _SECRETS.read_text().splitlines():
            line = line.strip()
            if line.startswith("TELUS_EMBED") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def record_key(rec: dict[str, Any]) -> str | None:
    """Build the join key from a parsed record's ISO timestamp."""
    m = _RE_TS.match(rec.get("ts") or "")
    if not m:
        return None
    return f"{m.group(1)}|{m.group(2)}-{m.group(3)}"


def _rid_key(rid: str) -> str | None:
    m = _RE_RID_TAIL.search(rid or "")
    if not m:
        return None
    return f"{m.group(1)}|{m.group(2)}"


class JournalSemantic:
    """Lazily-initialized semantic searcher. Safe to construct unconditionally."""

    def __init__(self) -> None:
        self._env = _load_env()
        self._url = self._env.get("TELUS_EMBED_URL", "")
        self._key = self._env.get("TELUS_EMBED_KEY", "")
        self._model = self._env.get("TELUS_EMBED_MODEL", "nvidia/nv-embedqa-e5-v5")
        self._qcache: dict[str, tuple[float, list[float]]] = {}
        self._available: bool | None = None

    @property
    def configured(self) -> bool:
        return bool(self._url and self._key)

    def _embed_query(self, query: str) -> list[float] | None:
        if not self.configured:
            return None
        now = time.time()
        cached = self._qcache.get(query)
        if cached and now - cached[0] < _CACHE_TTL:
            return cached[1]
        payload = json.dumps({
            "model": self._model, "input": query, "input_type": "query",
        }).encode()
        req = urllib.request.Request(
            self._url, data=payload, method="POST",
            headers={"Authorization": f"Bearer {self._key}",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=_EMBED_TIMEOUT) as r:
                data = json.loads(r.read())
            vec = data["data"][0]["embedding"]
        except (urllib.error.URLError, KeyError, IndexError, ValueError, OSError):
            return None
        self._qcache[query] = (now, vec)
        return vec

    def search_keys(self, query: str, limit: int = 60) -> list[str]:
        """Return record-join-keys ranked by semantic similarity (best first).

        Empty list on any failure → caller degrades to FTS-only.
        """
        vec = self._embed_query(query)
        if not vec:
            return []
        try:
            import psycopg  # local import: optional dependency
        except ImportError:
            return []
        lit = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        sql = (
            "SELECT b.rid FROM embeddings_telus_e5_1024 e "
            "JOIN bundles b ON b.rid = e.rid "
            "WHERE b.namespace = %s "
            "ORDER BY e.embedding <=> %s::vector LIMIT %s"
        )
        try:
            with psycopg.connect(_DSN, connect_timeout=5) as con:
                rows = con.execute(sql, (_NAMESPACE, lit, limit * 3)).fetchall()
        except Exception:
            return []
        keys: list[str] = []
        seen: set[str] = set()
        for (rid,) in rows:
            k = _rid_key(rid)
            if k and k not in seen:
                seen.add(k)
                keys.append(k)
            if len(keys) >= limit:
                break
        return keys
