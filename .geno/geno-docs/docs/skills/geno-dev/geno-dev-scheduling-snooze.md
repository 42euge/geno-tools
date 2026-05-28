---
title: geno-dev-scheduling-snooze
description: Snooze the current session
---

# geno-dev-scheduling-snooze

`/geno-dev-scheduling-snooze "<time expression> [prompt]"`

> Snooze the current session

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Usage

```
/geno-dev-scheduling-snooze <time> [prompt to execute on wake]
```


## Input

`<args>` contains a time expression and optionally a prompt describing what to do when the snooze ends.

**Time expression** — the first part of the argument, parsed as one of:

| Format | Examples | Resolution |
|---|---|---|
| Absolute clock time | `3:30 AM`, `15:30`, `3:30am` | Next occurrence of that time today, or tomorrow if already past |
| Relative duration | `in 2 hours`, `in 30 minutes`, `45m`, `2h` | From now |
| Named time | `tomorrow at 9am`, `tonight at midnight` | Resolved to absolute then to seconds |

**Prompt** — everything after the time expression. If provided, this is passed to `ScheduleWakeup` as the prompt to fire on wakeup. If omitted, the skill asks the user what they'd like to do when the snooze ends.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Get current time

Run `date "+%Y-%m-%d %H:%M:%S %Z"` to get the current local time and timezone.

### 2. Parse the time expression

Extract the time expression from the arguments. Parse it into an absolute target time.

**Rules:**
- If the target time is in the past (e.g., user says "3:30 AM" but it's already 4 AM), assume **tomorrow**.
- Clamp the computed delay to the ScheduleWakeup range: minimum 60 seconds, maximum 3600 seconds.
- If the target is more than 3600 seconds away, use **chained snoozes**: schedule a wakeup at the maximum delay (3600s) with a re-snooze prompt that will repeat until the target time is reached. The re-snooze prompt must include the original target time and the original wakeup prompt so context is preserved across hops.

### 3. Determine the wakeup prompt

- If the user provided a prompt after the time expression, use it verbatim.
- If no prompt was provided, ask the user: "What should I work on when the snooze ends?"
- For chained snoozes (target > 3600s away), the wakeup prompt is a `/loop`-compatible re-snooze instruction that re-checks the time and either re-snoozes or fires the original prompt.

### 4. Handle chained snoozes

When the delay exceeds 3600 seconds, build a chained wakeup:

1. Compute `remaining = target_time - now` in seconds.
2. If `remaining > 3600`, schedule a 3600s wakeup with a prompt that:
   - States the original target time (absolute, with timezone)
   - Includes the original wakeup prompt
   - Instructs the agent to re-invoke the snooze skill with the remaining time
3. If `remaining <= 3600`, schedule the final wakeup with the original prompt.

The chained prompt format:

```
Snooze chain — target: <YYYY-MM-DD HH:MM:SS TZ>. Check the current time.
If the target has not been reached, re-snooze for the remaining duration.
When the target is reached, execute: <original prompt>
```

### 5. Schedule the wakeup

Call `ScheduleWakeup` with:
- `delaySeconds`: the computed delay (clamped to [60, 3600])
- `reason`: a short human-readable description, e.g., "snoozing until 3:30 AM PST"
- `prompt`: the wakeup prompt (direct or chained)

### 6. Confirm to the user

Report:
- The target wakeup time (absolute, in local timezone)
- The delay in human-friendly format ("in 3 hours and 19 minutes")
- Whether chaining is needed ("will re-snooze every hour until then")
- What will happen on wakeup (the prompt, summarized)

## Examples

```
/geno-dev-scheduling-snooze 3:30 AM start working on the auth refactor
→ Snoozing until 3:30 AM PDT (in 3h 19m, 3 chained wakeups). On wake: "start working on the auth refactor"

/geno-dev-scheduling-snooze in 10 minutes
→ What should I work on when the snooze ends?
→ (user responds)
→ Snoozing for 10 minutes. On wake: "<user's response>"

/geno-dev-scheduling-snooze 45m run the benchmark suite
→ Snoozing for 45 minutes. On wake: "run the benchmark suite"
```

## Edge cases

- **Under 60 seconds**: ScheduleWakeup clamps to 60s minimum. Tell the user: "Minimum snooze is 60 seconds."
- **Ambiguous time**: If the time expression is ambiguous (e.g., "3:30" without AM/PM), infer based on context — if it's currently 2 AM, "3:30" likely means 3:30 AM. If it's 2 PM, "3:30" likely means 3:30 PM. When uncertain, ask.
- **No arguments**: Ask the user for a time expression.

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-dev-scheduling-snooze \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = ScheduleWakeup called with correct delay and prompt; confirmation displayed to user
- `failure` = time expression unparseable, or ScheduleWakeup call failed
- `abandoned` = user stopped early or declined to provide a wakeup prompt

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-dev](index.md)
