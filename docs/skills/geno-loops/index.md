---
title: geno-loops
description: Agentic execution loop patterns — cruise, turbocharge, autopilot
---

# geno-loops

Agentic execution loop patterns — cruise, turbocharge, autopilot

[:material-github: GitHub](https://github.com/42euge/geno-loops){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-loops-autopilot](#geno-loops-autopilot) | `/geno-loops-autopilot` | Background monitoring loop |
| [geno-loops-boost](#geno-loops-boost) | `/geno-loops-boost` | Time-boxed focus sessions (Pomodoro) |
| [geno-loops-cruise](#geno-loops-cruise) | `/geno-loops-cruise` | Plan-driven sequential execution loop |
| [geno-loops-drift](#geno-loops-drift) | `/geno-loops-drift` | Question-driven exploration loop |
| [geno-loops-ignition](#geno-loops-ignition) | `/geno-loops-ignition` | Cold-start bootstrap loop |
| [geno-loops-supercharge](#geno-loops-supercharge) | `/geno-loops-supercharge` | Run an extended autonomous work session with structured cycles of planning, implementation, and evaluation |
| [geno-loops-turbocharge](#geno-loops-turbocharge) | `/geno-loops-turbocharge` | Spec-driven convergence loop |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-loops
    
    Execution loop patterns for autonomous and semi-autonomous agent work.
    
    | Skill | Slash command | Pattern |
    |-------|---------------|---------|
    | geno-loops-turbocharge | /geno-loops-turbocharge | Spec-driven convergence — iterate until all criteria pass |
    | geno-loops-cruise | /geno-loops-cruise | Plan-driven sequential — execute steps one at a time |
    | geno-loops-boost | /geno-loops-boost | Pomodoro focus — time-boxed blocks with reflection |
    | geno-loops-drift | /geno-loops-drift | Question-driven exploration — prioritized Q queue |
    | geno-loops-ignition | /geno-loops-ignition | Cold-start bootstrap — turn goal into blueprint |
    | geno-loops-autopilot | /geno-loops-autopilot | Background monitoring — watch CI/tests/lint/git |
    | geno-loops-supercharge | /geno-loops-supercharge | Long-running autonomous sessions — 8-24h multi-cycle runs |

## geno-loops-autopilot

**Slash command:** `/geno-loops-autopilot`

> Background monitoring loop

??? example "Full skill definition (Level 4)"

    Background monitoring and maintenance loop. Watches the repo or PR over a long window and reacts when conditions change. Low intensity and reactive: it wakes on a cron, checks health signals, applies safe fixes when obvious, and escalates anything ambiguous.
    
    ## Input
    
    Parse `$ARGUMENTS` for:
    
    - **Task pattern** — fuzzy-matches against geno-notes tasks (optional)
    - **`--watch <tests|ci|lint|git|all>`** — what to monitor. Default: `all`
    - **`--every <15m|30m>`** — wake interval. Default: `15m`
    - **`--for <duration>`** — total monitoring window. Default: `24h`, max `7d`
    
    If no explicit watch target is given, monitor `ci`, `lint`, `tests`, and `git`.
    
    ## When to Use
    
    - You opened a PR and want passive CI/watchdog coverage
    - You want regression catching while other work is happening
    - You need low-touch maintenance over hours instead of an active tight loop
    - You want automatic journaling of failures, fixes, and follow-up tasks
    
    Do **not** use when the goal is active implementation (use Turbocharge or Cruise), exploratory research (use Drift), or a one-time delayed action (use Snooze).
    
    ## Workflow
    
    ### 1. Load context
    
    - Check for geno-notes project scope: `geno-notes list --project --status active --json`
    - If a task pattern was provided, activate it: `geno-notes start <pattern> --project`
    - Detect repo, current branch, default branch, and whether the branch has an open PR
    - Create session directory:
      ```
      .geno/loops/autopilot/<YYYYMMDD-HHMM>/
      ├── session.md
      └── checkpoints/
      ```
    - Write `session.md` header:
      ```markdown
      # Autopilot Session — <YYYY-MM-DD HH:MM>
      ## Config
      - Task: <geno-notes task id or "none">
      - Watch: <tests, ci, lint, git>
      - Interval: <15m or 30m>
      - Duration: <target end time>
      - Branch: <current branch>
    
      ## Log
      ```
    
    ### 2. Establish baseline
    
    Record the starting state for each selected signal:
    
    - **tests** — detect the project's normal test command and run it once if it is safe and well-defined
    - **lint** — detect the lint command (or formatter/lint autofix command if available)
    - **ci** — inspect current PR checks or recent workflow runs with `gh`
    - **git** — capture working tree status, ahead/behind state, and merge-conflict markers
    
    Log the baseline in `session.md`:
    
    ```markdown
    ### Baseline — <timestamp>
    - Tests: passing / failing / unavailable
    - Lint: clean / failing / unavailable
    - CI: green / red / pending / unavailable
    - Git: clean / dirty / diverged
    ```
    
    If no reliable local test or lint command can be detected, keep monitoring CI and git state instead of guessing.
    
    ### 3. Schedule recurring checks
    
    - Use `CronCreate` to schedule recurring wakeups every 15 or 30 minutes
    - Set the schedule end time to the requested duration, capped at 7 days
    - Pass a wake prompt that includes:
      - session directory
      - watch targets
      - branch / PR context
      - conservative fix rules
    - Record the cron id and end time in `session.md`
    
    ### 4. On each cycle
    
    On each wakeup:
    
    1. Re-check each selected signal
    2. Compare against the previous cycle and the baseline
    3. Classify findings:
       - **Healthy** — no action needed
       - **Retryable** — likely transient failure (for example flaky CI or network failure)
       - **Safe fix** — deterministic, low-risk fix is available
       - **Human action** — needs design judgment or touches user work
    
    Allowed safe fixes:
    
    - Run documented formatter or lint autofix commands
    - Regenerate deterministic tracked artifacts when the repo already treats them as generated outputs
    - Retry a failing test or CI check once when the failure looks transient
    
    If a safe fix changes tracked files:
    
    - Verify immediately with the relevant check
    - Only auto-commit on a non-default branch
    - Use a narrow commit message like `autopilot: fix lint drift`
    
    If the branch is the default branch, never auto-commit. Log the fix opportunity and alert instead.
    
    ### 5. Log and journal
    
    Append each cycle to `session.md`:
    
    ```markdown
    ### Cycle <n> — <timestamp>
    - Findings: <summary>
    - Action: <none | retried | fixed | escalated>
    - Result: <green | still failing | waiting on human>
    ```
    
    Integrate with geno-notes when available:
    
    - New failures or regressions → `geno-notes note ... --kind bug`
    - Successful auto-fixes → `geno-notes note ... --kind milestone`
    - Issues needing a human later → create or suggest a follow-up task
    
    ### 6. Continue or stop
    
    Keep monitoring while progress is passive and safe.
    
    Stop the loop when:
    
    - The requested duration expires
    - The PR is merged or closed
    - The branch is deleted or no longer relevant
    - The same problem fails repeated retries or safe fixes
    - Human input is required
    
    When stopping, write a final summary to `session.md` and report whether the session ended cleanly, with fixes applied, or blocked on a person.
    
    ## Error Recovery
    
    - If a check command crashes, retry once. If it crashes again, mark that signal unavailable and continue with the others.
    - If the same safe fix fails twice, stop retrying it and escalate.
    - If `gh` is unavailable, continue monitoring local signals and log degraded mode.
    - If `geno-notes` fails, keep monitoring and write the journal information to `session.md` instead.
    - Never do destructive git operations inside Autopilot: no force pushes, hard resets, rebases, merges, or automatic conflict resolution.
    
    ## What NOT to Do
    
    - **Don't monitor forever.** Respect the `CronCreate` 7-day cap.
    - **Don't auto-fix ambiguous failures.** If the cause is not obvious, alert a human.
    - **Don't commit to the default branch.** Background maintenance must stay off `main`/`master`.
    - **Don't overwrite user changes.** If the tree is dirty from unrelated edits, log it and stop.
    - **Don't turn Autopilot into Turbocharge.** If the loop becomes active implementation, switch to a tighter execution loop.
    
    ## Completion
    
    When this skill finishes (success, failure, or abandoned), emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-loops-autopilot \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --task <geno-notes task id, if any> \
      --scope project \
      --produced "<.geno/loops/autopilot/<timestamp>/session.md>"
    ```
    
    - `success` = monitoring window completed or PR merged with all signals healthy at final cycle
    - `failure` = all monitored signals unavailable, or unresolved regressions never escalated
    - `abandoned` = user stopped early
    
    ## Runtime
    
    No venv or scripts — pure markdown workflow. Uses `CronCreate` for 15–30 minute recurring checks over long-running sessions.

## geno-loops-boost

**Slash command:** `/geno-loops-boost`

> Time-boxed focus sessions (Pomodoro)

??? example "Full skill definition (Level 4)"

    Time-boxed focus sessions. Implements the Pomodoro technique: 25 minutes of deep work followed by 5 minutes of reflection. Forces periodic stopping to prevent context degradation and ensure progress is logged. Journal-heavy — every reflection phase writes a journal entry to `geno-notes`.
    
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

## geno-loops-cruise

**Slash command:** `/geno-loops-cruise`

> Plan-driven sequential execution loop

??? info "Observability"

    success_signal: "all plan steps completed successfully" failure_signals: - "step failed twice consecutively" - "user intervention required" knowledge_reads: - "geno-notes tasks (active, project scope)" - "geno-notes plans" knowledge_writes: - "geno-notes journal (milestones per step)" - ".geno/loops/cruise/*/session.md"

??? example "Full skill definition (Level 4)"

    Plan-driven sequential execution. Takes a plan (numbered step list) and executes steps one at a time, each in a fresh Agent subagent with checkpoint handoff. Methodical and predictable — no re-planning, no parallelism, just steady forward progress.
    
    ## Input
    
    Parse `$ARGUMENTS` for:
    
    - **Task pattern** — fuzzy-matches against geno-notes tasks (optional)
    - **`--plan <file>`** — path to a plan file with numbered steps
    
    Plan discovery order if `--plan` is not provided:
    
    1. Check `geno-notes plans/<task-slug>.md` for the matched task
    2. Check `.geno/loops/cruise/` for a recent session with an unfinished plan
    3. If nothing found, use `AskUserQuestion` to ask the user for one of:
       - A plan file path
       - A numbered list of steps (freeform text — write to `.geno/loops/cruise/<session>/plan.md`)
       - "Create one" — enter `EnterPlanMode`, design a plan, save it, then continue
    
    ## When to Use
    
    - You have a **clear, ordered plan** with numbered steps
    - Steps are mostly **sequential** — each builds on the previous
    - Multi-step refactors, migration checklists, documentation across files
    - Following a plan written in a previous planning session
    - Executing a runbook or checklist
    
    Do **not** use when the work needs re-planning as it progresses (use Overdrive), when steps are independent and can run in parallel (use NOS), or when there's no plan yet and the goal is exploratory (use Drift or Boost).
    
    ## Workflow
    
    ### 1. Load context
    
    - Check for geno-notes project scope: `geno-notes list --project --status active --json`
    - If a task pattern was provided, activate it: `geno-notes start <pattern> --project`
    - Read the plan file
    - Create session directory:
      ```
      .geno/loops/cruise/<YYYYMMDD-HHMM>/
      ├── session.md
      ├── plan.md          (copy of the plan)
      └── checkpoints/
      ```
    - Write `session.md` header:
      ```markdown
      # Cruise Session — <YYYY-MM-DD HH:MM>
      ## Config
      - Task: <geno-notes task id or "none">
      - Plan: <plan file path>
      - Steps: <total count>
    
      ## Checklist
      - [ ] Step 1: <description>
      - [ ] Step 2: <description>
      ...
    
      ## Log
      ```
    
    ### 2. Parse plan
    
    Extract the numbered steps from the plan file. For each step, identify:
    
    - **Description** — what to do
    - **Files involved** — which files will be read or modified (if stated)
    - **Dependencies** — whether this step depends on a previous step's output
    - **Verification** — how to confirm the step is done (if stated)
    
    Write the parsed checklist to `session.md`.
    
    ### 3. Pick next step
    
    Select the first step in the checklist that is not yet marked `[x]`. Read the checkpoint from the previous step (if any) at `checkpoints/step_<n-1>.md` to understand the current state.
    
    If all steps are done, skip to step 6 (complete).
    
    ### 4. Execute step
    
    Spawn an **Agent subagent** with a self-contained prompt including:
    
    - The step description
    - Relevant file paths from the plan
    - The previous step's checkpoint (handoff context)
    - Instructions to write a checkpoint when done
    
    The agent prompt should follow this structure:
    
    ```
    You are executing step <n> of a plan for: <task description>
    
    ## Previous step
    <checkpoint from step n-1, or "This is the first step">
    
    ## Your task
    <step description>
    
    ## Files
    <relevant file paths>
    
    ## When done
    Write a checkpoint to: <session-dir>/checkpoints/step_<n>.md
    
    Checkpoint format:
      # Step <n> Checkpoint
      ## What was done
      <summary of changes>
      ## Files modified
      <list>
      ## State for next step
      <anything the next step needs to know>
      ## Issues encountered
      <any problems or deviations from plan>
    ```
    
    Wait for the agent to complete and read its checkpoint.
    
    ### 5. Verify + log
    
    Read the agent's checkpoint at `checkpoints/step_<n>.md`:
    
    - Verify the step's claimed changes actually exist (spot-check modified files)
    - If verification is defined in the plan, run it (test command, type check, etc.)
    - Update `session.md`: mark the step `[x]` in the checklist, append a log entry:
      ```markdown
      ### Step <n> — <timestamp>
      <summary from checkpoint>
      ```
    - Log to geno-notes:
      ```bash
      geno-notes note "Cruise step <n>/<total>: <summary>" --task <id> --kind milestone --project
      ```
    
    If verification fails:
    - If this is the first failure for this step, retry (go back to step 4)
    - If this is the second failure, stop and ask the user for guidance via `AskUserQuestion`
    
    ### 6. Loop or complete
    
    **If more steps remain:**
    - Go back to step 3 (pick next step)
    - No delay needed between steps — Agent subagents already provide fresh context
    
    **If all steps are done:**
    1. Write final summary to `session.md`:
       ```markdown
       ## Summary
       - Steps completed: <n>/<total>
       - Duration: <start to end>
       - Key changes: <list>
       ```
    2. Log completion: `geno-notes note "Cruise complete: <n> steps executed" --task <id> --kind milestone --project`
    3. If the task is fully done: `geno-notes done <id> --project`
    4. Report to the user what was accomplished
    
    **If a step failed twice and user guidance is needed:**
    1. Write partial summary to `session.md`
    2. Log: `geno-notes note "Cruise paused at step <n>: <error>" --task <id> --kind bug --project`
    3. Present the issue to the user and wait for direction
    
    ## Error Recovery
    
    - If an Agent subagent fails to write a checkpoint, read the agent's output directly and construct the checkpoint manually.
    - If a step makes changes that break a previous step's work, revert the step's changes and flag the conflict. Do not attempt to fix inter-step conflicts automatically — ask the user.
    - If the plan file references files that don't exist, skip to the next step and log the missing file. The plan may be outdated.
    - If `geno-notes` CLI fails, continue executing steps — don't let journal failures block plan execution. Log the error to `session.md`.
    - Never do destructive git operations (force push, hard reset, branch delete) inside the loop.
    - If context grows too large (agent subagents help prevent this), write a comprehensive checkpoint and continue with fresh agents.
    
    ## What NOT to Do
    
    - **Don't re-plan mid-execution.** If the plan needs changing, stop and tell the user. Re-planning is Overdrive's job.
    - **Don't skip steps without user approval.** Even if a step seems unnecessary, execute it or ask first.
    - **Don't parallelize steps.** Steps are sequential by design. If you notice independent steps, suggest NOS for next time.
    - **Don't modify the plan file.** The plan is the contract. Deviations go in `session.md` and geno-notes, not the plan itself.
    - **Don't continue after two failures on the same step.** Escalate to the user.
    
    ## Completion
    
    When this skill finishes (success, failure, or abandoned), emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-loops-cruise \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --task <geno-notes task id, if any> \
      --scope project \
      --produced ".geno/loops/cruise/<session>/session.md"
    ```
    
    - `success` = all plan steps completed
    - `failure` = step failed twice or user had to intervene on a blocker
    - `abandoned` = user stopped the loop early
    
    ## Runtime
    
    No venv or scripts — pure markdown workflow. Uses Agent subagents for step execution with checkpoint-based handoff.

## geno-loops-drift

**Slash command:** `/geno-loops-drift`

> Question-driven exploration loop

??? example "Full skill definition (Level 4)"

    Question-driven exploration loop. Ideal for codebase archaeology, debugging complex issues with unclear scope, or understanding unfamiliar systems. It maintains a prioritized queue of questions, systematically answering each while spawning new inquiries along the way.
    
    ## Input
    
    Parse `$ARGUMENTS` for:
    
    - **Starting question** — the initial inquiry to kick off exploration (optional)
    - **`--max <n>`** — maximum cycles (default: 10)
    
    If no starting question is provided, use `AskUserQuestion` to ask the user what they want to explore.
    
    ## When to Use
    
    - **Codebase archaeology**: Understanding how a legacy or complex system works
    - **Debugging**: Investigating issues with high uncertainty or "where do I even start?"
    - **Research**: Exploring a new library, framework, or architectural pattern
    - **Root-cause analysis**: Following a chain of "why" questions
    
    Do **not** use when you have a clear spec or target (use Turbocharge), when you have a linear plan (use Cruise), or when you just need to get work done in focused blocks (use Boost).
    
    ## Workflow
    
    ### 1. Load context
    
    - Check for geno-notes project scope: `geno-notes list --project --status active --json`
    - Create session directory:
      ```
      .geno/loops/drift/<YYYYMMDD-HHMM>/
      ├── session.md
      └── questions.md
      ```
    - Write `questions.md` with the starting question:
      ```markdown
      # Question Queue
      - [ ] <starting-question> (Priority: High)
      ```
    - Write `session.md` header:
      ```markdown
      # Drift Session — <YYYY-MM-DD HH:MM>
      ## Config
      - Max cycles: <n>
    
      ## Log
      ```
    
    ### 2. Pick next question
    
    Select the highest priority open question from `questions.md`. If multiple have the same priority, pick the most specific one.
    
    Record the choice in `session.md`:
    ```markdown
    ### Cycle <n> — Exploring: "<question>"
    ```
    
    ### 3. Explore and answer
    
    Investigate the codebase or system to answer the question:
    
    - Use `grep_search`, `read_file`, `run_shell_command` as needed.
    - Document findings in `session.md` as they are discovered.
    - If the exploration leads to new questions, add them to `questions.md` with a priority (High/Medium/Low).
    - If a bug is found: `geno-notes note "Found bug: <desc>" --kind bug --project`
    - If a decision is needed or made: `geno-notes note "<decision>" --kind decision --project`
    
    ### 4. Finalize answer
    
    Once the question is sufficiently answered:
    
    - Update `questions.md`: mark the question as done and include the answer summary.
    - Log a milestone: `geno-notes note "Drift answered: <question>" --kind milestone --project`
    
    ### 5. Loop or complete
    
    **If all questions in `questions.md` are done OR max cycles reached:**
    1. Write final summary to `session.md`
    2. Present findings to the user.
    3. Stop the loop
    
    **If questions remain and cycles < max:**
    1. Call `ScheduleWakeup` with delay 180–270 seconds (exploratory work takes time)
    2. On wake, repeat from step 2
    
    ## What NOT to Do
    
    - **Don't get stuck on one question.** If a question is too broad, break it down into smaller ones.
    - **Don't skip documentation.** The value of Drift is the trail of breadcrumbs it leaves.
    - **Don't fix things blindly.** If you find a bug, log it first. Only fix it if it blocks the exploration itself.
    - **Don't lose the thread.** Always relate findings back to the current or future questions.
    
    ## Completion
    
    When this skill finishes (success, failure, or abandoned), emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-loops-drift \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --task <geno-notes task id, if any> \
      --scope project \
      --produced "<.geno/loops/drift/<timestamp>/session.md>"
    ```
    
    - `success` = all questions answered, or max cycles reached with findings documented in session.md and questions.md
    - `failure` = no questions answered after multiple cycles, or session ended without any findings logged
    - `abandoned` = user stopped early
    
    ## Runtime
    
    Pure markdown workflow. Uses `ScheduleWakeup` for self-pacing within `/loop`.

## geno-loops-ignition

**Slash command:** `/geno-loops-ignition`

> Cold-start bootstrap loop

??? example "Full skill definition (Level 4)"

    Cold-start bootstrap loop. Takes a high-level goal, generates or loads a blueprint, then iteratively bootstraps the work in layers: structure -> implementation -> verification. Each layer hands off checkpoints between Scaffolder, Builder, and Verifier roles so the plan can evolve as the repo takes shape.
    
    ## Input
    
    Parse `$ARGUMENTS` for:
    
    - **Task pattern** — fuzzy-matches against geno-notes tasks (optional)
    - **Goal text** — a freeform description of what to bootstrap
    - **`--blueprint <file>`** — start from an existing blueprint instead of generating one
    - **`--max <n>`** — maximum layers or iterations (default: 6)
    
    If no task pattern or goal is provided, use `AskUserQuestion` to ask the user for one of:
    1. A high-level goal
    2. A blueprint file path
    3. "Start from current issue/task"
    
    ## When to Use
    
    - Starting a new project, package, module, or feature branch from a rough goal
    - Bootstrapping structure before detailed specs exist
    - Standing up the first vertical slice: skeleton, core implementation, and verification harness
    - Turning an issue brief into an executable blueprint
    
    Do **not** use when a spec already exists (use Turbocharge), when a step-by-step plan already exists (use Cruise), or when the work is mostly exploratory research (use Drift).
    
    ## Workflow
    
    ### 1. Load or create task context
    
    - Check for geno-notes project scope: `geno-notes list --project --status active --json`
    - If a task pattern was provided, activate it: `geno-notes start <pattern> --project`
    - If no active task matches and the user gave a goal, create one: `geno-notes add "<goal>" --project`
    - Start or activate the task so milestones attach to it
    - Create session directory:
      ```
      .geno/loops/ignition/<YYYYMMDD-HHMM>/
      ├── session.md
      ├── goal.md
      ├── blueprint.md
      ├── layers/
      │   ├── layer_01.md
      │   └── ...
      └── checkpoints/
          ├── layer_01_scaffolder.md
          ├── layer_01_builder.md
          └── layer_01_verifier.md
      ```
    - Write `session.md` header:
      ```markdown
      # Ignition Session — <YYYY-MM-DD HH:MM>
      ## Config
      - Task: <geno-notes task id or "none">
      - Goal: <summary>
      - Blueprint: <generated or file path>
      - Max layers: <n>
    
      ## Log
      ```
    
    ### 2. Generate or load blueprint
    
    - If `--blueprint <file>` was provided, copy it into `blueprint.md`
    - Otherwise inspect the repo, issue, and constraints, then write a blueprint containing:
      - Objective and non-goals
      - Deliverables
      - Proposed structure (directories, files, entrypoints, interfaces)
      - Implementation slices or layers
      - Verification plan
      - Open questions and assumptions
    - Save the normalized goal in `goal.md`
    - Record the first log entry in `session.md`
    
    ### 3. Pick the next bootstrap layer
    
    Sequence work from lowest-friction foundation to first usable slice:
    
    1. **Structure** — folders, files, entrypoints, interfaces, placeholders
    2. **Implementation** — enough working code or content to make the layer real
    3. **Verification** — tests, lint/build integration, manual checks, docs updates
    
    Choose the smallest layer that meaningfully advances the blueprint without over-scaffolding. Write `layers/layer_<n>.md` with the target, files, verification method, and handoff notes.
    
    ### 4. Scaffold the layer
    
    - Spawn a **Scaffolder** agent with the blueprint, current layer file, and previous verifier checkpoint
    - Scaffolder creates or reorganizes the minimal structure needed for the layer and writes `checkpoints/layer_<n>_scaffolder.md`:
      ```markdown
      # Layer <n> Scaffolder
      ## Structure created
      ## Files touched
      ## Assumptions
      ## Handoff to Builder
      ```
    - If scaffolding reveals a better structure, update `blueprint.md` before continuing
    
    ### 5. Build the layer
    
    - Spawn a **Builder** agent with the blueprint, layer file, and scaffolder checkpoint
    - Builder fills in the scaffold with the smallest coherent implementation that makes the layer usable
    - Builder writes `checkpoints/layer_<n>_builder.md`:
      ```markdown
      # Layer <n> Builder
      ## What was implemented
      ## Files modified
      ## Remaining gaps
      ## Handoff to Verifier
      ```
    
    ### 6. Verify the layer
    
    - Spawn a **Verifier** agent with the blueprint, layer file, and builder checkpoint
    - Verifier runs the lightest meaningful validation for the layer:
    
    | Layer type | Verification examples |
    |---|---|
    | Structure | File tree check, import smoke test, command help output |
    | Implementation | Focused test, type check, local run, fixture execution |
    | Verification/docs | Full test target, lint, docs link spot-check |
    
    - Verifier writes `checkpoints/layer_<n>_verifier.md` with pass/fail, evidence, remaining gaps, and the recommended next layer
    - Log milestone:
      ```bash
      geno-notes note "Ignition layer <n> complete: <summary>" --task <id> --kind milestone --project
      ```
    
    ### 7. Evolve the blueprint
    
    Update `blueprint.md` and `session.md` with what became concrete:
    
    - Completed layers
    - Decisions discovered during implementation
    - Remaining layers
    - Scope cuts or new risks
    
    Treat the blueprint as a living build sheet, not a frozen spec.
    
    ### 8. Loop or complete
    
    **If the goal has a usable scaffold plus first verified slice:**
    1. Write final summary to `session.md`
    2. Log completion: `geno-notes note "Ignition complete: first verified slice bootstrapped" --task <id> --kind milestone --project`
    3. If the task is fully done: `geno-notes done <id> --project`
    4. Stop the loop
    
    **If work remains and layers < max:**
    1. Call `ScheduleWakeup` with delay 90-180 seconds
    2. On wake, repeat from step 3
    
    **If max layers reached:**
    1. Write summary to `session.md` with current scaffold, completed layers, and recommended next layer
    2. Log: `geno-notes note "Ignition stopped at max layers: <n>/<max> complete" --task <id> --kind note --project`
    3. Report what exists, what is next, and where to resume
    4. Stop the loop
    
    ## Error Recovery
    
    - If the blueprint is too vague to pick a first layer, stop and ask the user for a narrower goal.
    - If Scaffolder, Builder, and Verifier disagree on structure, resolve it in `blueprint.md` before starting the next layer.
    - If a verification step fails because the harness does not exist yet, treat building that harness as the next layer instead of forcing a broken check.
    - If two consecutive layers add only placeholders without producing a usable slice, reduce scope and bootstrap a thinner vertical path.
    - If `geno-notes` CLI fails, continue the loop and log the journal failure in `session.md`.
    - Never do destructive git operations or mass deletions of generated structure without explicit user confirmation.
    
    ## What NOT to Do
    
    - **Don't start coding without a blueprint.** Ignition is spec-generating; the blueprint is the contract for the next layers.
    - **Don't scaffold the whole project upfront.** Build only the next few layers needed to reach a verified slice.
    - **Don't freeze the blueprint.** Update it when the repo teaches you something new.
    - **Don't confuse placeholders with completion.** Every layer should end with something checkable.
    - **Don't use Ignition when the work already has a detailed plan or test suite.** Prefer Cruise or Turbocharge in those cases.
    
    ## Completion
    
    When this skill finishes (success, failure, or abandoned), emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-loops-ignition \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --task <geno-notes task id, if any> \
      --scope project \
      --produced "<.geno/loops/ignition/<timestamp>/session.md>"
    ```
    
    - `success` = first verified slice bootstrapped with at least one layer passing scaffolder+builder+verifier
    - `failure` = blueprint generated but no layers verified, or max layers reached with zero usable artifacts
    - `abandoned` = user stopped early
    
    ## Runtime
    
    No venv or scripts — pure markdown workflow. Uses Agent subagents for role handoffs and `ScheduleWakeup` for self-pacing within `/loop`.

## geno-loops-supercharge

**Slash command:** `/geno-loops-supercharge`

> Run an extended autonomous work session with structured cycles of planning, implementation, and evaluation

??? info "Observability"

    success_signal: "all planned cycles completed (or early-stopped because tasks are healthy) with checkpoints and session log written" failure_signals: - "cycle agent crashes repeatedly and no checkpoint is written" - "same action fails 3+ times without forward progress" - "git push or Kaggle API errors block all remaining work" knowledge_reads: - "task notebooks and reviews in tasks/" - "CLAUDE.md for architecture rules" - "~/.geno/supercharge/state.json (cross-session memory)" - "previous cycle checkpoints" knowledge_writes: - "session log at geno-agents/supercharge/sessions/<timestamp>/session.md" - "cycle checkpoints at geno-agents/supercharge/sessions/<timestamp>/checkpoints/" - "~/.geno/supercharge/state.json (updated cross-session memory)" - "task reviews in tasks/<task>/review/"

??? example "Full skill definition (Level 4)"

    Run an extended autonomous work session with structured cycles of planning, implementation, and evaluation. Works in any workspace — discovers tasks from geno-notes, scans for TODOs, or accepts user-specified goals. Based on Anthropic's harness design patterns for long-running apps.
    
    ## Input
    
    `$ARGUMENTS` — Optional directives. Examples:
    - `go!` — Start with defaults (8 hours, all discovered tasks)
    - `4h auth-refactor` — 4 hours focused on one area
    - `12h all` — Maximum duration across everything
    
    If no arguments, ask the user for duration and scope.
    
    ## Configuration
    
    ### Duration Dial
    
    Map the requested duration to cycle counts. Each cycle is ~30 minutes of wall time:
    
    | Duration | Cycles | Use case |
    |----------|--------|----------|
    | 1h       | 2      | Quick pass on one task |
    | 2h       | 4      | Focused work on 1-2 tasks |
    | 4h       | 8      | Medium run across several tasks |
    | 8h       | 16     | Full run across all tasks |
    | 12h      | 24     | Maximum — deep iteration on everything |
    
    ### Storage
    
    - **Session log:** `geno-agents/supercharge/sessions/<timestamp>/session.md` — running log of what happened
    - **Checkpoints:** `geno-agents/supercharge/sessions/<timestamp>/checkpoints/` — state snapshots between cycles
    - **Artifacts:** `geno-agents/supercharge/sessions/<timestamp>/artifacts/` — generated files, analysis, etc.
    - **Global state:** `~/.geno/supercharge/state.json` — cross-session memory (what worked, what didn't)
    
    ## Architecture
    
    Three specialized agent roles cycle through work:
    
    ### Planner (runs at start and every 4 cycles)
    - Reads current task state via `geno-notes list --project --json`
    - Reads CLAUDE.md / CLAUDE.local.md for project conventions
    - Checks `git status` and recent history for in-flight work
    - Reviews any existing plans and previous checkpoint findings
    - Prioritizes tasks from the backlog and writes a sprint plan to `checkpoints/sprint_<n>.md`
    - Considers: which tasks are blocked? which are highest priority? which have failing tests? what does the user care about most?
    
    ### Implementer (runs most cycles)
    - Picks up tasks from the sprint plan
    - Does the actual work: code changes, file edits, running commands, fixing tests
    - After each meaningful change, commits to git with a descriptive message
    - Logs progress via `geno-notes note "<cycle N: summary of what was done>"`
    - Writes a brief handoff note to `checkpoints/impl_<cycle>.md`
    
    ### Evaluator (runs every 2-3 cycles)
    - Checks: do tests pass? does the build succeed? does `git diff` look right?
    - Reviews whether acceptance criteria from the sprint plan are met
    - Runs any project-specific validation (linters, type checks, integration tests)
    - Compares current state against the sprint plan goals
    - Writes evaluation to `checkpoints/eval_<cycle>.md`
    - Feeds findings back into the next planner cycle
    
    ## Cycle Structure
    
    Each cycle follows this pattern:
    
    ```
    1. READ checkpoint from previous cycle
    2. DECIDE role for this cycle (planner/implementer/evaluator)
    3. EXECUTE the role's work
    4. WRITE checkpoint with:
       - What was done
       - Current state of each task
       - What to do next
       - Any blockers or surprises
    5. LOG to session.md
    6. LOG milestone to geno-notes via `geno-notes note`
    ```
    
    ### Role Rotation
    
    Default rotation pattern per 4-cycle sprint:
    1. **Plan** — assess state, set priorities
    2. **Implement** — work on highest priority item
    3. **Implement** — continue or move to next item
    4. **Evaluate** — check results, review, adjust
    
    ### Context Management
    
    To handle long runs without context degradation:
    - Each cycle runs as a **separate Agent** with a fresh context
    - The checkpoint file is the handoff document — it must contain everything the next agent needs
    - The session log is append-only and provides full history
    - If a cycle's agent runs into context limits, it writes a checkpoint and the next cycle picks up
    
    ## Task Discovery
    
    Tasks are discovered in priority order:
    
    1. **geno-notes project scope** — `geno-notes list --project --status backlog --json` for backlog tasks; `geno-notes list --project --status in-progress --json` for in-flight work
    2. **User-specified goals** — if the user provided a scope in `$ARGUMENTS`, treat it as the primary objective
    3. **Code scanning** — search for `TODO`, `FIXME`, `HACK`, `XXX` comments in the codebase as supplementary work items
    4. **Git state** — check for uncommitted changes, unfinished merges, or stale branches that need attention
    5. **Ask the user** — if none of the above yields actionable work, ask what to focus on
    
    ## Execution
    
    ### Startup
    
    1. Parse duration and scope from `$ARGUMENTS`
    2. Create session directory: `geno-agents/supercharge/sessions/<YYYYMMDD-HHMM>/`
    3. Read current state:
       - Discover tasks via geno-notes (`geno-notes list --project --json`)
       - Check `git status` and `git log --oneline -10` for recent activity
       - Scan for TODOs/FIXMEs if no geno-notes tasks exist
       - Read CLAUDE.md for project conventions and constraints
    4. Write initial checkpoint with full state assessment
    5. Write session header to `session.md`
    6. Log session start via `geno-notes note "supercharge session started: <duration>, <scope>"`
    
    ### Main Loop
    
    For each cycle (1 to N):
    1. Read the latest checkpoint
    2. Determine the role based on rotation + needs (e.g., if tests are failing, prioritize fixing them)
    3. Launch an Agent with the role's instructions and the checkpoint content
    4. The agent does its work and writes the next checkpoint
    5. Append cycle summary to session.md
    6. If the agent reports "all tasks are complete and no more work needed", stop early
    
    ### Shutdown
    
    After all cycles or early stop:
    1. Write final summary to `session.md`
    2. Write final state to `~/.geno/supercharge/state.json`
    3. Log completion via `geno-notes note "supercharge session complete: <summary>"`
    4. Report to user what was accomplished
    
    ## Checkpoint Format
    
    ```markdown
    # Checkpoint — Cycle <N>/<Total>
    ## Timestamp
    <ISO 8601>
    
    ## Previous Cycle
    <What the last cycle did, in 2-3 sentences>
    
    ## Task States
    | Task | Source | Status | Key Issue | Priority |
    |------|--------|--------|-----------|----------|
    | fix auth middleware | geno-notes | in-progress | token refresh failing | P1 |
    | add rate limiting | geno-notes | backlog | not started | P2 |
    | TODO: remove deprecated API | code scan | backlog | in api/v1/routes.py:42 | P3 |
    
    ## Current Sprint Plan
    <What we're working on this sprint>
    
    ## Next Action
    <Specific action for the next cycle to take>
    
    ## Blockers
    <Anything that's stuck>
    
    ## Lessons Learned
    <What worked, what didn't — carried forward>
    ```
    
    ## Error Recovery
    
    - If a cycle fails, the next cycle reads the last successful checkpoint and retries
    - If the same action fails 3 times, skip it and move to the next priority
    - If `git push` fails, investigate rather than retry blindly
    - If tests fail after a change, revert the change and try a different approach
    - If an external tool or API errors, note it and move to work that doesn't depend on it
    - Never force-push or do destructive git operations
    
    ## What NOT to Do
    
    - Don't spend multiple cycles on the same issue without trying a different approach
    - Don't push broken code — run tests and verify changes make sense before committing
    - Don't ignore CLAUDE.md rules — they exist for a reason
    - Don't create large, sweeping changes in a single cycle — prefer small, incremental commits
    - Don't skip the evaluation phase — it catches issues before they compound
    - Don't modify files outside the project scope without explicit user permission
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-loops-supercharge \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = all planned cycles completed (or early-stopped because all tasks are healthy) with session log and final checkpoint written
    - `failure` = loop terminated due to repeated cycle failures, unrecoverable errors, or no forward progress after 3 retries
    - `abandoned` = user stopped early

## geno-loops-turbocharge

**Slash command:** `/geno-loops-turbocharge`

> Spec-driven convergence loop

??? info "Observability"

    success_signal: "all acceptance criteria pass" failure_signals: - "max iterations reached with failing criteria" - "spec runner crashed twice" - "same criterion fails 3 iterations in a row" knowledge_reads: - "geno-notes tasks (active, project scope)" - "geno-notes plans" knowledge_writes: - "geno-notes journal (milestones per criterion)" - ".geno/loops/turbocharge/*/session.md"

??? example "Full skill definition (Level 4)"

    Spec-driven convergence loop. Takes a testable specification (test file, acceptance criteria, type contract) and iterates until every criterion passes. Each iteration validates, identifies gaps, implements fixes, and re-validates. The loop converges toward zero failures.
    
    ## Input
    
    Parse `$ARGUMENTS` for:
    
    - **Task pattern** — fuzzy-matches against geno-notes tasks (optional)
    - **`--spec <file>`** — path to the spec file (test suite, criteria list, type definitions)
    - **`--max <n>`** — maximum iterations (default: 8)
    
    If no spec is provided, use `AskUserQuestion` to ask the user for one of:
    1. A test file to run
    2. A list of acceptance criteria (freeform text — write them to `.geno/loops/turbocharge/<session>/spec.md`)
    3. A type contract or API spec file
    
    ## When to Use
    
    - You have a **testable target**: test suite, type definitions, acceptance criteria, API contract
    - The work is **convergence-oriented** — each iteration should get closer to passing
    - TDD: write tests first, then loop until green
    - Contract-first development: implement until the interface is satisfied
    - Migrations with known targets: old behavior must be preserved in new code
    
    Do **not** use when the goal is exploratory (use Drift), when there's no spec to validate against (use Boost), or when the work has many independent items (use NOS).
    
    ## Workflow
    
    ### 1. Load context
    
    - Check for geno-notes project scope: `geno-notes list --project --status active --json`
    - If a task pattern was provided, activate it: `geno-notes start <pattern> --project`
    - Read the spec file (or the criteria written during Input)
    - Create session directory:
      ```
      .geno/loops/turbocharge/<YYYYMMDD-HHMM>/
      ├── session.md
      ├── spec.md          (copy of spec or user-provided criteria)
      └── checkpoints/
      ```
    - Write `session.md` header:
      ```markdown
      # Turbocharge Session — <YYYY-MM-DD HH:MM>
      ## Config
      - Task: <geno-notes task id or "none">
      - Spec: <spec file path>
      - Max iterations: <n>
    
      ## Log
      ```
    
    ### 2. Validate spec (baseline)
    
    Run the spec check. The validation method depends on the spec type:
    
    | Spec type | Validation command |
    |---|---|
    | Test file (`.test.*`, `*_test.*`) | Run the test runner (`npm test`, `pytest`, `go test`, etc.) |
    | Type definitions (`.d.ts`, `.pyi`) | Run the type checker (`tsc --noEmit`, `mypy`, etc.) |
    | Acceptance criteria (`.md` list) | Grep/check each criterion manually against the codebase |
    | API contract (OpenAPI, protobuf) | Run contract validation tool or diff against implementation |
    
    Record baseline results in `session.md`:
    ```markdown
    ### Iteration 0 (baseline) — <timestamp>
    - Passing: 3/10
    - Failing: 7/10
    - Failures: <list each failing criterion>
    ```
    
    If everything already passes, write a note and stop — no work needed.
    
    ### 3. Identify gaps
    
    Compare passing vs. failing criteria. Prioritize:
    
    1. **Quick wins** — criteria that are close to passing (small changes needed)
    2. **Blockers** — criteria that other failing criteria depend on
    3. **Isolated** — criteria that can be fixed without touching shared code
    4. **Hard** — criteria requiring significant design or multi-file changes
    
    Pick the top 1–3 gaps to address this iteration. Write the plan to `session.md`.
    
    ### 4. Implement fixes
    
    Make targeted changes to close the selected gaps:
    
    - Keep changes **small and focused** — one logical change per iteration
    - Do not touch code unrelated to the failing criteria
    - Do not modify the spec itself
    - If a fix requires a design decision, log it: `geno-notes note "<decision>" --task <id> --kind decision --project`
    
    ### 5. Re-validate
    
    Run the spec check again (same method as step 2). Log results to `session.md`:
    
    ```markdown
    ### Iteration <n> — <timestamp>
    - Passing: 7/10 (+4)
    - Failing: 3/10 (-4)
    - Fixed this iteration: <list>
    - Still failing: <list>
    ```
    
    For each newly-passing criterion, log a milestone:
    ```bash
    geno-notes note "Turbocharge: <criterion> now passing" --task <id> --kind milestone --project
    ```
    
    ### 6. Loop or complete
    
    **If all criteria pass:**
    1. Write final summary to `session.md`
    2. Log completion: `geno-notes note "Turbocharge complete: all <n> criteria passing after <iterations> iterations" --task <id> --kind milestone --project`
    3. If the task is fully done: `geno-notes done <id> --project`
    4. Stop the loop
    
    **If criteria remain and iterations < max:**
    1. Call `ScheduleWakeup` with delay 60–120 seconds (stay in prompt cache)
    2. On wake, repeat from step 3
    
    **If max iterations reached:**
    1. Write summary to `session.md` with remaining failures
    2. Log: `geno-notes note "Turbocharge stopped at max iterations: <passing>/<total> passing" --task <id> --kind note --project`
    3. Report remaining gaps to the user
    4. Stop the loop
    
    ## Error Recovery
    
    - If a spec check command fails (not "tests failed" but "command crashed"), retry once. If it fails again, log the error to `session.md` and stop — the spec runner itself is broken.
    - If an iteration makes things worse (more failures than before), revert the changes (`git checkout -- .`) and try a different approach. Log the revert.
    - If the same criterion fails 3 iterations in a row with the same error, flag it as stuck and skip to other criteria.
    - If `geno-notes` CLI fails, continue the loop — don't let journal failures block convergence work. Log the geno-notes error to `session.md` instead.
    - Never do destructive git operations (force push, hard reset, branch delete) inside the loop.
    
    ## What NOT to Do
    
    - **Don't modify the spec.** The spec is the target, not the implementation. If the spec is wrong, stop and tell the user.
    - **Don't skip failing criteria.** Every criterion must either pass or be explicitly flagged as stuck.
    - **Don't make unrelated changes.** If you notice other issues, log them as `geno-notes note --kind bug` but don't fix them in this loop.
    - **Don't continue past max iterations.** Respect the limit — infinite loops waste resources.
    - **Don't run without a spec.** If there's nothing to validate against, suggest Boost or Drift instead.
    
    ## Completion
    
    When this skill finishes (success, failure, or abandoned), emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-loops-turbocharge \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --task <geno-notes task id, if any> \
      --scope project \
      --produced ".geno/loops/turbocharge/<session>/session.md"
    ```
    
    - `success` = all criteria pass
    - `failure` = max iterations reached or spec runner broken
    - `abandoned` = user stopped the loop early
    
    ## Runtime
    
    No venv or scripts — pure markdown workflow. Uses `ScheduleWakeup` for self-pacing within `/loop`.
