---
name: journal-browser
description: >
  Navigate, search, and explore the journal. Use when looking for past entries, searching content, finding entries by date/tag/venture, browsing the journal structure, or getting statistics.
allowed-tools: Read, Glob, Grep, Bash
---

# Journal Browser

Find, search, and navigate journal entries.

## Query Patterns

The user can request any of these browse modes:

### Browse by Date

**Today:**
```
Glob: ~/.claude/local/journal/{machine}/{YYYY}/{MM}/{DD}/*.md
```

**This week:** Glob the last 7 days of DD directories.

**This month:**
```
Glob: ~/.claude/local/journal/{machine}/{YYYY}/{MM}/**/*.md
```

**Specific date:**
```
Glob: ~/.claude/local/journal/{machine}/2026/03/09/*.md
```

### Browse by Tag

Search frontmatter for tag values:
```
Grep: "- {tag}" in ~/.claude/local/journal/{machine}/ glob="*.md"
```

### Browse by Venture

Search frontmatter for venture references:
```
Grep: "- {venture-name}" in ~/.claude/local/journal/ glob="*.md"
```

This searches across ALL machines since ventures span machines.

### Browse by Session Type

```
Grep: "session_type: {type}" in ~/.claude/local/journal/{machine}/ glob="*.md"
```

### Keyword Search

Full-text search across all entries:
```
Grep: "{keyword}" in ~/.claude/local/journal/ glob="*.md"
```

### Recent Entries

```
Glob: ~/.claude/local/journal/{machine}/**/*.md
```
Sort by modification time, take the most recent N.

## Statistics

When asked for `stats`, compute:

```markdown
## Journal Statistics

- **Total entries**: {count of all *.md files, excluding summaries}
- **Atomic entries**: {count where type: atomic or no type field}
- **Summaries**: {count where type: daily|monthly|yearly}
- **Date range**: {earliest entry} to {latest entry}
- **This month**: {count of entries this month}
- **Streak**: {consecutive days with at least one entry}
- **Top tags**: {most frequent tags across entries}
- **Machines**: {list of machine directories}
```

To compute stats efficiently:
1. `Glob: ~/.claude/local/journal/**/*.md` to get all files
2. Count by directory depth and naming pattern
3. `Grep: "tags:" + count` for top tags
4. Check consecutive dates for streak

## Output Format

### Simple List
For browse results, show a table:

```markdown
## Entries: {query description}

| Date | Time | Title | Tags |
|------|------|-------|------|
| 2026-03-09 | 12:11 | Sovereign Life System Roadmap | roadmap, planning |
| 2026-03-09 | 14:30 | Salish Dataset Progress | salish, data |
```

### With Preview
When the user wants more detail, show entry summaries:

```markdown
## Entries: {query description}

### 12:11 — Sovereign Life System Roadmap
> Built claude-ventures plugin. Discovered 10 old projects. Synthesized roadmap across three rings.
**Tags**: roadmap, planning | **Ventures**: salish-sea-dreaming

### 14:30 — Salish Dataset Progress
> Curated 47 images from ArcGIS...
```

### Search Results
For keyword searches, show matches in context:

```markdown
## Search: "{keyword}"

**12-11-sovereign-life-system-roadmap.md** (2026-03-09)
> ...the **keyword** appeared in this context...

**14-30-salish-dataset-progress.md** (2026-03-09)
> ...another match with **keyword**...
```

## Navigation Tips

- Start broad (browse month), then narrow (browse specific day)
- Use tags for thematic navigation
- Use ventures for project-scoped views
- Use keyword search when you remember content but not when
- Stats give a birds-eye view of journaling patterns

## Common Mistakes

1. **Searching wrong machine**: Default to configured machine, but search all machines for cross-cutting queries (ventures, keyword)
2. **Missing summary files**: Summary files (YYYY-MM-DD.md, YYYY-MM.md) are in parent directories, not day directories
3. **Confusing filename time with created time**: Filename `HH-MM` is creation time, but always read frontmatter `created:` for authoritative timestamp
