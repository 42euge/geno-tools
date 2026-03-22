# Start Task

Pick up a task from the project's `geno-tools/labnotes/tasks.md` and start working on it.

## Input

The user optionally provides a task description or number as `$ARGUMENTS`. If empty, show the task list and ask which one to start.

## Workflow

### 1. Load context

- Read `geno-tools/labnotes/tasks.md` in the current working directory
- Read `geno-tools/labnotes/notes.md` for recent context
- Check `geno-tools/labnotes/plans/` for any existing plans related to the task
- Read any CLAUDE.md or project instructions for project context

If `geno-tools/labnotes/` doesn't exist, tell the user to run `/gt-lab-notes create` first and stop.

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

Also save the plan to `geno-tools/labnotes/plans/<task-slug>.md` for future reference, with:

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
- As you make progress, append timestamped notes to `geno-tools/labnotes/notes.md` at key milestones (not every small step — just meaningful progress points)
- If you hit a blocker or need a decision, stop and ask the user

### 6. Complete

When the task is finished:

1. Mark it done in `tasks.md`: change `- [ ]` to `- [x]` and move it to `## Done`
2. Add a final note to `notes.md` summarizing what was done
3. If a plan file was created, leave it as-is for reference
4. Tell the user what was accomplished and suggest what to work on next from the remaining tasks
