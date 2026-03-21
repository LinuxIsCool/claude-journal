---
name: journal-writer
description: >
  Create atomic journal entries. Use when capturing ideas, decisions, events, session summaries, or any content that should be preserved as a journal entry.
  Handles frontmatter generation, slug creation, directory structure, and cross-linking.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Journal Writer

Create atomic journal entries — one idea, decision, or event per entry.

## Entry Creation Process

### 1. Determine Entry Details

**Session ID**: Every journal entry should include the `session_id` of the session that created it. This closes the provenance chain between sessions and journal entries.
- **How to obtain**: Read `~/.claude/projects/-home-shawn/.session_id` if it exists, OR check the `CLAUDE_SESSION_ID` environment variable, OR extract from the most recent session JSONL filename in `~/.claude/local/logging/-home-shawn/sessions/`
- **If unavailable**: Set to `null` — never block entry creation on missing session_id

**Primary source: the conversation context.** The user typically asks to journal about work that just happened in the current session. Use the full conversation history — not just the argument text — to construct a detailed, accurate entry. The argument text is a hint about what to focus on, not the content itself.

From the conversation context and user's input, extract:
- **Title**: Clear, descriptive (used in filename slug). **Always use em dash (—) as the separator** between scope/topic and subtitle. Never use colons, hyphens, or other separators in titles. Examples:
  - ✅ `"claude-dock Phase 7 — Activation v0.8.0"`
  - ✅ `"Venture Financial & Legal Standing — Setting the Foundation"`
  - ✅ `"graphiti_skills_repo.py — Code Review and Cleanup"`
  - ❌ `"claude-dock Phase 7: Activation"` (colon)
  - ❌ `"Code Review - Cleanup"` (hyphen as separator)
- **Description**: One-line summary
- **Summary**: 2-3 sentences capturing the essence
- **Tags**: Relevant topic tags (lowercase, hyphenated)
- **Session type**: strategic | design | debug | reflect | plan | note | meeting | research
- **Related**: Other entries, dates, or topics referenced
- **Ventures**: Any active ventures this relates to
- **URLs**: Any URLs mentioned in the content

### 2. Generate Filename

Format: `HH-MM-slug.md`

**Slug rules:**
- Lowercase the title
- Replace spaces with hyphens
- Remove special characters except hyphens
- Truncate to 50 characters at a word boundary
- Examples:
  - "Sovereign Life System Roadmap" → `12-11-sovereign-life-system-roadmap.md`
  - "Fixed the Auth Bug in API Gateway" → `15-22-fixed-the-auth-bug-in-api-gateway.md`
  - "Quick Note on Meeting with Arshia" → `09-45-quick-note-on-meeting-with-arshia.md`

**Time**: Use current time in the configured timezone (default: America/Vancouver).

### 3. Determine File Path

```
~/.claude/local/journal/{machine}/YYYY/MM/DD/HH-MM-slug.md
```

Where:
- `{machine}` comes from `config.yml` → `default_machine` (default: `legion`)
- `YYYY/MM/DD` is today's date
- Create directories if they don't exist

### 4. Write the Entry

```markdown
---
title: "{title}"
created: {ISO-8601-with-timezone}
machine: {machine}
author: {author}
session_id: "{session_id from CLAUDE_SESSION_ID env var or hook context, if available}"
description: "{description}"
summary: "{summary}"
tags:
  - {tag1}
  - {tag2}
session_type: {type}
related:
  - {ref1}
ventures:
  - {venture1}
urls:
  - {url1}
references_date: null
type: atomic
parent_daily: "{YYYY-MM-DD}"
parent_monthly: "{YYYY-MM}"
parent_yearly: "{YYYY}"
---

# {title}

{content}
```

### 5. Post-Creation

After writing the entry:
1. Confirm creation with path and title
2. If URLs were found in content, mention they were captured in frontmatter
3. If ventures were linked, mention the connection
4. Write the pipeline heartbeat (so the health monitor knows journaling is active):
   ```bash
   date -u +%Y-%m-%dT%H:%M:%S+00:00 > ~/.claude/local/health/journal-heartbeat
   ```

## Content Guidelines

### What Makes a Good Atomic Entry

**DO:**
- Capture one coherent thought, decision, or event
- Include context: why this matters, what prompted it
- Record decisions with rationale (not just the outcome)
- Note people involved and their roles
- Include concrete details: numbers, dates, names
- End with forward-looking notes when relevant ("Next: ...")

**DON'T:**
- Combine unrelated topics (make two entries instead)
- Write vague summaries ("did stuff today")
- Omit the WHY behind decisions
- Truncate or abbreviate — full content always

### Entry Size

- Quick notes: 3-5 lines of content
- Standard entries: 1-2 paragraphs
- Detailed entries (strategic, design): multi-section with headers
- No maximum — let the content determine the length

### Session Type Guide

| Type | When to Use |
|------|------------|
| `strategic` | Roadmaps, long-term planning, system design |
| `design` | Architecture decisions, technical design |
| `debug` | Bug investigation, troubleshooting |
| `reflect` | Looking backward, lessons learned |
| `plan` | Forward-looking, priorities, intentions |
| `note` | General observations, quick captures |
| `meeting` | Conversation summaries, decisions from meetings |
| `research` | Investigation, learning, discovery |

## DNA Spiral: Writing Style

Journal entries capture experience at multiple levels simultaneously:

1. **What happened** — the facts, events, actions
2. **What it means** — interpretation, significance, patterns
3. **What comes next** — implications, next steps, open questions

Weave these three levels naturally rather than separating into rigid sections. The best entries flow from observation to meaning to intention.

## Templates by Session Type

### Strategic Entry
```markdown
# {title}

## Context
{What situation or question prompted this}

## Analysis
{Key observations, data, patterns}

## Decision / Direction
{What was decided and why}

## Implications
{What this means for active ventures, timeline, priorities}

## Next Steps
- {concrete action 1}
- {concrete action 2}
```

### Debug Entry
```markdown
# {title}

## Symptom
{What was observed}

## Investigation
{What was tried, what was found}

## Root Cause
{The actual issue}

## Fix
{What was done}

## Lessons
{What to remember for next time}
```

### Meeting / Conversation Entry
```markdown
# {title}

## Participants
{Who was involved}

## Key Points
- {point 1}
- {point 2}

## Decisions
- {decision with rationale}

## Action Items
- [ ] {who}: {what} by {when}
```

### Quick Note
```markdown
# {title}

{The thought, observation, or capture. Just write naturally.}
```

## Common Mistakes

1. **Forgetting machine scope**: Always use the configured machine name in the path
2. **Wrong time format**: Must be ISO 8601 with timezone offset (e.g., `2026-03-09T14:30:00-07:00`)
3. **Missing parent links**: Always include parent_daily, parent_monthly, parent_yearly
4. **Tag formatting**: Lowercase, hyphenated, no `#` prefix in frontmatter (that's for body text)
5. **Overloading entries**: One topic per entry. If two things happened, write two entries.
6. **Empty summary**: The summary field is crucial for synthesis — always fill it
