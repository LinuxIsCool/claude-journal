---
name: journal-planner
description: >
  Forward-looking planning through the journal. Use when the user wants to plan their day, week, or month, set priorities, allocate time to ventures, or set goals.
  Reads recent entries and venture data to provide informed planning.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Journal Planner

Create forward-looking journal entries that translate reflection into action.

## When to Use

- Daily planning: "What should I focus on today?"
- Weekly planning: "What are my priorities this week?"
- Venture planning: "What needs to happen on each active venture?"
- Goal setting: "What do I want to accomplish this month?"

## Planning Process

### 1. Gather Context

Before planning, read:

**Recent journal entries:**
```
Glob: ~/.claude/local/journal/{machine}/YYYY/MM/DD/*.md  (last 3-7 days)
```

**Active ventures (if claude-ventures installed):**
```
Glob: ~/.claude/local/ventures/active/*.md
```

**Previous plans:**
```
Grep: "session_type: plan" in ~/.claude/local/journal/{machine}/
```

### 2. Assess Current State

From gathered context, identify:
- What's in progress? What's blocked?
- What deadlines are approaching?
- What was planned but not done?
- What new information changes priorities?

### 3. Choose Framework

Offer these frameworks — let the user choose, don't force one:

#### 1-3-5 Rule
Simple and effective for daily planning.

```markdown
## Today's Plan (1-3-5)

### The One Big Thing
- [ ] {the most important thing to accomplish}

### Three Medium Things
- [ ] {important but not critical}
- [ ] {important but not critical}
- [ ] {important but not critical}

### Five Small Things
- [ ] {quick wins, maintenance, communications}
- [ ] {quick wins}
- [ ] {quick wins}
- [ ] {quick wins}
- [ ] {quick wins}
```

#### Time Boxing
For days with competing priorities.

```markdown
## Time Blocks

| Time | Block | Venture/Focus | Energy |
|------|-------|--------------|--------|
| 09:00-11:00 | Deep work | salish-sea-dreaming | High |
| 11:00-12:00 | Admin | infrastructure | Medium |
| 13:00-15:00 | Deep work | salish-sea-dreaming | High |
| 15:00-16:00 | Communication | — | Low |
| 16:00-17:00 | Learning | — | Medium |
```

#### Energy Mapping
Match work to energy levels.

```markdown
## Energy-Aligned Plan

### High Energy (morning)
- {hardest, most creative work}
- {deep thinking, design decisions}

### Medium Energy (afternoon)
- {implementation, routine tasks}
- {meetings, collaboration}

### Low Energy (evening)
- {reading, light review}
- {planning tomorrow}
```

### 4. Write the Plan Entry

Create an atomic entry with `session_type: plan`:

```markdown
---
title: "Weekly Plan — March 10-14"
created: {timestamp}
machine: {machine}
author: {author}
description: "Planning priorities and time allocation for the week"
summary: "{2-3 sentences summarizing key priorities}"
tags:
  - planning
  - weekly
session_type: plan
related:
  - {previous plan entry}
ventures:
  - {active ventures this week}
urls: []
type: atomic
parent_daily: "{YYYY-MM-DD}"
parent_monthly: "{YYYY-MM}"
parent_yearly: "{YYYY}"
---

# Weekly Plan — March 10-14

## Priorities
{ranked list with venture connections}

## Plan
{chosen framework content}

## Venture Focus
{time/attention allocation per active venture}

## Open Questions
{things to resolve this week}
```

## Venture-Aware Planning

When ventures are available, planning should:

1. **Read active ventures** and their deadlines
2. **Rank by priority** (deadline urgency, manual priority)
3. **Allocate attention** proportional to urgency
4. **Surface dormant ventures** if context makes them relevant
5. **Note blocked ventures** and what unblocks them

### Example Venture Section

```markdown
## Venture Focus This Week

### Salish Sea Dreaming (CRITICAL — 36 days to show)
- 60% of deep work time
- Target: 100 more images curated, first Autolume test
- Blocked on: H100 access (follow up with Arshia)

### Infrastructure (HIGH — foundation work)
- 20% of time
- Target: E15 backup complete, inventory verified
- No blockers

### Knowledge Processing (MEDIUM — can wait)
- 10% of time
- Target: Transcript pipeline skeleton only
- Deferred: FalkorDB setup (spring)
```

## Planning Rhythms

| Rhythm | Frequency | Duration | Focus |
|--------|-----------|----------|-------|
| Daily | Every morning | 5 min | Today's 1-3-5 |
| Weekly | Monday morning | 15 min | Week priorities, venture allocation |
| Monthly | First of month | 30 min | Month goals, venture portfolio review |
| Quarterly | Season change | 60 min | Strategic review, lifecycle transitions |

## Common Mistakes

1. **Planning without context**: Always read recent entries first
2. **Overcommitting**: Plan for 60% capacity — interruptions happen
3. **Ignoring energy**: Don't schedule deep work when energy is low
4. **Venture blindness**: Check all active ventures, not just the loudest
5. **No carryover**: Review what rolled over from last plan before making new one
