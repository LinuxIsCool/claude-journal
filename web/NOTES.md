# claude-journal webui — Phase 0 recon notes

> Task-4133. Audit run 2026-06-14 02:23 PDT. Read-only census of the journal corpus.
> Deliverable: corpus facts + **frozen record schema** + tolerant-parse rules for Phase 1.

## TL;DR

- **4,577** markdown files under `~/.claude/local/journal/` (symlinked root — use `find -L` / `rglob`).
- **97.6%** have a YAML frontmatter fence; the newest **112** entries (matt, 2026-06-12/13) do **not**.
- **Author is unreliable in frontmatter (43%) but clean from the top-level dir.** Infer from dir, normalize case.
- **Timestamp is reliably derivable from path (99%) + filename (86%)** even when frontmatter omits it.
- **No threading fields exist** (`thread`/`parent_id`/`id` = 0%). Drop thread-chaining from Phase 1; revisit via same-day/tag heuristics later.
- **Tags are rich and meaningful** (present 61%) → facets are viable.
- **Embeddings cover journal** (4,443 KOI bundles, 7,966 embedding rows in `embeddings_telus_e5_1024`) → semantic search viable in Phase 2.
- **Port 8865 is free** (nothing listening).

## Corpus census

| Metric | Value |
|---|---|
| Total `.md` files | 4,577 |
| With frontmatter fence | 4,465 (97.6%) |
| Without frontmatter | 112 (2.4%, all newest matt entries) |
| Date in path (`/YYYY/MM/DD/`) | 4,549 (99.4%) |
| Timestamp in filename (`HH-MM-` / `YYYY-MM-DD-`) | 3,924 (85.7%) |
| Read/parse errors | 0 |
| KOI journal bundles | 4,443 |
| Journal embedding rows (e5-1024) | 7,966 (chunked; >1 per bundle) |

### Top-level dirs = content classes (file counts)

| Dir | Files | Class |
|---|---|---|
| `legion/` | 1,857 | journal (persona: legion) |
| `matt/` | 1,797 | journal (persona: matt) |
| `transcripts/` | 712 | imported meeting transcripts — **separate class** |
| `2026/` | 180 | legacy flat dated entries |
| `darren/` | 16 | journal (persona: darren) |
| `bondometer/` | 14 | journal (persona: bondometer) |
| `last-7-days/` | 1 | rollup artifact — likely exclude |

Note: `pipeline-watch` shows up as an **author value** (205 entries) — automated alert entries
(e.g. "diarize-queue: plateau detected"). These are journal-class but a distinct `source_class`.

## Frontmatter field coverage (of the 4,465 fenced entries)

| Field | Coverage | Decision |
|---|---|---|
| `tags` | 60.7% | Use as facet; normalize lowercase |
| `title` | 60.2% | Alias source #1 for title |
| `author` | 43.0% | **Unreliable + inconsistent case** — prefer dir |
| `persona` | 39.9% | Alias for author |
| `timestamp` | 39.6% | Alias for ts |
| `type` | 39.0% | Optional → source_class hint |
| `date` | 38.3% | Alias for ts |
| `created` | 21.7% | Alias for ts |
| `ts` | 0% | not used |
| `thread` / `parent_id` / `id` | 0% | **Do not exist — no threading in corpus** |

### Author value mess (why we infer from dir)

Explicit author/persona values seen: `matt` (2077), `legion` (1311), `pipeline-watch` (205),
`codex` (31), `darren` (21), `bondometer` (14), `Matt` (9), `Darren (KOI protocol researcher)` (6),
`Codex` (5), `Legion` (5), `Matt (Chief of Staff, session matt:656)` (2), `legion (matt drafting)` (2)…
→ Same identity, many spellings. **Top-level dir is the clean signal.** Normalize: lowercase,
strip parentheticals.

### Tag vocabulary (sample, matt+legion)

