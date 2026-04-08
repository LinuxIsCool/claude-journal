# Claude Code Journal Plugin

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An atomic journaling system for Claude Code. Capture thoughts, decisions, and events as small markdown entries that synthesize upward into daily, monthly, and yearly summaries — a layered knowledge base that grows with every session.

Claude Code sessions are ephemeral. Even with full transcripts, the *meaning* of what happened — the decisions made, the shape of your thinking, the patterns across weeks — gets lost in the noise. This plugin gives you a deliberate place to write those things down, and the tools to find them later.

---

## Features

- **Atomic entries** — one idea, decision, or event per file. Small, composable, Zettelkasten-style.
- **Synthesis upward** — atomics roll up into daily → monthly → yearly summaries, each layer compressing while preserving decisions, names, numbers, and deadlines.
- **Machine-scoped** — entries are tagged by host, so you can journal across multiple machines and keep provenance.
- **Rich frontmatter** — tags, session type, related entries, venture links, URLs, and back-references to past events.
- **Five specialist subskills** — writer, planner, reflector, browser, synthesizer. Each is a focused workflow you invoke with a single command.
- **Scribe agent** — a reflective agent for long, multi-turn journaling and planning sessions.
- **Session hooks** — gentle start-of-session nudges and end-of-session offers to capture what just happened.
- **Plain markdown on disk** — no database, no lock-in. Every entry is a file you can read, edit, grep, and back up with any tool.

---

## Install

```
/plugin marketplace add linuxiscool/claude-journal
/plugin install claude-journal
```

Or clone and install locally:

```bash
git clone https://github.com/LinuxIsCool/claude-journal ~/.claude/plugins/claude-journal
```

Restart your Claude Code session. The `/journal` command will be available.

---

## Quick Start

```
/journal                         # show today's entries, or create the first one
/journal note <title>            # quick atomic entry with a title
/journal <free text>             # journal about whatever you type
/journal reflect                 # end-of-day / weekly reflection session
/journal plan                    # weekly or daily planning session
/journal browse [query]          # search past entries (by date, tag, venture, keyword)
/journal stats                   # counts, streaks, and tag frequencies
/journal synthesize [period]     # roll atomics up into a daily/monthly/yearly summary
/journal today                   # same as bare /journal
```

Examples:

```
/journal note shipped claude-logging v1.0.0
/journal browse tag:immigration
/journal browse venture:salish-sea-dreaming
/journal synthesize this week
/journal reflect
```

---

## How It's Organized

```
~/.claude/local/journal/
├── config.yml
└── {machine}/
    └── YYYY/
        ├── YYYY.md                    # yearly summary
        └── MM/
            ├── YYYY-MM.md              # monthly summary
            └── DD/
                ├── YYYY-MM-DD.md       # daily summary
                └── HH-MM-slug.md       # atomic entry
```

Every entry lives in **today's** folder — even if it references a past event (use the `references_date` frontmatter field for that). Filenames use the creation time (`HH-MM-slug.md`), so entries sort chronologically inside each day.

### Entry frontmatter

Atomic entries carry rich YAML frontmatter so they're easy to query, cross-reference, and synthesize:

```yaml
---
title: "Scope — Subtitle"              # required; em dash separator
created: 2026-04-08T12:30:00-07:00     # required; ISO 8601 with timezone
machine: legion                         # required
author: legion                          # required
description: "One-line description"
summary: "2–3 sentence summary"
tags: [roadmap, planning]
session_type: strategic                 # strategic | design | debug | reflect | plan | note | meeting | research
related: [other-entry-slug, 2026-04-07]
ventures: [salish-sea-dreaming]
urls: []
references_date: null                   # set if documenting a past event
type: atomic                            # atomic | daily | monthly | yearly
parent_daily: "2026-04-08"
parent_monthly: "2026-04"
parent_yearly: "2026"
---
```

Daily, monthly, and yearly summaries share the same schema with `type` set accordingly.

---

## The Subskills

The `/journal` command dispatches to one of five specialist subskills based on the argument:

### `@journal-writer`
Captures a new atomic entry. Handles slug generation, filename, directory creation, and frontmatter. Use for any "I want to note X" moment.

### `@journal-planner`
Forward-looking. Daily priorities, weekly intentions, venture planning, goal setting. Reads recent entries and any active ventures to make the planning session grounded in context. Frameworks: 1-3-5 Rule, Time Boxing, Energy Mapping.

### `@journal-reflector`
Backward-looking. End-of-day review, weekly retrospective, milestone reflection. Frameworks: Start-Stop-Continue, Rose-Thorn-Bud, 4Ls, Energy Audit.

### `@journal-browser`
Search and navigation. Query by date (`today`, `this week`, `march`, `2026`), tag (`tag:immigration`), venture (`venture:indigenomicsai`), or keyword. Also provides stats mode: counts, streaks, tag frequencies.

### `@journal-synthesizer`
Rolls atomics upward. Aggregates the atomics in a given period into a summary entry (daily, monthly, or yearly), compressing prose while preserving decisions, names, numbers, and links. Safe to re-run — it replaces the existing summary.

### `@scribe` (agent)
A dedicated journaling agent for longer, reflective, multi-turn sessions. Useful when you want a conversation partner rather than a one-shot skill invocation.

---

## Session Hooks

Two optional hooks are registered by default:

- **`SessionStart`** — a gentle nudge showing today's entry count and offering to open the journal.
- **`Stop`** — an end-of-session offer to capture what just happened.

Both are non-blocking. Disable them by editing `plugin.json` if you prefer a quieter experience.

---

## Philosophy

**Atomic-first.** One idea per file. If you're writing about two things, write two entries. The atomic unit is what makes synthesis work.

**Synthesis, not summary.** The daily/monthly/yearly layers are not just concatenations — they're compressions that preserve what matters (decisions, names, numbers, deadlines) and drop the rest. You should be able to read the yearly summary in five minutes and remember the year.

**Plain files, forever.** Every entry is a markdown file on your disk. No database, no cloud, no vendor. You can grep it, back it up, sync it, and read it on any machine a decade from now.

**Machine-scoped provenance.** Every entry knows which host it was written from. If you journal from a laptop and a workstation, the entries don't collide — they coexist under their machine name.

---

## Configuration

`~/.claude/local/journal/config.yml`:

```yaml
default_machine: legion
default_author: legion
timezone: America/Vancouver
```

If the config doesn't exist, sensible defaults are used.

---

## Data Location

All journal data lives under `~/.claude/local/journal/`. It's yours — never uploaded, never shared. Back it up like you'd back up any other plain-text notes directory.

---

## Contributing

Issues and pull requests welcome. This is a personal tool first, but the patterns are general and contributions that keep it simple and file-based are appreciated.

---

## License

MIT — see [LICENSE](LICENSE).
