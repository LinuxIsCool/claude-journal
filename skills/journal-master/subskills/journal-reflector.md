---
name: journal-reflector
description: >
  Facilitate structured reflection through the journal. Use when the user wants to look backward — end-of-day review, weekly retrospective, milestone reflection, venture retrospective, or lessons-learned capture.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Journal Reflector

Look backward to move forward. Structured reflection extracts patterns, lessons, and insights from recent experience.

## When to Use

- End of day: "How did today go?"
- End of week: "What patterns do I notice?"
- After a milestone: "What did we learn from shipping X?"
- Venture transition: "Why is this venture going dormant?"
- On request: "I want to reflect on..."

## Reflection Process

### 1. Gather Context

Read relevant entries:

**For daily reflection:**
```
Glob: ~/.claude/local/journal/{machine}/YYYY/MM/DD/*.md  (today's entries)
```

**For weekly reflection:**
```
Glob: ~/.claude/local/journal/{machine}/YYYY/MM/{last 7 days}/*.md
```

**For venture reflection:**
```
Grep: "ventures:.*{venture-name}" in ~/.claude/local/journal/{machine}/
```

### 2. Choose Framework

Offer these frameworks — match to situation, let user choose:

#### Start-Stop-Continue
Best for: behavioral adjustment, process improvement.

```markdown
## Reflection: Start-Stop-Continue

### Start (What should I begin doing?)
- {new behavior or practice to adopt}

### Stop (What should I cease doing?)
- {behavior or practice that isn't serving me}

### Continue (What's working well?)
- {behavior or practice to maintain}
```

#### Rose-Thorn-Bud
Best for: balanced assessment with forward potential.

```markdown
## Reflection: Rose-Thorn-Bud

### Rose (What went well?)
- {positive outcomes, wins, things to celebrate}

### Thorn (What was difficult?)
- {challenges, frustrations, things that didn't work}

### Bud (What has potential?)
- {emerging opportunities, seeds planted, things to watch}
```

#### 4Ls (Liked, Learned, Lacked, Longed For)
Best for: comprehensive retrospective.

```markdown
## Reflection: 4Ls

### Liked
- {what I enjoyed or appreciated}

### Learned
- {new knowledge, skills, or insights}

### Lacked
- {what was missing — resources, skills, information}

### Longed For
- {what I wished for — better tools, more time, different outcome}
```

#### Energy Audit
Best for: understanding personal patterns and sustainability.

```markdown
## Reflection: Energy Audit

### Energy Givers (what energized me?)
- {activities, people, outcomes that gave energy}

### Energy Drains (what depleted me?)
- {activities, situations, patterns that cost energy}

### Energy Balance
- Overall: {net positive / neutral / net negative}
- Pattern: {what I notice about my energy this period}
- Adjustment: {what to change to improve the balance}
```

#### Venture Retrospective
Best for: when a venture changes stage (active → dormant, exploring → active, etc.)

```markdown
## Venture Retrospective: {venture name}

### Stage Transition
- From: {previous stage}
- To: {new stage}
- Why: {what triggered this transition}

### What Was Accomplished
- {concrete outcomes, deliverables, milestones reached}

### What Was Learned
- {technical lessons, process insights, relationship dynamics}

### What Carries Forward
- {knowledge, relationships, artifacts that remain valuable}

### Conditions for Reactivation (if going dormant)
- {what would need to change for this to become active again}
```

### 3. Write the Reflection Entry

Create an atomic entry with `session_type: reflect`:

```markdown
---
title: "Weekly Reflection — March 3-9"
created: {timestamp}
machine: {machine}
author: {author}
description: "End-of-week reflection on first week with Legion"
summary: "{2-3 sentences capturing key insights}"
tags:
  - reflection
  - weekly
session_type: reflect
related:
  - {entries referenced during reflection}
ventures:
  - {ventures discussed}
urls: []
type: atomic
parent_daily: "{YYYY-MM-DD}"
parent_monthly: "{YYYY-MM}"
parent_yearly: "{YYYY}"
---

# Weekly Reflection — March 3-9

{framework content}

## Key Insight
{The one thing that stands out most from this reflection}

## Carrying Forward
{What specifically changes going forward based on this reflection}
```

### 4. After Writing

- Highlight the key insight to the user
- Suggest connections to ventures or past entries if relevant
- If patterns emerge across multiple reflections, note them

## Reflection Prompts

Use these to deepen reflection when the user gives brief input:

**Daily:**
- What was the most meaningful thing today?
- What decision did you make that you want to remember?
- What would you tell yourself tomorrow morning?

**Weekly:**
- What pattern repeats across this week's entries?
- Where did intention and reality diverge?
- What's one thing you'd do differently?

**Milestone:**
- What was harder than expected? Easier?
- Who helped? Who should you thank?
- What would you tell someone starting this same work?

## Common Mistakes

1. **Shallow reflection**: "It was good" isn't reflection. Push for specifics.
2. **Only negative**: Balance critique with wins. What worked matters too.
3. **No forward action**: Reflection without intention for change is just reminiscing.
4. **Skipping context**: Always read entries before reflecting — memory is unreliable.
5. **Forced frameworks**: If the user just wants to free-write, let them. Frameworks are tools, not mandates.
