---
title: geno-loops-boost
description: Time-boxed focus sessions (Pomodoro)
---

# geno-loops-boost

`/geno-loops-boost "[task] [--work <min>] [--reflect <min>]"`

> Time-boxed focus sessions (Pomodoro)

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

Parse `$ARGUMENTS` for:

- **Task pattern** — fuzzy-matches against geno-notes tasks (optional)
- **`--work <min>`** — duration of the work phase in minutes (default: 25)
- **`--reflect <min>`** — duration of the reflection phase in minutes (default: 5)


## When to Use

- **Complex investigation** where context degradation is a risk
- **Open-ended exploration** or debugging without a clear end-point
- When you want to ensure **steady journal logging**
- To prevent "rabbit-holing" on a single approach for too long

Do **not** use when you have a clear plan (use Cruise), when you have a testable spec (use Turbocharge), or for quick tasks (under 30min).

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Load context

- Check for geno-notes project scope: `geno-notes list --project --status active --json`
- If a task pattern was provided, activate it: `geno-notes start <pattern> --project`
- Create session directory:
  ```
  .geno/loops/boost/<YYYYMMDD-HHMM>/
  ├── session.md
  └── log/
  ```
- Write `session.md` header:
  ```markdown
  # Boost Session — <YYYY-MM-DD HH:MM>
  ## Config
  - Task: <geno-notes task id or "none">
  - Work: <work_min>m
  - Reflect: <reflect_min>m

  ## Log
  ```

### 2. Start Work Phase

1. Log the start of the work block to `session.md`.
2. Determine the work duration (default 25min, max 60min for `ScheduleWakeup`).
3. Call `ScheduleWakeup` with the delay and the prompt: `/loop-boost-reflect <session_dir>`
4. Start working autonomously on the task.

### 3. Reflect Phase (Triggered by Wakeup)

When the wakeup fires, transition to reflection:

1. **Summarize** what was accomplished during the work block.
2. **Identify** key findings, decisions made, or new sub-tasks.
3. **Write to geno-notes**:
   ```bash
   geno-notes note "Boost Reflection: <summary>" --task <id> --kind note --project
   ```
4. Update `session.md` with the reflection summary.
5. Use `AskUserQuestion` to ask the user:
   - "Continue for another block?"
   - "Finish session"
   - "Change task"

### 4. Continue or Finish

- **If Continue**: Repeat from Step 2.
- **If Finish**:
  1. Write final summary to `session.md`.
  2. Log completion: `geno-notes note "Boost session complete" --task <id> --kind milestone --project`
  3. Report to the user and stop.
- **If Change Task**: Update configuration and repeat from Step 1.

## Error Recovery

- If `geno-notes` fails, log the reflection to `session.md` and continue.
- If the agent crashes during a work block, the `ScheduleWakeup` will still fire. On wake, the agent should attempt to reconstruct the lost work state from file changes.

## Completion

When this skill finishes (success, failure, or abandoned), emit a trace:

```bash
geno-trace emit \
  --skill geno-loops-boost \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors> \
  --task <geno-notes task id, if any> \
  --scope project \
  --produced "<.geno/loops/boost/<timestamp>/session.md>"
```

- `success` = at least one full work+reflect cycle completed with reflection logged to geno-notes
- `failure` = no work blocks completed, or reflection could not be persisted anywhere
- `abandoned` = user stopped early

## Runtime

Pure markdown workflow. Uses `ScheduleWakeup` for time-boxing and `geno-notes` for reflection persistence.

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Error recovery section** — LLMs can get stuck in retry loops or abandon tasks on first failure. Explicit fallback steps prevent both.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-loops](index.md)
