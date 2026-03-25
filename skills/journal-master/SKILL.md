---
name: journal-master
description: >
  Atomic journaling system — capture ideas, decisions, and events as small entries that synthesize into daily, monthly, and yearly summaries.
  Use when the user wants to journal, write notes, reflect on work, plan forward, browse past entries, or synthesize patterns.
  Also triggers when significant work occurs and should be captured, or when the user mentions reviewing what happened.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Journal Master

Atomic journaling for Claude Code. Every thought, decision, or event is an **atomic entry** — a small markdown file with rich frontmatter. Atomics synthesize upward into daily, monthly, and yearly summaries, creating a layered knowledge base.

## Philosophy

**Atomic-first**: The primary unit is a single entry capturing one idea, decision, event, or reflection. Never combine unrelated content into one entry.

**Synthesis upward**: Daily summaries aggregate atomics. Monthly summaries aggregate dailies. Yearly summaries aggregate monthlies. Each layer compresses while preserving key details (decisions, deadlines, names, numbers).

**Machine-scoped**: Entries are scoped by machine name, giving provenance and enabling multi-machine journaling.

**Venture-linked**: Entries can reference active ventures from claude-ventures, creating bidirectional context.

## Directory Structure

```
~/.claude/local/journal/
├── config.yml
├── {machine}/
│   └── YYYY/
│       ├── YYYY.md              # Yearly summary
│       └── MM/
│           ├── YYYY-MM.md       # Monthly summary
│           └── DD/
│               ├── YYYY-MM-DD.md  # Daily summary
│               └── HH-MM-slug.md  # Atomic entry
```

## Entry Frontmatter Schema

```yaml
---
title: "Scope — Subtitle"               # Required. Always use em dash (—) as separator.
created: 2026-03-09T12:11:00-07:00     # Required, ISO 8601 with timezone
machine: legion                         # Required
author: legion                          # Required (legion | mothership | shawn)
description: "One-line description"     # Recommended
summary: "2-3 sentence summary"         # Recommended
tags: [roadmap, planning]               # Recommended
session_type: strategic                 # strategic | design | debug | reflect | plan | note | meeting | research
related: [other-entry, 2026-03-08]     # Cross-references
ventures: [salish-sea-dreaming]         # Connected ventures
urls: []                                # URLs mentioned in content
references_date: null                   # If documenting a past event
type: atomic                            # atomic | daily | monthly | yearly
parent_daily: "2026-03-09"
parent_monthly: "2026-03"
parent_yearly: "2026"
---
```

## Subskills

### @journal-writer
**Trigger**: Creating new journal entries, capturing ideas, noting decisions, recording events.
Creates atomic entries with proper frontmatter, slug filenames, and directory structure.

### @journal-planner
**Trigger**: Planning forward — daily priorities, weekly intentions, venture planning, goal setting.
Reads recent entries and venture data to provide informed planning. Frameworks: 1-3-5 Rule, Time Boxing, Energy Mapping.

### @journal-reflector
**Trigger**: Looking backward — end-of-day review, weekly retrospective, milestone reflection, venture retrospective.
Facilitates structured reflection. Frameworks: Start-Stop-Continue, Rose-Thorn-Bud, 4Ls, Energy Audit.

### @journal-browser
**Trigger**: Searching, navigating, or exploring past entries. Finding by date, tag, venture, or keyword. Statistics.
Query patterns: `browse today`, `browse this week`, `browse tag:X`, `browse venture:X`, `search keyword`, `stats`.

### @journal-synthesizer
**Trigger**: Creating summaries — daily, monthly, yearly, or on-demand topic synthesis.
Reads child entries and produces compressed summaries that preserve key details.

## Routing

When invoked without specific context:
1. Check if today has entries → show them
2. If no entries today → offer to create one
3. If the user's message implies a specific subskill → route there
4. If unclear → ask what they'd like to do

## Config

`~/.claude/local/journal/config.yml`:
```yaml
default_machine: legion
default_author: legion
journal_root: ~/.claude/local/journal
timezone: America/Vancouver
nudge_after_days: 3
stop_hook_threshold_minutes: 30
```
