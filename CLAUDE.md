# claude-journal

Atomic journaling plugin. Capture → Synthesize → Reflect → Plan.

## Quick Start
- `/journal` — create or open today's journal
- `/journal note <title>` — quick atomic entry
- `/journal reflect` — end-of-week reflection
- `/journal plan` — weekly planning session
- `/journal browse` — search and navigate entries

## Data Location
Journal plugin root: `~/.claude/local/journal/`
Default atomic entry layout: `~/.claude/local/journal/{machine}/YYYY/MM/DD/HH-MM-slug.md`
Config: `~/.claude/local/journal/config.yml`

The canonical operational contract is the plugin root:

- `~/.claude/local/journal/`

The machine/date tree is the journal plugin's internal default layout beneath that root.

- Do not create parallel journal hierarchies outside the journal plugin root for the same entries.
- Because `~/.claude/local/` may be symlinked into a version-controlled backing store, writing to the canonical `.claude/local/journal/` root is already sufficient.

## Entry Types
- **atomic** — primary unit, one idea/event/decision per entry
- **daily/monthly/yearly** — synthesized summaries, auto-generated from atomics

## Conventions
- All entries go in TODAY's folder (use `references_date` for past events)
- Filenames: `HH-MM-slug.md` (time of creation, not time of event)
- Summaries: `YYYY-MM-DD.md`, `YYYY-MM.md`, `YYYY.md`
- Always include: title, created, machine, author, tags, summary
- Link to ventures via `ventures:` frontmatter field
- Link to other entries via `related:` field and body wikilinks

## Progressive Disclosure Role

This file states the adapter-visible contract for Claude Code.

The deeper pattern is:

- machine-wide storage root conventions should also exist in runtime-loaded doctrine
- the master journal skill defines the journaling domain contract and routing behavior
- subskills implement specialized workflows like writing, browsing, reflection, planning, and synthesis

Do not redefine the journal root differently in subskills or commands.

## Data Schema

No SQLite. File-based only.

### File Layout

```
~/.claude/local/journal/
└── {machine}/                    # e.g. "legion"
    └── YYYY/
        └── MM/
            └── DD/
                ├── HH-MM-slug.md           # atomic entry
                ├── YYYY-MM-DD.md           # daily summary
            └── YYYY-MM.md                  # monthly summary
        └── YYYY.md                         # yearly summary
```

### Frontmatter Contract

```yaml
---
title: "2026-04-13 — Nightly Integration"       # required
created: 2026-04-13T03:01:19-07:00               # required, ISO 8601
machine: legion                                   # required
author: legion                                    # required
description: "..."                                # optional
summary: "..."                                    # optional
tags: [rhythm, nightly-integration]               # required (may be empty)
session_type: brief                               # optional
related: []                                       # optional, wikilinks
ventures: []                                      # optional, venture slugs
urls: []                                          # optional
references_date: null                             # optional, past event date
type: atomic                                      # optional (atomic|daily|monthly|yearly)
parent_daily: "2026-04-13"                        # optional, synthesis linking
parent_monthly: "2026-04"                         # optional, synthesis linking
---
```

### Canonical Count

The SessionStart hook (`session-recent-entries.py`) finds entries via:

```python
JOURNAL_ROOT.rglob("*.md")  # all .md under ~/.claude/local/journal/
```

It filters hidden files (`.name.startswith(".")`) and sorts by mtime descending. There is no explicit exclusion of summary files from the count.
