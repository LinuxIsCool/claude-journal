"""JournalAccessor — read-through Accessor for the journal corpus.

Implements the claude_webui Accessor protocol (list / feed / detail / stats /
signature / healthz + NAMESPACE) over markdown files in
``~/.claude/local/journal/``. Read-only: no writes, no second copy of any
entry. Tolerant parsing per task-4133 Phase 0 (web/NOTES.md).

Frozen record schema (Phase 1):
    id            sha1(relpath)[:12]
    path          absolute
    relpath       from journal root
    author        normalized from top-level dir (lowercased); fallback frontmatter
    source_class  journal | transcript | pipeline-alert | legacy
    ts            ISO 8601 (frontmatter ts/created/date → path → filename → mtime)
    title         frontmatter title → first '# ' heading → filename slug
    tags          frontmatter tags[], lowercased, deduped (venture→ventures)
    body_md       content below the fence (or whole file if unfenced)
    excerpt       first ~200 chars of plain text
    has_fm        bool

Mode A standalone:   python web/server.py --port 8865
"""
from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from claude_webui.healthz import healthz_response

from journal_search import JournalFTS
from journal_semantic import JournalSemantic, record_key

NAMESPACE = "legion.claude-journal"
_RRF_K = 60  # reciprocal-rank-fusion constant

# ── tolerant-parse constants (from Phase 0 audit) ──────────────────────────
_TS_FIELDS = ("timestamp", "created", "date")          # alias chain → ts
_AUTHOR_FIELDS = ("author", "persona")                 # alias chain → author
_RE_DATEPATH = re.compile(r"/(\d{4})/(\d{2})/(\d{2})/")
_RE_HHMM = re.compile(r"^(\d{2})-(\d{2})-")             # filename "HH-MM-slug.md"
_RE_YMD = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")       # filename "YYYY-MM-DD-slug.md"
_RE_H1 = re.compile(r"^#\s+(.+)$", re.M)
_RE_ISO_LIKE = re.compile(r"^\d{4}-\d{2}-\d{2}")       # guard: reject free-text ts
_RE_FENCE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)
_RE_MDSYNTAX = re.compile(r"[#*_`>\[\]()!-]|https?://\S+")
_EXCERPT_LEN = 200
_FEED_DEFAULT_LIMIT = 50
_LIST_DEFAULT_LIMIT = 200


def _iso_from_parts(y: int, mo: int, d: int, hh: int = 0, mm: int = 0) -> str:
    try:
        return datetime(y, mo, d, hh, mm, tzinfo=timezone.utc).isoformat()
    except ValueError:
        return datetime(y, mo, d, tzinfo=timezone.utc).isoformat()


def _norm_author(raw: str) -> str:
    """Lowercase, strip parentheticals/quotes — 'Matt (Chief…)' → 'matt'."""
    raw = re.sub(r"\(.*?\)", "", raw or "").strip().strip("\"'")
    raw = raw.split(",")[0].split("(")[0].strip()
    return raw.lower() or "unknown"


def _slug_to_title(name: str) -> str:
    name = re.sub(r"\.md$", "", name)
    name = _RE_HHMM.sub("", name)
    name = _RE_YMD.sub("", name).lstrip("-")
    name = name.replace("-", " ").replace("_", " ").strip()
    return name[:1].upper() + name[1:] if name else "(untitled)"


