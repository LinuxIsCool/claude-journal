---
name: journal-synthesizer
description: >
  Synthesize journal entries into summaries. Use when creating daily summaries, monthly overviews, yearly narratives, or on-demand topic synthesis.
  Reads child entries and produces compressed summaries that preserve key details.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Journal Synthesizer

Compress many entries into layered summaries. Each level preserves key details (decisions, deadlines, names, numbers) while abstracting narrative flow.

**Rule**: Never truncate. Compress. Every decision, name, and number from child entries should be findable in the parent summary.

## Synthesis Hierarchy

```
Atomic entries (HH-MM-slug.md)
    ↓ synthesize into
Daily summary (YYYY-MM-DD.md) — in the DD/ directory
    ↓ synthesize into
Monthly summary (YYYY-MM.md) — in the MM/ directory
    ↓ synthesize into
Yearly summary (YYYY.md) — in the YYYY/ directory
```

## Daily Synthesis

**Trigger**: End of day, or on request for any date.

**Process:**
1. `Glob: ~/.claude/local/journal/{machine}/YYYY/MM/DD/*.md` — get all atomic entries for the day (exclude any existing YYYY-MM-DD.md)
2. Read each entry's frontmatter and content
3. Produce a daily summary

**Output file**: `~/.claude/local/journal/{machine}/YYYY/MM/DD/YYYY-MM-DD.md`

```markdown
---
title: "Daily Summary — March 9, 2026"
created: {now}
machine: {machine}
author: {author}
description: "Summary of {N} entries on {date}"
summary: "{2-3 sentences capturing the day's arc}"
tags: [{union of all entry tags}]
type: daily
entries_summarized: {N}
date_range:
  start: {date}
  end: {date}
themes: [{extracted themes}]
parent_monthly: "{YYYY-MM}"
parent_yearly: "{YYYY}"
---

# Daily Summary — {Month Day, Year}

## Arc
{1-2 paragraph narrative of the day — what happened, what it means}

## Entries
{For each atomic entry, one line:}
- **{HH:MM}** — [{title}]({filename}): {summary from frontmatter}

## Key Decisions
{Bulleted list of decisions made today, with rationale}

## Ventures Touched
{List of ventures referenced across today's entries with brief status}

## Open Threads
{Things started but not finished, questions raised, items for tomorrow}
```

## Monthly Synthesis

**Trigger**: End of month, or on request.

**Process:**
1. `Glob: ~/.claude/local/journal/{machine}/YYYY/MM/*/YYYY-MM-*.md` — get daily summaries
2. Also scan `Glob: ~/.claude/local/journal/{machine}/YYYY/MM/**/*.md` for atomic entries without daily summaries
3. Read and synthesize

**Output file**: `~/.claude/local/journal/{machine}/YYYY/MM/YYYY-MM.md`

```markdown
---
title: "Monthly Summary — March 2026"
created: {now}
machine: {machine}
author: {author}
description: "Summary of {month}"
summary: "{3-4 sentences capturing the month's arc}"
tags: [{top tags from the month}]
type: monthly
entries_summarized: {total atomic entries}
date_range:
  start: YYYY-MM-01
  end: YYYY-MM-{last day}
themes: [{major themes}]
parent_yearly: "{YYYY}"
---

# Monthly Summary — {Month Year}

## Narrative
{2-3 paragraph narrative of the month}

## By Week
### Week of {date}
{brief summary}
### Week of {date}
{brief summary}

## Key Themes
{Major themes that emerged, with entry references}

## Venture Progress
{Per-venture summary of movement during this month}

## Decisions & Milestones
{Significant decisions and milestones reached}

## Metrics
- Entries: {count}
- Days journaled: {count} / {days in month}
- Most active day: {date} ({count} entries)
- Top tags: {tag1} ({count}), {tag2} ({count}), ...
```

## Yearly Synthesis

**Trigger**: End of year, or on request.

**Process:**
1. Read all monthly summaries for the year
2. Read yearly summary from previous year if it exists (for continuity)
3. Synthesize into narrative arc

**Output file**: `~/.claude/local/journal/{machine}/YYYY/YYYY.md`

```markdown
---
title: "Yearly Summary — 2026"
created: {now}
machine: {machine}
author: {author}
description: "The year in review"
summary: "{4-5 sentences capturing the year}"
tags: [{defining tags of the year}]
type: yearly
entries_summarized: {total entries}
date_range:
  start: YYYY-01-01
  end: YYYY-12-31
themes: [{year's defining themes}]
---

# {Year} in Review

## Narrative Arc
{The story of this year in 3-5 paragraphs}

## By Quarter
### Q1 (Jan-Mar)
### Q2 (Apr-Jun)
### Q3 (Jul-Sep)
### Q4 (Oct-Dec)

## Defining Themes
{3-5 themes with supporting evidence}

## Ventures
{Lifecycle of each venture that was active during the year}

## Growth
{How capabilities, knowledge, or circumstances changed}

## Numbers
- Total entries: {count}
- Days journaled: {count} / 365
- Ventures active: {count}
- Machines used: {list}
```

## On-Demand Topic Synthesis

**Trigger**: "Synthesize everything about X" or "What do I know about X?"

**Process:**
1. `Grep: "{topic}" in ~/.claude/local/journal/ glob="*.md"` — find all mentions
2. Read matching entries
3. Produce a topic synthesis as an atomic entry with `session_type: research`

This creates a regular atomic entry (not a summary entry) — it's a new piece of knowledge derived from existing entries.

## Synthesis Guidelines

1. **Preserve specifics**: Decisions, deadlines, names, numbers, URLs — these must survive compression
2. **Abstract narrative**: "Spent 3 hours debugging auth" → "Fixed auth bug (root cause: token expiry race condition)"
3. **Surface patterns**: If the same theme appears across entries, name it explicitly
4. **Link back**: Always reference source entries by filename or date
5. **Don't editorialize**: Summarize what was written, not what should have been written
6. **Honest metrics**: If only 3 of 30 days were journaled, say so — don't present sparse data as comprehensive

## Common Mistakes

1. **Synthesizing without reading**: Always read all child entries before writing a summary
2. **Losing specifics**: "Made progress on ventures" loses all information. Name the ventures and what happened.
3. **Creating summary when one exists**: Check if YYYY-MM-DD.md already exists before creating. If it does, update or replace.
4. **Wrong file location**: Daily summaries go IN the day directory, monthly summaries go IN the month directory, yearly IN the year directory.
