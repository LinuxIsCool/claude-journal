---
description: "Atomic journaling — capture, reflect, plan, browse, synthesize"
argument-hint: "[note <title> | reflect | plan | browse [query] | stats | synthesize [period] | today]"
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, Skill]
model: sonnet
---

# /journal Command

Dispatches to journal subskills based on the argument.

## Routing

Parse the argument and route:

| Input | Action |
|-------|--------|
| `/journal` | Show today's entries. If none, offer to create one. |
| `/journal today` | Same as bare `/journal` |
| `/journal note <title>` | Invoke **@journal-writer** with the given title |
| `/journal <free text>` | Invoke **@journal-writer** — treat the text as content to journal about |
| `/journal reflect` | Invoke **@journal-reflector** — start a reflection session |
| `/journal plan` | Invoke **@journal-planner** — start a planning session |
| `/journal browse` | Invoke **@journal-browser** — show recent entries |
| `/journal browse <query>` | Invoke **@journal-browser** with the query (date, tag, venture, keyword) |
| `/journal stats` | Invoke **@journal-browser** in stats mode |
| `/journal synthesize` | Invoke **@journal-synthesizer** for today |
| `/journal synthesize <period>` | Invoke **@journal-synthesizer** for the given period (today, this week, march, 2026, etc.) |

## Default Behavior (no arguments)

1. Determine today's date and the default machine from config
2. `Glob: ~/.claude/local/journal/{machine}/YYYY/MM/DD/*.md`
3. If entries exist:
   - List them with time, title, and summary
   - Offer: "Create another entry, or reflect on today?"
4. If no entries:
   - Say: "No journal entries today. What would you like to capture?"
   - Guide toward creating the first entry of the day

## Config Location

Read config from `~/.claude/local/journal/config.yml`. If it doesn't exist, use defaults:
- `default_machine: legion`
- `default_author: legion`
- `timezone: America/Vancouver`

## Argument Parsing

The first word after `/journal` determines the route:
- `note` → writer (rest of line is the title)
- `reflect` → reflector
- `plan` → planner
- `browse` → browser (rest of line is the query)
- `stats` → browser (stats mode)
- `synthesize` → synthesizer (rest of line is the period)
- `today` → default behavior
- Anything else → treat as free-text input for the writer