class JournalAccessor:
    """Read-through accessor over the journal markdown corpus."""

    namespace = NAMESPACE

    def __init__(self, data_root: Path | None = None) -> None:
        if data_root is None:
            data_root = Path.home() / ".claude" / "local" / "journal"
        self.root = data_root
        self._cache: list[dict[str, Any]] | None = None
        self._cache_sig: tuple | None = None
        self._by_id: dict[str, dict[str, Any]] | None = None
        self._key_index: dict[str, list[str]] | None = None
        self._fts = JournalFTS(self._load, self.signature)
        self._sem = JournalSemantic()

    # ── parsing ────────────────────────────────────────────────────────────

    def _parse_file(self, path: Path) -> dict[str, Any]:
        relpath = str(path.relative_to(self.root))
        parts = path.relative_to(self.root).parts
        top = parts[0] if parts else ""
        name = path.name

        try:
            text = path.read_text(errors="replace")
        except Exception:
            text = ""

        fm: dict[str, Any] = {}
        body = text
        has_fm = False
        m = _RE_FENCE.match(text)
        if m:
            has_fm = True
            try:
                parsed = yaml.safe_load(m.group(1))
                if isinstance(parsed, dict):
                    fm = parsed
            except Exception:
                fm = {}
            body = text[m.end():]

        # author — top-level dir is the clean signal (general rule).
        # Legacy `2026/` flat tree has no author dir → frontmatter fallback.
        if top == "2026" or not parts[:-1]:
            author = "unknown"
            for f in _AUTHOR_FIELDS:
                if fm.get(f):
                    author = _norm_author(str(fm[f]))
                    break
            if author == "unknown":
                author = "legion"
        else:
            author = top.lower()

        # source_class
        fm_author_raw = ""
        for f in _AUTHOR_FIELDS:
            if fm.get(f):
                fm_author_raw = str(fm[f]).lower()
                break
        tags_raw = fm.get("tags") or []
        if isinstance(tags_raw, str):
            tags_raw = [tags_raw]
        tags = sorted({
            ("ventures" if str(t).lower() == "venture" else str(t).lower())
            for t in tags_raw if t
        })
        if top == "transcripts":
            source_class = "transcript"
        elif top == "2026":
            source_class = "legacy"
        elif fm_author_raw == "pipeline-watch" or "alert" in tags:
            source_class = "pipeline-alert"
        else:
            source_class = "journal"

        # ts — frontmatter alias → path → filename → mtime
        ts = ""
        for f in _TS_FIELDS:
            v = fm.get(f)
            if v and _RE_ISO_LIKE.match(str(v).strip()):
                ts = str(v).strip()
                break
        if not ts:
            dm = _RE_DATEPATH.search("/" + relpath)
            if dm:
                y, mo, d = map(int, dm.groups())
                hh = mm = 0
                hm = _RE_HHMM.match(name)
                if hm:
                    hh, mm = int(hm.group(1)), int(hm.group(2))
                ts = _iso_from_parts(y, mo, d, hh, mm)
        if not ts:
            ym = _RE_YMD.match(name)
            if ym:
                ts = _iso_from_parts(*map(int, ym.groups()))
        if not ts:
            try:
                ts = datetime.fromtimestamp(
                    path.stat().st_mtime, tz=timezone.utc
                ).isoformat()
            except Exception:
                ts = ""

        # title — frontmatter → first H1 → slug
        title = str(fm.get("title") or "").strip()
        if not title:
            hm = _RE_H1.search(body)
            title = hm.group(1).strip() if hm else _slug_to_title(name)

        excerpt = _RE_MDSYNTAX.sub("", body).strip()
        excerpt = re.sub(r"\s+", " ", excerpt)[:_EXCERPT_LEN]

        return {
            "id": hashlib.sha1(relpath.encode()).hexdigest()[:12],
            "path": str(path),
            "relpath": relpath,
            "author": author,
            "source_class": source_class,
            "ts": ts,
            "title": title,
            "tags": tags,
            "body_md": body,
            "excerpt": excerpt,
            "has_fm": has_fm,
        }

    def _load(self) -> list[dict[str, Any]]:
        sig = self.signature()
        if self._cache is not None and sig == self._cache_sig:
            return self._cache
        records = [
            self._parse_file(p)
            for p in self.root.rglob("*.md")
            if p.is_file()
        ]
        records.sort(key=lambda r: r["ts"], reverse=True)
        self._cache, self._cache_sig = records, sig
        self._by_id = {r["id"]: r for r in records}
        key_index: dict[str, list[str]] = {}
        for r in records:
            k = record_key(r)
            if k:
                key_index.setdefault(k, []).append(r["id"])
        self._key_index = key_index
        return records

    # ── filtering ────────────────────────────────────────────────────────────

    @staticmethod
    def _matches(rec: dict[str, Any], params: dict[str, Any]) -> bool:
        author = params.get("author")
        if author and author != "all" and rec["author"] != author:
            return False
        sc = params.get("source_class")
        if sc and sc != "all" and rec["source_class"] != sc:
            return False
        tag = params.get("tag")
        if tag and tag not in rec["tags"]:
            return False
        date_from = params.get("from")
        if date_from and rec["ts"] < date_from:
            return False
        date_to = params.get("to")
        if date_to and rec["ts"] > date_to:
            return False
        md = params.get("md")  # "MM-DD" on-this-day filter
        if md and rec["ts"][5:10] != md:
            return False
        # NOTE: free-text `q` is handled by the search path (_search_ranked),
        # not here — _matches applies structured facets only.
        return True

    @staticmethod
    def _strip_body(rec: dict[str, Any]) -> dict[str, Any]:
        """List/feed payloads omit body_md (keep responses small)."""
        return {k: v for k, v in rec.items() if k != "body_md"}

    # ── search (FTS5 + optional semantic, RRF-fused) ────────────────────────

    def _search_ranked(self, query: str, mode: str) -> list[dict[str, Any]]:
        """Return records in relevance order with an attached `snippet`.

        mode="text"   → FTS5 only.
        mode="hybrid" → FTS5 ⊕ semantic via reciprocal-rank fusion; degrades
                        to FTS5 (and FTS5 degrades to substring) on failure.
        """
        self._load()  # ensure id + key indexes populated
        by_id = self._by_id or {}

        fts_hits = self._fts.search(query, limit=200)
        fts_rank = {h["id"]: h["rank"] for h in fts_hits}
        snippets = {h["id"]: h["snippet"] for h in fts_hits if h["snippet"]}

        sem_rank: dict[str, int] = {}
        if mode == "hybrid":
            keys = self._sem.search_keys(query, limit=80)
            ki = self._key_index or {}
            pos = 0
            for k in keys:
                for rid in ki.get(k, []):
                    sem_rank.setdefault(rid, pos)
                    pos += 1

        # FTS unavailable AND no semantic → substring fallback over excerpt.
        if not fts_rank and not sem_rank:
            ql = query.casefold()
            ranked = [
                r for r in (self._cache or [])
                if ql in (r["title"] + " " + r["excerpt"] + " "
                          + " ".join(r["tags"])).casefold()
            ]
            return [{**self._strip_body(r), "snippet": ""} for r in ranked]

        scores: dict[str, float] = {}
        for rid, rk in fts_rank.items():
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (_RRF_K + rk)
        for rid, rk in sem_rank.items():
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (_RRF_K + rk)

        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        out = []
        for rid, _ in ordered:
            rec = by_id.get(rid)
            if rec is None:
                continue
            out.append({**self._strip_body(rec), "snippet": snippets.get(rid, "")})
        return out

    @staticmethod
    def _paginate(params: dict[str, Any], default_limit: int) -> tuple[int, int]:
        try:
            limit = int(params.get("limit") or default_limit)
        except (TypeError, ValueError):
            limit = default_limit
        try:
            offset = int(params.get("offset") or 0)
        except (TypeError, ValueError):
            offset = 0
        return limit, offset

    def _query(self, params: dict[str, Any], default_limit: int) -> list[dict[str, Any]]:
        """Unified list/feed core: search-ranked when `q`, else chrono."""
        limit, offset = self._paginate(params, default_limit)
        q = (params.get("q") or "").strip()
        if q:
            mode = "hybrid" if params.get("mode") == "hybrid" else "text"
            ranked = self._search_ranked(q, mode)
            faceted = [r for r in ranked if self._matches(r, params)]
            return faceted[offset:offset + limit]
        recs = [self._strip_body(r) for r in self._load() if self._matches(r, params)]
        return recs[offset:offset + limit]

    # ── Accessor protocol ──────────────────────────────────────────────────

    def list(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        return self._query(params, _LIST_DEFAULT_LIMIT)

    def feed(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        # Default feed = reflective journal only unless caller overrides.
        p = dict(params)
        p.setdefault("source_class", "journal")
        return self._query(p, _FEED_DEFAULT_LIMIT)

    def detail(self, item_id: str) -> dict[str, Any]:
        recs = self._load()
        idx = next((i for i, r in enumerate(recs) if r["id"] == item_id), None)
        if idx is None:
            return {"error": "not found", "id": item_id}
        rec = dict(recs[idx])
        # recs are sorted newest-first → next-newer is idx-1, prev-older is idx+1
        rec["newer"] = self._strip_body(recs[idx - 1]) if idx > 0 else None
        rec["older"] = (
            self._strip_body(recs[idx + 1]) if idx + 1 < len(recs) else None
        )
        return rec

    def stats(self) -> dict[str, Any]:
        recs = self._load()
        by_author: dict[str, int] = {}
        by_class: dict[str, int] = {}
        by_day: dict[str, int] = {}
        by_hour = [0] * 24
        by_weekday = [0] * 7   # 0=Mon … 6=Sun
        tag_counts: dict[str, int] = {}
        tag_by_month: dict[str, dict[str, int]] = {}  # tag → {YYYY-MM: n}
        for r in recs:
            by_author[r["author"]] = by_author.get(r["author"], 0) + 1
            by_class[r["source_class"]] = by_class.get(r["source_class"], 0) + 1
            ts = r["ts"]
            day = ts[:10]
            if day:
                by_day[day] = by_day.get(day, 0) + 1
            month = ts[:7]
            # hour
            if len(ts) >= 13 and ts[11:13].isdigit():
                by_hour[int(ts[11:13]) % 24] += 1
            # weekday
            try:
                by_weekday[datetime.fromisoformat(day).weekday()] += 1
            except (ValueError, TypeError):
                pass
            for t in r["tags"]:
                tag_counts[t] = tag_counts.get(t, 0) + 1
                if len(month) == 7:
                    tag_by_month.setdefault(t, {})[month] = (
                        tag_by_month.setdefault(t, {}).get(month, 0) + 1
                    )
        journal_n = by_class.get("journal", 0)
        top_tags = sorted(tag_counts.items(), key=lambda kv: kv[1], reverse=True)[:40]

        # tag_trends: top 8 tags × sorted months → stacked-stream series.
        trend_tags = [t for t, _ in top_tags[:8]]
        months = sorted({m for t in trend_tags for m in tag_by_month.get(t, {})})
        tag_trends = {
            "months": months,
            "series": [
                {"tag": t, "counts": [tag_by_month.get(t, {}).get(m, 0) for m in months]}
                for t in trend_tags
            ],
        }
        return {
            "key_metric": journal_n,
            "key_metric_label": "journal entries",
            "total": len(recs),
            "by_author": by_author,
            "by_source_class": by_class,
            "by_day": by_day,
            "by_hour": by_hour,
            "by_weekday": by_weekday,
            "top_tags": top_tags,
            "tag_trends": tag_trends,
            "latest": recs[0]["ts"] if recs else None,
        }

    def healthz(self) -> dict[str, Any]:
        t0 = time.perf_counter()
        ok = self.root.is_dir()
        s = self.stats() if ok else {"key_metric": 0, "key_metric_label": "journal entries"}
        resp = healthz_response(
            namespace=NAMESPACE,
            database=str(self.root),
            elapsed_ms=(time.perf_counter() - t0) * 1000.0,
            ok=ok,
        )
        resp["stats"] = {
            "key_metric": s["key_metric"],
            "key_metric_label": s["key_metric_label"],
        }
        return resp

    def signature(self) -> tuple:
        """Cheap live-refresh signature — stat DIRECTORIES only, not 4.5k files.

        A new entry bumps its parent dir's mtime, so directory mtimes +
        total dir count are sufficient to detect change without an O(files)
        stat sweep every poll.
        """
        sig: list[tuple[str, int]] = []
        if self.root.is_dir():
            for d in sorted(self.root.rglob("*")):
                if d.is_dir():
                    try:
                        sig.append((str(d), d.stat().st_mtime_ns))
                    except OSError:
                        continue
            try:
                sig.append((str(self.root), self.root.stat().st_mtime_ns))
            except OSError:
                pass
        return tuple(sig)
