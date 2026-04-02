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
