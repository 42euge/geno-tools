---
title: geno-agents
description: Multi-agent coordination, registration, autonomous loops
---

# geno-agents

Multi-agent coordination, registration, autonomous loops

[:material-github: GitHub](https://github.com/42euge/geno-agents){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-agents-supercharge](#geno-agents-supercharge) | `/geno-agents-supercharge` | Run an extended autonomous work session across benchmark tasks with structured cycles of implementation, reflection, ... |
| [geno-agents-tasks-start](#geno-agents-tasks-start) | `/geno-agents-tasks-start` | Pick up a task from the current workspace's geno-notes project scope, plan if needed, and start executing |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-agents — Agent Coordination
    
    ```!
    which geno-agents >/dev/null 2>&1 || echo "⚠️ geno-agents CLI not on PATH. Run: geno-tools install agents"
    ```
    
    You have access to geno-agents MCP tools (`list_agents`, `who`, `update_agent`, `register_agent`) and the `geno-agents` CLI on PATH (installed by geno-tools).
    
    ## Commands
    
    Parse the user's arguments to determine the action:
    
    ### `/geno-agents` (no args) or `/geno-agents status`
    Show the current agent network. Use the `list_agents` MCP tool. Display a clean summary:
    - Each agent's role, project, what they're working on, resources in use, and last seen
    - Highlight the current session
    - Flag stale agents
    
    ### `/geno-agents who`
    Show who this agent is — display the current session's agent card. Use the `who` MCP tool (no arguments needed).
    
    ### `/geno-agents who-are`
    List all other agents in the network (excludes yourself). Run:
    ```bash
    geno-agents who-are --session-id "${CLAUDE_SESSION_ID:-}"
    ```
    
    ### `/geno-agents whois <query>`
    Find agents by role or capability. Use the `whois` MCP tool.
    Example: `/geno-agents whois browser` → finds agents with browser capability.
    
    ### `/geno-agents register <role>`
    Register this session as an agent with the given role. If a `.geno-agents` file exists in the current directory, read role/description/capabilities from it instead.
    
    To register from `.geno-agents` file:
    ```bash
    geno-agents register "$(grep '^role:' .geno-agents | sed 's/^role: *//')" \
      --desc "$(grep '^description:' .geno-agents | sed 's/^description: *//')" \
      --project "$(basename $(pwd))" \
      --session-id "${CLAUDE_SESSION_ID:-}"
    ```
    
    To register with a custom role:
    Use the `register_agent` MCP tool with the provided role.
    
    After registering, confirm by showing the agent card via `list_agents`.
    
    ### `/geno-agents update`
    Update this agent's card. Parse the arguments for:
    - `--working-on "description"` — what you're currently doing
    - `--using resource` — shared resource you're using (browser, api, etc.)
    - `--status busy|available` — availability
    
    Use the `update_agent` MCP tool.
    
    ### `/geno-agents ls`
    Alias for status — list all agents.
    
    ## Auto-Registration
    
    On session start, the `geno-agents-register.sh` hook automatically registers this session using the `.geno-agents` file in the project root. If no file exists, it infers the role from `CLAUDE.md`.
    
    You can check if you're registered by running `/geno-agents status`.
    
    ## Session ID environment variable
    
    The commands above use `$CLAUDE_SESSION_ID`, which is the session identifier set by Claude Code. Other coding agents (e.g., Gemini CLI, Cursor, Windsurf) may expose their session ID under a different environment variable. The `--session-id` flag accepts any string, so adapt the env var reference to match the agent in use. The Python CLI (`geno_agents/cli.py`) currently falls back to `CLAUDE_SESSION_ID` when no `--session-id` is provided; extending that fallback chain to other agents is tracked as a future improvement.
    
    ## `.geno-agents` File Format
    
    Projects declare their agent identity in a `.geno-agents` file at the repo root:
    
    ```yaml
    role: dev-agent
    description: Feature development and code review
    capabilities:
      - coding
      - testing
      - review
    ```

## geno-agents-supercharge

**Slash command:** `/geno-agents-supercharge`

> Run an extended autonomous work session across benchmark tasks with structured cycles of implementation, reflection, ...

??? info "Observability"

    success_signal: "all planned cycles completed (or early-stopped because tasks are healthy) with checkpoints and session log written" failure_signals: - "cycle agent crashes repeatedly and no checkpoint is written" - "same action fails 3+ times without forward progress" - "git push or Kaggle API errors block all remaining work" knowledge_reads: - "task notebooks and reviews in tasks/" - "CLAUDE.md for architecture rules" - "~/.geno/supercharge/state.json (cross-session memory)" - "previous cycle checkpoints" knowledge_writes: - "session log at geno-agents/supercharge/sessions/<timestamp>/session.md" - "cycle checkpoints at geno-agents/supercharge/sessions/<timestamp>/checkpoints/" - "~/.geno/supercharge/state.json (updated cross-session memory)" - "task reviews in tasks/<task>/review/"

??? example "Full skill definition (Level 4)"

    Run an extended autonomous work session across benchmark tasks with structured cycles of implementation, reflection, and research. Based on Anthropic's harness design patterns for long-running apps.
    
    ## Input
    
    `$ARGUMENTS` — Optional directives. Examples:
    - `go!` — Start with defaults (8 hours, all tasks)
    - `4h change_blindness` — 4 hours on one task
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
    - Reads current state of all tasks (notebooks, reviews, results)
    - Reads CLAUDE.md and any existing reviews
    - Prioritizes what to work on next
    - Writes a sprint plan to `checkpoints/sprint_<n>.md`
    - Considers: which tasks have errors? which lack discriminatory power? which need more items? which haven't been run yet?
    
    ### Implementer (runs most cycles)
    - Picks up the sprint plan
    - Does the actual work: fixes bugs, improves scoring, adds passages, refactors prompts
    - After each change, updates the notebook timestamp and pushes to GitHub
    - Writes a brief handoff note to `checkpoints/impl_<cycle>.md`
    
    ### Evaluator (runs every 2-3 cycles)
    - Pulls latest results from Kaggle using `/gt-kaggle-benchmarks-task-review`
    - If no new results, checks if a run is in progress or needs to be triggered
    - Compares results against previous runs
    - Writes evaluation to the task's `review/` folder
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
    ```
    
    ### Role Rotation
    
    Default rotation pattern per 4-cycle sprint:
    1. **Plan** — assess state, set priorities
    2. **Implement** — work on highest priority item
    3. **Implement** — continue or move to next item
    4. **Evaluate** — pull results, review, adjust
    
    ### Context Management
    
    To handle long runs without context degradation:
    - Each cycle runs as a **separate Agent** with a fresh context
    - The checkpoint file is the handoff document — it must contain everything the next agent needs
    - The session log is append-only and provides full history
    - If a cycle's agent runs into context limits, it writes a checkpoint and the next cycle picks up
    
    ## Execution
    
    ### Startup
    
    1. Parse duration and scope from `$ARGUMENTS`
    2. Create session directory: `geno-agents/supercharge/sessions/<YYYYMMDD-HHMM>/`
    3. Read current state:
       - List all tasks in `tasks/`
       - Check which have Kaggle kernels (via `kaggle kernels list`)
       - Check which have reviews
       - Read CLAUDE.md for architecture rules
    4. Write initial checkpoint with full state assessment
    5. Write session header to `session.md`
    
    ### Main Loop
    
    For each cycle (1 to N):
    1. Read the latest checkpoint
    2. Determine the role based on rotation + needs (e.g., if an error was found, prioritize fixing it)
    3. Launch an Agent with the role's instructions and the checkpoint content
    4. The agent does its work and writes the next checkpoint
    5. Append cycle summary to session.md
    6. If the agent reports "all tasks are in good shape and no more work needed", stop early
    
    ### Shutdown
    
    After all cycles or early stop:
    1. Write final summary to `session.md`
    2. Write final state to `~/.geno/supercharge/state.json`
    3. Report to user what was accomplished
    
    ## Checkpoint Format
    
    ```markdown
    # Checkpoint — Cycle <N>/<Total>
    ## Timestamp
    <ISO 8601>
    
    ## Previous Cycle
    <What the last cycle did, in 2-3 sentences>
    
    ## Task States
    | Task | Status | Last Run | Key Issue | Priority |
    |------|--------|----------|-----------|----------|
    | change_blindness | needs-rerun | 2026-03-31 04:15 UTC | scoring too strict | P1 |
    | attentional_blink | not-linked | never | needs Kaggle task created | P2 |
    | ... | ... | ... | ... | ... |
    
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
    - If Kaggle API errors, note it and move to implementation work that doesn't need results
    - Never force-push or do destructive git operations
    
    ## What NOT to Do
    
    - Don't spend multiple cycles on the same issue without trying a different approach
    - Don't create new tasks without using `/gt-kaggle-benchmarks-task-generate`
    - Don't modify notebooks without updating the timestamp
    - Don't push broken code — verify changes make sense before committing
    - Don't ignore CLAUDE.md rules (self-contained notebooks, llm as list, etc.)
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-agents-supercharge \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = all planned cycles completed (or early-stopped because all tasks are healthy) with session log and final checkpoint written
    - `failure` = loop terminated due to repeated cycle failures, unrecoverable git/Kaggle errors, or no forward progress after 3 retries
    - `abandoned` = user stopped early

## geno-agents-tasks-start

**Slash command:** `/geno-agents-tasks-start`

> Pick up a task from the current workspace's geno-notes project scope, plan if needed, and start executing

??? info "Observability"

    success_signal: "task marked done via geno-notes with milestone journal entry summarizing what was accomplished" failure_signals: - "no project scope found and user aborts initialization" - "task execution blocked and user cannot resolve blocker" - "geno-notes CLI errors prevent task state transitions" knowledge_reads: - "geno-notes project-scope task list (active + backlog)" - "CLAUDE.md / project instructions for project context" - "task details via geno-notes show" knowledge_writes: - "geno-notes journal entries (milestone, finding, bug, decision)" - "plan file at geno-notes path/plans/<task-id>.md (medium/large tasks)" - "task status transitions (backlog -> active -> done)"

??? example "Full skill definition (Level 4)"

    Pick up a task from this workspace's `geno-notes` project scope (discovered automatically by `geno-notes path --project`) and start working on it.
    
    **Workspace-only.** This skill does not read from or write to the global geno-notes scope. If the user wants to start a task that lives globally, they should either `geno-notes promote <task> --to project` first, or invoke it manually outside this skill.
    
    Uses the `geno-notes` CLI (`~/.local/bin/geno-notes` or on PATH).
    
    ## Input
    
    The user optionally provides a task description or number as `$ARGUMENTS`. If empty, show the task list and ask which one to start.
    
    ## Workflow
    
    ### 0. Confirm we can proceed
    
    Immediately check that a project scope exists:
    
    ```bash
    geno-notes path --project 2>/dev/null
    ```
    
    If the command exits non-zero (no project scope found in cwd or ancestors):
    
    1. **Ask the user upfront** using `AskUserQuestion` with these options:
       - **Initialize here** — run `geno-notes init --project` in the current directory.
       - **Proceed without prompts** — auto-run `geno-notes init --project` here and don't stop for a confirmation on future gaps this session.
       - **Abort** — they want to handle it outside this skill.
    
    2. Only once a project scope exists, continue to step 1.
    
    If the user has already chosen "Proceed without prompts" earlier in the session, skip the `AskUserQuestion` and just run `geno-notes init --project` silently.
    
    ### 1. Load context
    
    ```bash
    geno-notes list --project --status active --json    # current active tasks
    geno-notes list --project --status backlog --json   # candidates to start
    ```
    
    Also read any `CLAUDE.md` or project instructions for project context.
    
    ### 2. Select the task
    
    - If `$ARGUMENTS` is provided, pass it to `geno-notes show <pattern> --project` to confirm a unique match. If the CLI exits non-zero with multiple candidates, show them and ask the user to disambiguate.
    - If no arguments, use `AskUserQuestion`. Show up to 4 options — Active tasks first, then Backlog. Label = task title; description = `[<status>] <id>`. Include an "Other" option so the user can specify a task outside the top 4.
    - If the task is already in Active, skip to step 3.
    - If the task is in Backlog, run:
      ```bash
      geno-notes start <task-id-or-pattern> --project
      ```
    
    ### 3. Understand the task
    
    ```bash
    geno-notes show <task-id> --project   # frontmatter + body + journal refs
    ```
    
    Assess complexity:
    
    - **Small task** (single-file change, config tweak, quick addition): skip step 4; go to step 5.
    - **Medium/large task** (multi-file, research needed, design decisions): proceed to step 4.
    
    ### 4. Plan (for medium/large tasks)
    
    Use `EnterPlanMode`. Explore the codebase, design an approach, resolve open questions with the user.
    
    Save the plan to `$(geno-notes path --project)/plans/<task-id>.md` (same id as the task file). Structure:
    
    ```markdown
    # Plan: <task title>
    
    ## Goal
    <What does "done" look like?>
    
    ## Approach
    <Numbered steps>
    ```
    
    Once the user approves, call `ExitPlanMode`.
    
    ### 5. Execute
    
    - Work through the task (or the plan steps).
    - At meaningful progress points, log a timestamped entry linked to the task:
      ```bash
      geno-notes note "<what just happened>" --task <task-id> --project --kind milestone
      ```
      Use `--kind finding` for discovered facts, `--kind bug` for problems hit, `--kind decision` for design calls. Default `note` is fine for routine updates. Log milestones, not every small step.
    - If you hit a blocker, stop and ask the user.
    
    ### 6. Complete
    
    ```bash
    geno-notes note "<summary of what was done>" --task <task-id> --project --kind milestone
    geno-notes done <task-id> --project
    ```
    
    Then tell the user what was accomplished and suggest what to start next:
    
    ```bash
    geno-notes list --project --status backlog
    ```
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-agents-tasks-start \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = task marked done via `geno-notes done` with a summary milestone logged
    - `failure` = task could not be completed due to unresolved blocker, missing project scope (user aborted), or repeated CLI errors
    - `abandoned` = user stopped early
