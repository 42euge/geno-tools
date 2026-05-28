---
title: geno-agents-tasks-start
description: Pick up a task from the current workspace's geno-notes project scope, plan if needed, and start executing
---

# geno-agents-tasks-start

`/geno-agents-tasks-start`

> Pick up a task from the current workspace's geno-notes project scope, plan if needed, and start executing

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

The user optionally provides a task description or number as `$ARGUMENTS`. If empty, show the task list and ask which one to start.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

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

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-notes`

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-agents](index.md)