`rhythm`(558) `alert`(289) `pipeline`(210) `ventures`(161) `checkpoint`(137) `venture`(134)
`infrastructure`(97) `architecture`(94) `indigenomics-ai`(75) `legion`(70) `voice`(63)
`code-review`(62) `regen-ai`(57) `session`(56) `bcrg`(56) `koi`(54) `milestone`(50)
`discourse`(47) `tmux`(44) `sysadmin`(44) … → strong faceting signal; `venture`/`ventures` need merge.

## FROZEN record schema (Phase 1 internal record)

```python
JournalRecord = {
  "id":           str,   # stable: sha1(relpath)[:12]
  "path":         str,   # absolute
  "relpath":      str,   # from journal root
  "author":       str,   # normalized from top-level dir; lowercase; fallback frontmatter author/persona
  "source_class": str,   # "journal" | "transcript" | "pipeline-alert" | "legacy"
  "ts":           str,   # ISO 8601; resolution order below
  "title":        str,   # resolution order below
  "tags":         list,  # frontmatter tags[], lowercased, deduped
  "body_md":      str,   # content below the fence (or whole file if unfenced)
  "excerpt":      str,   # first ~200 chars of plain text
  "has_fm":       bool,  # had a YAML fence
}
```

### Field-resolution (tolerant parse) rules

- **author** ← top-level dir name, lowercased (`matt`,`legion`,`darren`,`bondometer`,`transcripts`).
  For `2026/` legacy → fall back to frontmatter `author`/`persona`, else `legion`. Strip
  parentheticals, lowercase. Never hard-fail.
- **source_class** ← `transcript` if under `transcripts/`; `legacy` if under `2026/`;
  `pipeline-alert` if frontmatter `author`==`pipeline-watch` or `tags` contains `alert`;
  else `journal`.
- **ts** ← first available: frontmatter `timestamp` → `created` → `date` → parse path
  `/YYYY/MM/DD/` + filename leading `HH-MM` → parse filename leading `YYYY-MM-DD` → file mtime.
- **title** ← frontmatter `title` → first `^# ` heading in body → filename slug (strip
  date/time prefix, de-kebab).
- **tags** ← frontmatter `tags[]`, lowercase, dedupe. Merge `venture`→`ventures` at read time.
- **threading** ← **deferred.** No fields exist. Phase 3+ may derive "related" from same-day +
  shared-tag + embedding neighbors. Roadmap idea #8 (thread chaining) downgraded accordingly.

### Parser must handle

1. **Unfenced entries** (112, newest matt): no `---`. Treat whole file as `body_md`,
   `has_fm=False`, infer all fields from path/filename/headings.
2. **Inconsistent FM field names** via the alias chains above.
3. **Symlinked root** — resolve with `rglob`/`find -L`.
4. **Mixed content classes** — surface `source_class` as a filter; default feed can hide
   `transcript` + `pipeline-alert` behind a toggle so reflective journal stays primary.

## Decisions locked for Phase 1

- Port **8865**, bind `127.0.0.1`, Mode A standalone (mirror `claude-schedule/web/server.py`).
- Read-only: `mutation_catalog=None`.
- Author axis = 5 personas + `transcripts`; default feed = `source_class=journal` only,
  toggles to reveal transcript/alert/legacy.
- No thread-chaining in Phase 1 (no data). Prev/next = temporal only.
- Semantic search (Phase 2) backed by existing `embeddings_telus_e5_1024`; degrade to FTS-only
  when an entry has no vector.

## Open questions surfaced (for Shawn)

1. Should `transcripts/` (712) live in the journal webui at all, or stay in claude-transcripts? (Lean: show, but off by default.)
2. Freeze a forward frontmatter contract for the scribe (so coverage stops drifting), or commit to permanent tolerant parsing? (Lean: do both — tolerant reader + nudge scribe to always emit `author`+`timestamp`+`tags`.)
3. Mode A standalone only, or also mount as `:8800/journal/` satellite under the unified platform?
