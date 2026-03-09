# claude-journal

Atomic journaling plugin. Capture → Synthesize → Reflect → Plan.

## Quick Start
- `/journal` — create or open today's journal
- `/journal note <title>` — quick atomic entry
- `/journal reflect` — end-of-week reflection
- `/journal plan` — weekly planning session
- `/journal browse` — search and navigate entries

## Data Location
Journal entries: `~/.claude/local/journal/{machine}/YYYY/MM/DD/HH-MM-slug.md`
Config: `~/.claude/local/journal/config.yml`

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
