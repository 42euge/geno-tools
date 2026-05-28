---
title: geno-dev-tasks-start
description: Pick up a task from lab notes, assess scope, plan if needed, execute, and mark done
---

# geno-dev-tasks-start

`/geno-dev-tasks-start "[task description or number]"`

> Pick up a task from lab notes, assess scope, plan if needed, execute, and mark done

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

The user optionally provides a task description or number as `$ARGUMENTS`. If empty, show the task list and ask which one to start.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 0. Load knowledge context

Run `geno-notes context --skill geno-dev-tasks-start [--task <id>]` and review the returned bundle (active tasks, recent journal, relevant wiki, skill health). Use these to inform your approach — prior failures, relevant patterns, and active tasks provide context the user may not have stated explicitly.

### 1. Load context

- Read `geno-notes tasks` in the current working directory
- Read `geno-notes journal` for recent context
- Check `geno-notes plans/` for any existing plans related to the task
- Read any CLAUDE.md or project instructions for project context

If no geno-notes scope exists (neither `./geno/geno-notes/` nor `~/.geno/geno-notes/`), tell the user to run `geno-notes init --project` first and stop.

### 2. Select the task

- If `$ARGUMENTS` is provided, fuzzy-match it against tasks in **Backlog** and **Active** sections
- If no arguments, use the `AskUserQuestion` tool to present a selection menu. Show **Active** tasks first, then **Backlog** tasks. Use up to 4 options (the most relevant tasks), with each option's label being the task name and description showing its current section (Active/Backlog). The user can also type "Other" to specify a different task.
- If the task is already in **Active**, skip to step 3
- If the task is in **Backlog**, move it to **Active** (change section, keep `- [ ]`)

### 3. Understand the task

Assess the task's scope and complexity:

- **Small task** (single file change, config tweak, quick addition): proceed directly to step 5
- **Medium/large task** (multi-file, research needed, design decisions): proceed to step 4

### 4. Plan (for medium/large tasks)

Use the `EnterPlanMode` tool to switch into plan mode. While in plan mode:

- Explore the codebase to understand what's needed
- Design an approach and present it to the user
- Resolve any open questions

Also save the plan to `geno-notes plans/<task-slug>.md` for future reference, with:

```markdown
# Plan: <task description>

## Goal
<What does "done" look like?>

## Approach
<Numbered steps to complete the task>
```

Once the user approves, use `ExitPlanMode` to leave plan mode and proceed to step 5.

### 5. Execute

- Work through the task (or the plan steps if one was created)
- As you make progress, append timestamped notes to `geno-notes journal` at key milestones (not every small step — just meaningful progress points)
- If you hit a blocker or need a decision, stop and ask the user

### 6. Complete

When the task is finished:

1. Mark it done in `tasks.md`: change `- [ ]` to `- [x]` and move it to `## Done`
2. Add a final note to `notes.md` summarizing what was done
3. If a plan file was created, leave it as-is for reference
4. Tell the user what was accomplished and suggest what to work on next from the remaining tasks

## Completion

When this skill finishes (success, failure, or abandoned), emit a trace:

```bash
geno-trace emit \
  --skill geno-dev-tasks-start \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors> \
  --task <geno-notes task id, if any> \
  --scope <project|global>
```

- `success` = task marked done
- `failure` = task could not be completed (blocker, missing context)
- `abandoned` = user chose to stop or switch tasks

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-notes`

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-dev](index.md)
