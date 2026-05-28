---
title: geno-dev-worktrees-manage
description: Manage git worktrees
---

# geno-dev-worktrees-manage

`/geno-dev-worktrees-manage "[list|create|switch|prune] [args...]"`

> Manage git worktrees

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` can optionally specify:
- A subcommand: `list`, `create`, `switch`, `prune` (default: `list`)
- Subcommand-specific arguments (see each section below)

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Zero Footprint Policy

This skill NEVER modifies a project's tracked files — no `.gitignore` edits, no `CLAUDE.md` changes, no config file additions. All geno artifacts live either:
- Outside the repo (workspace mode), or
- Inside `.geno/` within the repo (inline mode), with agent-level rules to avoid committing them.

## Safety: Protected Worktrees

Before ANY operation, run `git worktree list --porcelain` and classify each entry by its path:

1. **Claude Code worktrees** — path contains `/.claude/worktrees/`
   NEVER modify, remove, or interact with these. They are managed by Claude Code's agent isolation system.
   In listings, label them `[claude-code]`.

2. **geno-tools meta-harness worktrees** — path starts with `$HOME/.geno/`
   These are global skillset worktrees managed by geno-tools (e.g. `~/.geno/geno-dev/worktrees/exp-1`). Show in listings labeled `[geno-tools]`. Never prune without explicit user confirmation and a warning that these are managed by geno-tools. Never create worktrees inside `~/.geno/`.

3. **User worktrees** — everything else. Managed normally by this skill.

## Agent Rules

When operating inside a worktree created by this skill (whether workspace or inline mode):

- NEVER `git add` the `.geno/` directory or any of its contents.
- NEVER stage `CLAUDE.local.md` for commit.
- When running `git add .` or `git add -A`, always follow up by unstaging: `git reset HEAD .geno/ CLAUDE.local.md 2>/dev/null` before committing.
- These paths belong to the geno tooling layer, not to the project.

## Workflow

### 1. Detect environment

- Run `git rev-parse --git-dir` to confirm we are in a git repo. If not, tell the user and stop.
- Run `git worktree list --porcelain` to get structured worktree data.
- Classify each worktree per the Safety rules above.
- **Workspace detection**: check if `../.geno/workspace.yaml` exists (current repo is inside a workspace) or if `.geno/workspace.yaml` exists in cwd (cwd IS the workspace root). If found, set workspace mode and record the workspace path.

### 2. Route to subcommand

Parse `$ARGUMENTS` for the subcommand. If none given, default to `list`.

---

### Subcommand: list

Show a table of all worktrees:

| Column | Source |
|---|---|
| Path | Shortened with `~` for home directory |
| Branch | Branch name or `(detached)` |
| HEAD | Short commit hash |
| Status | Clean or dirty — run `git -C <path> status --porcelain` |
| Category | `[user]`, `[claude-code]`, or `[geno-tools]` |

If in workspace mode, also scan `<workspace>/.geno/worktrees/` for worktrees belonging to other repos in the workspace and show them grouped by repo.

If there are no worktrees beyond the main one, say so and suggest `create` to get started. If no workspace is set up, mention that `/geno-dev-workspaces-init` can create one.

---

### Subcommand: create \<branch\> [--from \<base\>]

1. Validate that `<branch>` does not already exist as a worktree.
2. Determine the base:
   - If `--from <base>` is given, use that ref.
   - Otherwise, use HEAD.
3. Choose the worktree path based on mode:
   - **Workspace mode** (`../.geno/workspace.yaml` exists): place at `<workspace>/.geno/worktrees/<repo>/<branch>/`
     - The `<repo>/` prefix groups worktrees by repo in multi-repo workspaces.
   - **Inline mode** (no workspace): place at `<repo>/.geno/worktrees/<branch>/`
     - Create `.geno/worktrees/` if it doesn't exist.
     - Do NOT edit `.gitignore`. Remind the user that `.geno/` should not be committed and that agent rules are active to prevent accidental staging.
4. Run: `git worktree add <path> -b <branch> <base>`
   - If the branch already exists (but has no worktree), use `git worktree add <path> <branch>` without `-b`.
5. Create a `CLAUDE.local.md` in the new worktree with:
   ```markdown
   # Worktree: <branch>

   This is a geno-managed worktree. Do not commit `.geno/` or `CLAUDE.local.md`.
   ```
6. Report the created path and suggest the user can `cd` into it or use `switch` to get the path later.

---

### Subcommand: switch \<name-or-branch\>

1. Find the worktree matching `<name-or-branch>` (fuzzy match against branch names and directory names from the worktree list).
2. If the match is a Claude Code worktree, refuse and explain why.
3. Print the absolute path.
4. Tell the user: "Run `cd <path>` in your terminal to switch, or start a new agent session in that directory."

Note: The agent cannot change the user's shell working directory. This subcommand is informational — it helps the user find and navigate to worktrees.

---

### Subcommand: prune [--dry-run]

1. Identify candidates for removal:
   - Worktrees whose branch has been merged into main/master
   - Worktrees whose branch no longer exists on the remote (use `git branch -vv` to check tracking)
   - Worktrees marked as prunable by git (directory was manually deleted)
2. Exclude all Claude Code worktrees — never touch.
3. For geno-tools worktrees, include in the candidate list but add a `[geno-tools]` warning label.
4. Present the list to the user via `AskUserQuestion`:
   - Show each candidate with path, branch, and reason for pruning
   - Options: "Remove all", "Let me pick", "Cancel"
5. If `--dry-run` was specified or user chose "Cancel", stop and show what would have been removed.
6. For each confirmed removal:
   - Run `git worktree remove <path>` (or `git worktree remove --force <path>` if dirty, after user confirms the force)
   - If the branch was merged, offer to delete it: `git branch -d <branch>`
7. Run `git worktree prune` to clean up stale administrative files.
8. Show summary of what was removed.

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-dev-worktrees-manage \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = subcommand completed (worktrees listed, created, located, or pruned as requested)
- `failure` = not a git repo, worktree creation/removal failed, or safety violation encountered
- `abandoned` = user cancelled prune operation or stopped early

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-dev`, `geno-dev-workspaces-init`

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-dev](index.md)
