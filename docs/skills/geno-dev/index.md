---
title: geno-dev
description: Developer and infrastructure utilities — task execution from lab notes, git commit history rewriting, worktree manage...
---

# geno-dev

Developer and infrastructure utilities — task execution from lab notes, git commit history rewriting, worktree manage...

[:material-github: GitHub](https://github.com/42euge/geno-dev){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-dev-branches-audit](#geno-dev-branches-audit) | `/geno-dev-branches-audit` | Audit all branches across a workspace or repo — find branches needing PRs, PRs ready to merge, an... |
| [geno-dev-commits-rewrite](#geno-dev-commits-rewrite) | `/geno-dev-commits-rewrite` | Rewrite git commit history into a clean narrative (backup + soft reset + restage). |
| [geno-dev-feature-ship](#geno-dev-feature-ship) | `/geno-dev-feature-ship` | End-to-end feature shipping — discuss scope, create a GitHub issue, branch, implement, and open a... |
| [geno-dev-issue-work](#geno-dev-issue-work) | `/geno-dev-issue-work` | Select a GitHub issue or JIRA ticket and start working on it, with a choice of normal interactive... |
| [geno-dev-loops-cruise](#geno-dev-loops-cruise) | `/geno-dev-loops-cruise` | Plan-driven sequential execution loop — execute a plan one step at a time. |
| [geno-dev-loops-turbocharge](#geno-dev-loops-turbocharge) | `/geno-dev-loops-turbocharge` | Spec-driven convergence loop — iterate until all acceptance criteria pass. |
| [geno-dev-prs-check](#geno-dev-prs-check) | `/geno-dev-prs-check` | Check open PRs for repos in the current session and show which ones may need to be closed. |
| [geno-dev-scheduling-snooze](#geno-dev-scheduling-snooze) | `/geno-dev-scheduling-snooze` | Snooze the current session — delay work until a specified time using natural language ("3:30 AM",... |
| [geno-dev-sessions-fork](#geno-dev-sessions-fork) | `/geno-dev-sessions-fork` | Fork an agent session — extract its full context and start a new session that continues where the... |
| [geno-dev-tasks-start](#geno-dev-tasks-start) | `/geno-dev-tasks-start` | Pick up a task from lab notes, assess scope, plan if needed, execute, and mark done. |
| [geno-dev-workspaces-init](#geno-dev-workspaces-init) | `/geno-dev-workspaces-init` | Create development workspaces from GitHub issues, JIRA tickets, repo names, or feature ideas. Clo... |
| [geno-dev-worktrees-manage](#geno-dev-worktrees-manage) | `/geno-dev-worktrees-manage` | Manage git worktrees — list, create, switch, and prune. |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-dev — Developer Utilities
    
    Dev and infrastructure skills for AI coding agents. Task execution, git history rewriting, worktree management, workspace creation, and session forking.
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `/geno-dev-tasks-start [description]` | Pick up a task from lab notes, assess scope, plan if needed, execute, and mark done |
    | `/geno-dev-commits-rewrite` | Rewrite git commit history into a clean narrative (backup + soft reset + restage) |
    | `/geno-dev-worktrees-manage [list\|create\|switch\|prune]` | Manage git worktrees — list, create, switch, and prune |
    | `/geno-dev-workspaces-init [config\|list\|<text>]` | Create development workspaces from issues, tickets, repos, or ideas |
    | `/geno-dev-sessions-fork [session]` | Fork an agent session — extract context to continue in a new session |
    
    ## Runtime
    
    No venv or scripts — pure markdown workflows.

## geno-dev-branches-audit

**Slash command:** `/geno-dev-branches-audit`
  **Arguments:** `[repo|--all]`

> Audit all branches across a workspace or repo — find branches needing PRs, PRs ready to merge, and stale branches to clean up.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` can be:
    
    - Empty — audits the current repo (from `git remote -v`)
    - A repo name or `owner/repo` — audits that specific repo
    - `--all` — if inside a workspace, audits all repos listed in `.geno/workspace.yaml`

??? example "Full skill definition (Level 4)"

    # Audit Branches
    
    Audit all branches across a workspace or repo to answer: "What's the status of everything?" For each branch, determines whether a PR exists, what state it's in, and what action is needed — surfacing branches that need PRs, PRs ready to merge, and stale branches to clean up.
    
    ## Input
    
    `$ARGUMENTS` can be:
    
    - Empty — audits the current repo (from `git remote -v`)
    - A repo name or `owner/repo` — audits that specific repo
    - `--all` — if inside a workspace, audits all repos listed in `.geno/workspace.yaml`
    
    ## Workflow
    
    ### 1. Resolve repos
    
    - If `--all` and inside a workspace: read `.geno/workspace.yaml` and collect all repo entries (url + path).
    - If a repo argument is given: use it (expand bare names to `42euge/<name>`).
    - Otherwise: read `git remote -v` from cwd to get the current repo's `owner/repo` and local path.
    
    If no repo can be resolved, tell the user and stop.
    
    For each repo, determine the local clone path:
    - In workspace mode: `<workspace>/<repo.path>/`
    - Otherwise: the current working directory
    
    ### 2. Discover branches
    
    For each repo, collect all non-default branches from three sources:
    
    **a. Local branches:**
    
    ```bash
    git -C <repo-path> branch --format='%(refname:short) %(upstream:short) %(committerdate:iso8601)'
    ```
    
    **b. Worktree branches:**
    
    ```bash
    git -C <repo-path> worktree list --porcelain
    ```
    
    Parse the output to extract branches checked out in worktrees. Record each worktree path.
    
    **c. Remote-only branches (no local tracking branch):**
    
    ```bash
    git -C <repo-path> branch -r --format='%(refname:short)' | grep -v HEAD
    ```
    
    Include remote branches that have no corresponding local branch (strip the `origin/` prefix and check). These represent branches pushed by other agents or sessions.
    
    **Determine the default branch:**
    
    ```bash
    git -C <repo-path> symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||'
    ```
    
    If that fails, fall back to checking for `main` then `master`. Exclude the default branch from the audit list.
    
    Also exclude `gh-pages` — it is a deployment branch, not a feature branch.
    
    Deduplicate: if a branch appears in both local and worktree lists, merge the entries (keep the worktree path info).
    
    Filter out any branches checked out in paths containing `/.claude/worktrees/` — these are managed by Claude Code's isolation system and are not part of the user's branch workflow.
    
    ### 3. Analyze each branch
    
    For each branch, gather:
    
    **a. Commits ahead of default branch:**
    
    ```bash
    git -C <repo-path> rev-list --count origin/<default>..<branch>
    ```
    
    If the branch only exists on the remote (no local), use:
    
    ```bash
    git -C <repo-path> rev-list --count origin/<default>..origin/<branch>
    ```
    
    **b. Last commit date:**
    
    ```bash
    git -C <repo-path> log -1 --format='%ci' <branch>
    ```
    
    **c. PR status on GitHub:**
    
    ```bash
    gh pr list --repo <owner/repo> --head <branch> --state all --json number,title,state,isDraft,reviewDecision,url,mergedAt,mergeable --limit 1
    ```
    
    Using `--state all` captures open, merged, and closed PRs. If multiple PRs exist for the same branch, use the most recent one.
    
    **d. Worktree association:**
    
    Check if this branch has an active worktree (from step 2b). Record the worktree path if so.
    
    ### 4. Classify each branch
    
    Assign exactly one status tag. Evaluate in this order (first match wins):
    
    | Tag | Condition |
    |-----|-----------|
    | `PR MERGED` | PR exists with `state: MERGED` and branch still exists locally or on remote |
    | `PR CLOSED` | PR exists with `state: CLOSED` (not merged) and branch still exists |
    | `PR APPROVED` | PR is open and `reviewDecision: APPROVED` |
    | `PR BLOCKED` | PR is open and (`reviewDecision: CHANGES_REQUESTED` or `mergeable: CONFLICTING`) |
    | `PR DRAFT` | PR is open and `isDraft: true` |
    | `PR OPEN` | PR is open (none of the above conditions) |
    | `STALE` | No PR exists, has commits ahead, and last commit is 30+ days old |
    | `NEEDS PR` | No PR exists and branch has 1+ commits ahead of default |
    | `NO CHANGES` | Branch exists but has 0 commits ahead of default |
    
    ### 5. Render the table
    
    For each repo, output an H2 header and a markdown table sorted by status tag priority (PR MERGED first as cleanup candidates, then actionable items, then informational):
    
    Columns:
    
    | Column | Source |
    |--------|--------|
    | Branch | Branch name |
    | Commits | Number of commits ahead of default |
    | Age | Days since last commit |
    | Worktree | Worktree path (shortened with `~`) or `—` |
    | PR | PR number with link (e.g., `[#42](url)`) or `—` |
    | Status | The tag from step 4 |
    
    Example output:
    
    ```
    ## geno-dev (42euge/geno-dev)
    
    | Branch | Commits | Age | Worktree | PR | Status |
    |--------|---------|-----|----------|----|--------|
    | feat/old-feature | 3 | 45d | — | [#47](url) | PR MERGED |
    | chore/cleanup | 1 | 60d | — | — | STALE |
    | feat/new-auth | 5 | 2d | ~/.geno/worktrees/geno-dev/feat/new-auth | — | NEEDS PR |
    | docs/improve-site | 8 | 1d | — | [#52](url) | PR OPEN |
    | feat/gt-snooze | 12 | 3d | ~/.geno/worktrees/geno-dev/feat/gt-snooze | [#55](url) | PR DRAFT |
    | stale-experiment | 0 | 90d | — | — | NO CHANGES |
    ```
    
    ### 6. Suggested actions
    
    After the table, group branches by action type and print specific, copy-pasteable commands:
    
    **Cleanup (merged/closed PRs, no-change branches):**
    
    ```
    Delete merged branch feat/old-feature:
      git -C <repo-path> branch -d feat/old-feature && git push origin --delete feat/old-feature
    
    Delete no-change branch stale-experiment:
      git -C <repo-path> branch -d stale-experiment
    ```
    
    **Ready to merge:**
    
    ```
    Merge PR #52 (docs/improve-site, approved):
      gh pr merge 52 --repo 42euge/geno-dev
    ```
    
    **Branches needing PRs:**
    
    ```
    Open PR for feat/new-auth (5 commits ahead):
      gh pr create --head feat/new-auth --repo 42euge/geno-dev
    ```
    
    **Stale branches (30+ days, no PR):**
    
    ```
    Stale: chore/cleanup (60 days, 1 commit ahead) — open a PR or delete:
      gh pr create --head chore/cleanup --repo 42euge/geno-dev
      git -C <repo-path> branch -D chore/cleanup && git push origin --delete chore/cleanup
    ```
    
    Only show action groups that have at least one branch.
    
    ### 7. Overall summary
    
    Print a one-line summary per repo:
    
    ```
    geno-dev: 6 branches — 1 needs PR, 2 open PRs (1 draft), 1 merged (cleanup), 1 stale, 1 no changes
    ```
    
    If `--all` was used, add a combined summary across all repos.
    
    If there are PRs with `PR APPROVED` status, highlight them prominently:
    
    ```
    Ready to merge: PR #52 (docs/improve-site) — approved, no conflicts
    ```
    
    ## Don'ts
    
    - Do NOT create, merge, close, or delete anything. This skill is strictly read-only — it audits and suggests, never mutates.
    - Do NOT fetch or pull. Work with whatever state is already local. If a branch exists only on the remote, use `origin/<branch>` refs.
    - Do NOT include the default branch (main/master) or `gh-pages` in the audit.
    - Do NOT show Claude Code worktrees (paths containing `/.claude/worktrees/`) — these are managed by Claude Code's isolation system.
    - Do NOT prompt the user for input during the audit. Run to completion and present results.

## geno-dev-commits-rewrite

**Slash command:** `/geno-dev-commits-rewrite`
  **Arguments:** `[branch] [--onto <base>]`

> Rewrite git commit history into a clean narrative (backup + soft reset + restage).

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` can optionally specify:
    - A branch name (default: current branch)
    - `--onto <base>` to specify the base branch (default: auto-detect merge-base with main/master, or rewrite from root if on main)

??? example "Full skill definition (Level 4)"

    # Rewrite Commit History
    
    Rewrite git commit history so it tells a clear, logical narrative — as if the work was done in clean, intentional steps from the start.
    
    ## Input
    
    `$ARGUMENTS` can optionally specify:
    - A branch name (default: current branch)
    - `--onto <base>` to specify the base branch (default: auto-detect merge-base with main/master, or rewrite from root if on main)
    
    ## Workflow
    
    ### 1. Analyze current state
    
    - Run `git log --oneline` to see the full commit history
    - Run `git status` to check for uncommitted changes
    - Run `git diff` to see unstaged changes
    - If there are uncommitted changes, stage and commit them first with a temporary message before proceeding
    - Identify the range of commits to rewrite:
      - If on main/master: rewrite from root (all commits)
      - If on a feature branch: rewrite from merge-base with main/master
    
    ### 2. Understand the work
    
    - Read through all the diffs in the commit range (`git diff <base>..HEAD` or full diff from root)
    - Read geno-notes journal if it exists for context on what was done and in what order
    - Read geno-notes tasks if they exist to understand the logical units of work
    - Identify the logical narrative: what are the natural "chapters" of this work?
    
    ### 3. Plan the new history
    
    Use `AskUserQuestion` to present the proposed commit plan to the user. Show:
    - Number of new commits
    - Each commit's summary (one line) and what files/changes it includes
    - The narrative arc (why this ordering makes sense)
    
    Use 2 options: "Looks good" and "Let me adjust" (where they can type feedback).
    
    Guidelines for good narrative commits:
    - Each commit should be a single logical unit of work that makes sense on its own
    - Commits should build on each other in a natural progression
    - Early commits set up foundations, later ones add features/refinements
    - Keep commits atomic: don't mix unrelated changes
    - Typical narrative: scaffold → core data models → implementation → tests/validation → polish
    - 3-8 commits is usually the sweet spot
    - Every commit message should explain the "why", not just the "what"
    - Use conventional commit style if the repo already uses it
    
    ### 4. Execute the rewrite
    
    **IMPORTANT:** Before rewriting, create a backup branch: `git branch backup-before-rewrite`
    
    Then use `git reset --soft <base>` (or `git reset --soft --root` if rewriting from root) to unstage all commits while keeping all file changes in the working tree.
    
    For each planned commit:
    1. Stage only the files belonging to that logical unit (`git add <specific files>`)
    2. Commit with the crafted message
    3. Verify with `git status` that remaining files are as expected
    
    Use `git add -p` or specific file paths — never `git add .` for intermediate commits (only OK for the final commit if all remaining files belong together).
    
    End the commit messages with:
    ```
    Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
    ```
    
    ### 5. Verify and push
    
    - Run `git log --oneline` to show the new history
    - Run `git diff backup-before-rewrite` to confirm no content was lost (should show empty diff)
    - If the branch has a remote and user confirms, force push: `git push --force-with-lease`
    - Tell the user the backup branch name in case they need to recover
    
    ### 6. Clean up
    
    - Ask user if they want to delete the backup branch
    - If yes, delete it: `git branch -d backup-before-rewrite`

## geno-dev-feature-ship

**Slash command:** `/geno-dev-feature-ship`
  **Arguments:** `<feature description or issue URL>`

> End-to-end feature shipping — discuss scope, create a GitHub issue, branch, implement, and open a PR.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` is either a freeform feature description or an existing GitHub issue URL. If empty, ask the user what they want to build.

??? example "Full skill definition (Level 4)"

    # Ship Feature
    
    Take a feature idea from discussion through to a pull request: scope the work with the user, create a GitHub issue, branch, implement, and open a PR.
    
    ## Input
    
    `$ARGUMENTS` is either a freeform feature description or an existing GitHub issue URL. If empty, ask the user what they want to build.
    
    ## Workflow
    
    ### 1. Scope the feature
    
    If `$ARGUMENTS` is a GitHub issue URL, fetch it with `gh issue view` and skip to step 2.
    
    Otherwise, start a conversation with the user to understand what they want:
    
    - Ask clarifying questions to nail down the requirements
    - Identify the target repo (use `git remote -v` in the current directory, or ask)
    - Agree on the approach before moving forward
    
    Do not rush past this step. The goal is a shared understanding of what "done" looks like.
    
    ### 2. Create a GitHub issue
    
    Draft the issue based on the scoping conversation:
    
    - Title: concise, under 70 characters
    - Body: problem statement, proposed approach, scope (what's in / what's out)
    
    Present the draft to the user with `AskUserQuestion` for approval. Create with `gh issue create`. Record the issue number for the branch name and PR.
    
    Skip this step if `$ARGUMENTS` was already an issue URL.
    
    ### 3. Create a branch
    
    Create a feature branch from the current default branch:
    
    ```
    git checkout -b <descriptive-branch-name>
    ```
    
    Branch name should reflect the feature (e.g., `add-dep-management`, `fix-auth-token`). Push with `-u` to set up tracking.
    
    ### 4. Implement
    
    - Explore the codebase to understand the relevant code
    - For non-trivial work, use `EnterPlanMode` to design the approach and get user approval, then `ExitPlanMode` to execute
    - Implement the feature, committing logical units as you go
    - Update documentation (CLAUDE.md, README, etc.) if the feature changes public behavior
    - Run any available tests or linters to verify correctness
    
    ### 5. Open a pull request
    
    Create the PR with `gh pr create`:
    
    - Title: short, matches the feature
    - Body: summary bullets, link to the issue (`Closes #N`), test plan
    - Target the default branch
    
    Present the PR URL to the user.
    
    ### 6. Wrap up
    
    Summarize what was shipped: the issue, branch, PR, and key implementation decisions. If there are follow-up items (future scope from step 1), mention them so nothing is lost.

## geno-dev-issue-work

**Slash command:** `/geno-dev-issue-work`
  **Arguments:** `[issue number, JIRA key, search query, or URL]`

> Select a GitHub issue or JIRA ticket and start working on it, with a choice of normal interactive mode or autonomous loop mode.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` is optional. Can be:
    
    - A GitHub issue number (e.g., `42`)
    - A JIRA ticket key (e.g., `PROJ-1234`)
    - A URL to a GitHub issue or JIRA ticket
    - A search query (e.g., `auth bug`)
    - Empty — show open issues and let the user pick

??? example "Full skill definition (Level 4)"

    # Work on Issue
    
    Pick a GitHub issue or JIRA ticket and start working on it. Offers two execution modes: normal (interactive, back-and-forth with the user) or loop (autonomous work with periodic check-ins).
    
    ## Input
    
    `$ARGUMENTS` is optional. Can be:
    
    - A GitHub issue number (e.g., `42`)
    - A JIRA ticket key (e.g., `PROJ-1234`)
    - A URL to a GitHub issue or JIRA ticket
    - A search query (e.g., `auth bug`)
    - Empty — show open issues and let the user pick
    
    ## Workflow
    
    ### 1. Detect issue source
    
    Determine whether we're working with GitHub or JIRA based on the input:
    
    - **Bare number** (e.g., `42`) → GitHub issue in the current repo
    - **JIRA key** (e.g., `PROJ-1234`, matches `[A-Z]+-\d+`) → JIRA ticket
    - **URL containing `github.com`** → GitHub issue (extract owner/repo/number)
    - **URL containing `atlassian.net` or `jira`** → JIRA ticket (extract key)
    - **Text or empty** → GitHub issue search in the current repo
    
    For GitHub: run `gh repo view --json nameWithOwner -q .nameWithOwner` to confirm the current repo. If not in a git repo or no GitHub remote, tell the user and stop.
    
    For JIRA: the user must have the JIRA CLI (`jira`) or a configured MCP server. If neither is available, ask the user to provide the ticket details manually.
    
    ### 2. Select an issue
    
    **GitHub path:**
    
    If `$ARGUMENTS` is a number, fetch it directly with `gh issue view <number>`.
    
    If `$ARGUMENTS` is text, search with `gh issue list --search "<query>" --json number,title,labels,assignees --limit 10`.
    
    If no arguments, list open issues with `gh issue list --json number,title,labels,assignees --limit 15`.
    
    Present the results to the user with `AskUserQuestion`. Each option shows the issue number, title, and labels. Let the user pick one.
    
    **JIRA path:**
    
    Fetch the ticket details. Try `jira issue view <KEY> --plain` if the CLI is available, or use the JIRA MCP server if configured.
    
    If `$ARGUMENTS` is a search query with no matching JIRA key pattern, search with `jira issue list --query "text ~ '<query>'" --plain` or ask the user to provide the ticket key directly.
    
    ### 3. Understand the issue
    
    **GitHub:** Read the full issue body and comments with `gh issue view <number>`.
    
    **JIRA:** Read the ticket description, acceptance criteria, and comments.
    
    Summarize the issue for the user: what needs to happen, any constraints or context from the comments.
    
    ### 4. Choose execution mode
    
    Use `AskUserQuestion` to ask the user how they want to work on this:
    
    - **Normal mode** — interactive back-and-forth. You implement, ask questions when stuck, and the user reviews as you go. Best for exploratory or ambiguous issues.
    - **Loop mode** — autonomous execution with periodic status updates. You work independently, checking in at key milestones. Best for well-defined issues with clear acceptance criteria.
    
    ### 5. Choose workspace strategy
    
    Use `AskUserQuestion` to ask the user where to work:
    
    - **Worktree** — create an isolated git worktree so the current working tree stays clean. Best when the user has in-progress work on the current branch or wants parallel development.
    - **In-place** — work directly in the current repo clone. Simpler, but changes the working tree state.
    
    **Worktree path:**
    
    Delegate to `/geno-dev-worktrees-manage create` to create the worktree. It handles safety checks (protected worktrees, zero footprint policy) and picks the correct worktree location based on the workspace configuration. Pass the branch name from step 6 as the argument. Then work inside the new worktree directory for all subsequent steps.
    
    **In-place path:**
    
    Continue in the current directory. Create a feature branch as usual.
    
    ### 6. Set up the branch
    
    Create a feature branch from the default branch:
    
    - **GitHub:** `<number>-<slug>` (e.g., `19-add-dep-management`)
    - **JIRA:** `<KEY>-<slug>` (e.g., `PROJ-1234-migrate-db-schema`)
    
    Where `<slug>` is a short kebab-case summary of the issue title. Push with `-u` to set up tracking.
    
    ### 7a. Normal mode
    
    Work interactively:
    
    - Explore the codebase to understand the relevant code
    - For non-trivial changes, use `EnterPlanMode` to propose an approach, get user approval, then `ExitPlanMode`
    - Implement the fix or feature
    - Ask the user when you hit ambiguity or need a decision
    - When done, create a PR with `gh pr create`. For GitHub issues, link with `Closes #N`. For JIRA tickets, include the ticket key in the PR title (e.g., `PROJ-1234: Fix auth token`) and body. Present the URL.
    
    ### 7b. Loop mode
    
    Work autonomously using `ScheduleWakeup` to self-pace:
    
    **First iteration:**
    
    - Explore the codebase and build context
    - Draft a plan (save it as a comment on the issue or present it briefly)
    - Start implementing
    
    **Each subsequent iteration:**
    
    - Continue where you left off
    - Commit logical units as you go
    - At each wake-up, assess: am I blocked? is there a decision the user needs to make?
    - If blocked or need input, stop the loop and ask the user
    - If making progress, schedule the next wake-up and keep going
    
    **Finishing:**
    
    - Run available tests or linters
    - Create a PR with `gh pr create`. For GitHub issues, link with `Closes #N`. For JIRA, include the ticket key in the title and body.
    - Stop the loop and present the PR URL to the user
    
    Use `ScheduleWakeup` with the `/loop` prompt to continue each iteration. Choose delay based on the work: 60–90s for active implementation, 120–270s if waiting on a build or test run.

## geno-dev-loops-cruise

**Slash command:** `/geno-dev-loops-cruise`
  **Arguments:** `[task] [--plan <file>]`

> Plan-driven sequential execution loop — execute a plan one step at a time.

??? info "Overview (Level 3)"

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

??? example "Full skill definition (Level 4)"

    # Cruise Loop
    
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
    
    ## Runtime
    
    No venv or scripts — pure markdown workflow. Uses Agent subagents for step execution with checkpoint-based handoff.

## geno-dev-loops-turbocharge

**Slash command:** `/geno-dev-loops-turbocharge`
  **Arguments:** `[task] [--spec <file>] [--max <n>]`

> Spec-driven convergence loop — iterate until all acceptance criteria pass.

??? info "Overview (Level 3)"

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

??? example "Full skill definition (Level 4)"

    # Turbocharge Loop
    
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
    
    ## Runtime
    
    No venv or scripts — pure markdown workflow. Uses `ScheduleWakeup` for self-pacing within `/loop`.

## geno-dev-prs-check

**Slash command:** `/geno-dev-prs-check`
  **Arguments:** `[repo|--all]`

> Check open PRs for repos in the current session and show which ones may need to be closed.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` can be:
    
    - Empty — uses the current repo (from `git remote -v`)
    - A repo name or `owner/repo` — checks that specific repo
    - `--all` — if inside a workspace, checks all repos listed in `.geno/workspace.yaml`

??? example "Full skill definition (Level 4)"

    # Check PRs
    
    Check open pull requests for repos in the current session. Produces a table with PR status, review state, and links — highlighting PRs that may need to be closed (merged branches, stale, draft, or superseded).
    
    ## Input
    
    `$ARGUMENTS` can be:
    
    - Empty — uses the current repo (from `git remote -v`)
    - A repo name or `owner/repo` — checks that specific repo
    - `--all` — if inside a workspace, checks all repos listed in `.geno/workspace.yaml`
    
    ## Workflow
    
    ### 1. Resolve repos
    
    - If `--all` and inside a workspace: read `.geno/workspace.yaml` and collect all repo URLs.
    - If a repo argument is given: use it (expand bare names to `42euge/<name>`).
    - Otherwise: read `git remote -v` from cwd to get the current repo's `owner/repo`.
    
    If no repo can be resolved, tell the user and stop.
    
    ### 2. Fetch open PRs
    
    For each repo, run:
    
    ```bash
    gh pr list --repo <owner/repo> --state open --json number,title,headRefName,baseRefName,author,createdAt,updatedAt,isDraft,reviewDecision,url,labels,mergeable --limit 50
    ```
    
    ### 3. Classify each PR
    
    For each open PR, determine a **status tag**:
    
    | Tag | Condition |
    |-----|-----------|
    | `CLOSEABLE` | Head branch has been merged into base (or deleted) — PR is stale |
    | `STALE` | No updates in the last 30 days |
    | `DRAFT` | PR is marked as draft |
    | `BLOCKED` | Review decision is `CHANGES_REQUESTED` or mergeable is `CONFLICTING` |
    | `APPROVED` | Review decision is `APPROVED` — ready to merge |
    | `OPEN` | None of the above — normal open PR |
    
    To detect merged branches, run:
    
    ```bash
    git ls-remote --heads <repo-url> <head-ref>
    ```
    
    If the remote branch no longer exists and the PR is open, tag it `CLOSEABLE`.
    
    ### 4. Render the table
    
    Output a markdown table sorted by status tag priority: `CLOSEABLE` first, then `STALE`, `BLOCKED`, `DRAFT`, `APPROVED`, `OPEN`.
    
    Columns:
    
    | Column | Source |
    |--------|--------|
    | # | PR number |
    | Title | PR title (truncated to 50 chars) |
    | Author | `author.login` |
    | Branch | `headRefName` → `baseRefName` |
    | Age | Days since `createdAt` |
    | Status | The tag from step 3 |
    | Link | Full PR URL — always included |
    
    Example output:
    
    ```
    ## PRs for 42euge/geno-dev
    
    | # | Title | Author | Branch | Age | Status | Link |
    |---|-------|--------|--------|-----|--------|------|
    | 47 | Remove legacy auth middleware | 42euge | fix/auth → main | 45d | CLOSEABLE | https://github.com/42euge/geno-dev/pull/47 |
    | 52 | Add worktree safety checks | 42euge | feature/wt-safety → main | 12d | APPROVED | https://github.com/42euge/geno-dev/pull/52 |
    | 55 | WIP: Refactor config loader | 42euge | refactor/config → main | 3d | DRAFT | https://github.com/42euge/geno-dev/pull/55 |
    
    3 open PRs — 1 closeable, 1 approved, 1 draft
    ```
    
    ### 5. Summary line
    
    After the table, print a one-line summary: total count and breakdown by status tag (only include tags that have at least one PR).
    
    If there are `CLOSEABLE` PRs, add:
    
    ```
    💡 Close stale PRs: gh pr close <number> --repo <owner/repo>
    ```
    
    ### 6. Multi-repo output
    
    If `--all` was used, repeat steps 2–5 for each repo with an H2 header per repo. End with a combined summary across all repos.

## geno-dev-scheduling-snooze

**Slash command:** `/geno-dev-scheduling-snooze`
  **Arguments:** `<time expression> [prompt]`

> Snooze the current session — delay work until a specified time using natural language ("3:30 AM", "in 2 hours", "tomorrow at 9am"). Wraps ScheduleWakeup with smart time parsing.

??? info "Overview (Level 3)"

    ## Input
    
    `<args>` contains a time expression and optionally a prompt describing what to do when the snooze ends.
    
    **Time expression** — the first part of the argument, parsed as one of:
    
    | Format | Examples | Resolution |
    |---|---|---|
    | Absolute clock time | `3:30 AM`, `15:30`, `3:30am` | Next occurrence of that time today, or tomorrow if already past |
    | Relative duration | `in 2 hours`, `in 30 minutes`, `45m`, `2h` | From now |
    | Named time | `tomorrow at 9am`, `tonight at midnight` | Resolved to absolute then to seconds |
    
    **Prompt** — everything after the time expression. If provided, this is passed to `ScheduleWakeup` as the prompt to fire on wakeup. If omitted, the skill asks the user what they'd like to do when the snooze ends.

??? example "Full skill definition (Level 4)"

    # Snooze
    
    Delay the current session's work until a specified time. Parses natural language time expressions and schedules a wakeup via the `ScheduleWakeup` tool.
    
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

## geno-dev-sessions-fork

**Slash command:** `/geno-dev-sessions-fork`

> Fork an agent session — extract its full context and start a new session that continues where the original left off.

??? info "Overview (Level 3)"

    Fork an agent session: extract the full context (environment, files touched, conversation history) and produce a structured markdown document suitable for continuing the work in a new session.
    
    ## Usage
    
    ```
    /geno-dev-sessions-fork [session] [--output <file>] [--max-messages <N>]
    ```
    
    ## Prerequisites
    
    - `geno-mon` must be installed and available on `$PATH`
    
    ## Workflow
    
    1. **Discover sessions** — run `geno-mon list` to show recent sessions
    2. **Select session** — use the user's argument or ask them to pick one
    3. **Extract context** — run `geno-mon fork <session>` to extract the session context
    4. **Deliver** — write the context to a file (if `--output` given) or display it
    
    *[...truncated — expand Level 4 for full definition]*

??? example "Full skill definition (Level 4)"

    # geno-dev-sessions-fork
    
    Fork an agent session: extract the full context (environment, files touched, conversation history) and produce a structured markdown document suitable for continuing the work in a new session.
    
    ## Usage
    
    ```
    /geno-dev-sessions-fork [session] [--output <file>] [--max-messages <N>]
    ```
    
    ## Prerequisites
    
    - `geno-mon` must be installed and available on `$PATH`
    
    ## Workflow
    
    1. **Discover sessions** — run `geno-mon list` to show recent sessions
    2. **Select session** — use the user's argument or ask them to pick one
    3. **Extract context** — run `geno-mon fork <session>` to extract the session context
    4. **Deliver** — write the context to a file (if `--output` given) or display it
    
    ### Step 1 — Discover sessions
    
    ```bash
    geno-mon list
    ```
    
    If the user provided a session argument (number, partial ID, or path), skip the picker and go to step 3.
    
    ### Step 2 — Select session
    
    If no session was specified, show the list output and ask the user which session to fork.
    
    ### Step 3 — Extract context
    
    ```bash
    geno-mon fork <session>                    # display to stdout
    geno-mon fork <session> -o context.md      # write to file
    geno-mon fork <session> -m 20             # limit to last 20 user messages
    ```
    
    The fork output is a structured markdown document with these sections:
    
    - **Environment** — working directory, git branch, model
    - **Files Modified** — files the session edited or created
    - **Files Read** — files read but not modified
    - **Commands Run** — unique shell commands executed (last 30, deduplicated)
    - **Conversation History** — user messages with assistant responses and tool usage summaries
    
    ### Step 4 — Deliver
    
    - If `--output <file>` was given, confirm the file was written
    - Otherwise, display the context to the user
    - Suggest how to use it: paste into a new agent session prefixed with "Continue the work described in this context"
    
    ## Options
    
    | Flag | Description |
    |---|---|
    | `<session>` | Session number, partial ID, or JSONL path (default: latest) |
    | `-o <file>`, `--output <file>` | Write output to a file instead of stdout |
    | `-m <N>`, `--max-messages <N>` | Maximum user messages to include (default: 50) |
    
    ## Use cases
    
    - **Session continuation** — pick up where a session left off after it ended or was interrupted
    - **Handoff** — pass session context to a different model or agent configuration
    - **Knowledge transfer** — share what a session accomplished with other agents or team members
    - **Debugging** — extract a full record of what happened in a session for analysis

## geno-dev-tasks-start

**Slash command:** `/geno-dev-tasks-start`
  **Arguments:** `[task description or number]`

> Pick up a task from lab notes, assess scope, plan if needed, execute, and mark done.

??? info "Overview (Level 3)"

    ## Input
    
    The user optionally provides a task description or number as `$ARGUMENTS`. If empty, show the task list and ask which one to start.

??? example "Full skill definition (Level 4)"

    # Start Task
    
    Pick up a task from geno-notes and start working on it.
    
    ## Input
    
    The user optionally provides a task description or number as `$ARGUMENTS`. If empty, show the task list and ask which one to start.
    
    ## Workflow
    
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

## geno-dev-workspaces-init

**Slash command:** `/geno-dev-workspaces-init`
  **Arguments:** `[config|list|<freeform text>]`

> Create development workspaces from GitHub issues, JIRA tickets, repo names, or feature ideas. Clone repos into color-coded folders with metadata and agent rules.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` is either a utility subcommand (`config`, `list`) or freeform text describing what to work on.

??? example "Full skill definition (Level 4)"

    # Create Workspace
    
    Create isolated development workspaces by cloning repos into the user's preferred code space. Accepts freeform input — the skill infers whether it's a GitHub issue, JIRA ticket, repo names, or a feature idea.
    
    ## Input
    
    `$ARGUMENTS` is either a utility subcommand (`config`, `list`) or freeform text describing what to work on.
    
    ## Zero Footprint Policy
    
    This skill never modifies a project's tracked files. All geno artifacts (`.geno/`, `CLAUDE.local.md`) live in the workspace directory, which is outside any repo's working tree.
    
    ## Config System
    
    Workspace settings live at `~/.geno/config.yaml`. Auto-created on first use if missing.
    
    ```yaml
    workspaces:
      mode: color                # code space method — determines folder strategy
      base_path: "~"
      color:                     # settings for mode: color
        default: code-purp
        folders:
          - code-red
          - code-blue
          - code-purp
          - code-indigo
    ```
    
    The `mode` field selects the code space method. Currently supported: `color`. Future modes (e.g., `flat`, `project`, `date`) can be added by defining a new key under `workspaces` with their own settings.
    
    ## Naming Convention
    
    Workspace directory names encode the source and context:
    
    | Source | Format | Example |
    |---|---|---|
    | GitHub issue | `GH-{repo}-{number}-{slug}-ws` | `GH-geno-dev-42-fix-auth-token-ws` |
    | JIRA ticket | `{PROJECT-NUMBER}-{slug}-ws` | `PROJ-1234-migrate-db-schema-ws` |
    | Repos / Idea | `{slug}-ws` | `voice-coding-assist-ws` |
    
    Slug rules: AI-generated, 5–15 characters, 3–4 hyphenated words. Must be filesystem-safe (lowercase, hyphens only).
    
    ## Workflow
    
    ### 1. Load config
    
    - Read `~/.geno/config.yaml`.
    - If the file does not exist, create it with the defaults shown above.
    - Read `mode` to determine the folder strategy.
    - For `color` mode: read `default` folder and `folders` list.
    
    ### 2. Parse input and infer intent
    
    If `$ARGUMENTS` starts with `config` or `list`, route to that subcommand (see below) and stop.
    
    If `$ARGUMENTS` is empty, use `AskUserQuestion` to ask "What are you working on?" with a freeform text option.
    
    Otherwise, infer the mode from the freeform text:
    
    1. **Contains a `github.com` URL** (e.g., `https://github.com/42euge/geno-dev/issues/42`)
       → **GitHub issue mode**. Extract owner, repo name, and issue number from the URL.
    
    2. **Matches `[A-Z]+-\d+` pattern** (e.g., `PROJ-1234`, `TEAM-56`)
       → **JIRA ticket mode**. The matched string is the ticket ID.
    
    3. **Looks like repo names** (words that match known geno-ecosystem repo names, or `owner/repo` patterns, or GitHub URLs without issue paths)
       → **Repos mode**. Each word/URL is a repo to clone.
    
    4. **Anything else** (natural language description)
       → **Idea mode**. Treat the text as a feature description.
    
    5. **Ambiguous** (could be repo names or a description)
       → Use `AskUserQuestion` to clarify: "Did you mean repos to clone, or a feature description?" with options for each.
    
    ### 3. Resolve repos
    
    #### GitHub issue mode
    
    1. Run `gh issue view <url> --json title,body,labels,assignees` to fetch issue details.
    2. The repo from the URL is the primary repo — always included.
    3. Scan the issue body for references to other repos (look for `github.com/42euge/geno-*` URLs or `geno-*` mentions).
    4. If additional repos are found, suggest them via `AskUserQuestion` (multi-select: "Include these related repos?").
    5. Generate the slug from the issue title (3–4 hyphenated words, 5–15 chars).
    6. Workspace name: `GH-{repo}-{number}-{slug}-ws`
    
    #### JIRA ticket mode
    
    1. No API call — the ticket ID is used for naming only.
    2. Since JIRA tickets don't imply a repo, prompt the user to select repos.
    3. Scan the geno-ecosystem repos directory. For each repo, read its `.geno-agents` file to get role, description, and capabilities.
    4. Present repos via `AskUserQuestion` with multi-select. Each option shows the repo name and its description from `.geno-agents`.
    5. Ask for a short description (or use any additional text from `$ARGUMENTS` after the ticket ID) to generate the slug.
    6. Workspace name: `{TICKET-ID}-{slug}-ws`
    
    #### Repos mode
    
    1. For each repo argument:
       - If it's a full URL → use as-is
       - If it's `owner/repo` → expand to `https://github.com/{owner}/{repo}`
       - If it's a bare name → expand to `https://github.com/42euge/{name}`
    2. Validate each with `gh repo view <repo> --json name,url 2>/dev/null`. If validation fails, warn the user and ask to continue or fix.
    3. Generate the slug from the repo names or ask the user for one.
    4. Workspace name: `{slug}-ws`
    
    #### Idea mode
    
    1. Read `.geno-agents` from every repo directory under the geno-ecosystem path:
       `/Users/euge/Library/Mobile Documents/iCloud~md~obsidian/Documents/Everything/research/kaggle/gemma-4-good-hackathon/geno-ecosystem/repos/`
       For each, extract: role, description, capabilities.
    2. Also run `gh repo list 42euge --limit 50 --json name,description` to discover repos not in the local ecosystem directory.
    3. Analyze the idea description against repo descriptions and capabilities. Rank by relevance.
    4. Present the top 3–5 suggested repos via `AskUserQuestion` with multi-select. Each option shows the repo name and why it's relevant.
    5. Generate the slug from the idea description.
    6. Workspace name: `{slug}-ws`
    
    ### 4. Confirm with user
    
    Use `AskUserQuestion` to present the workspace plan:
    - Workspace name (the generated directory name)
    - Color folder (the default from config, e.g., `~/code-purp/`)
    - Repos to clone (with URLs)
    
    Options:
    - "Create" — proceed
    - "Change color" — show available color folders as options
    - "Change name" — accept freeform text for a custom name
    
    ### 5. Create workspace
    
    For `color` mode:
    
    ```bash
    # Ensure color folder exists
    mkdir -p ~/<color>/
    
    # Create workspace structure
    mkdir -p ~/<color>/<workspace-name>/.geno
    
    # Clone each repo
    git clone <url-1> ~/<color>/<workspace-name>/<repo-1>
    git clone <url-2> ~/<color>/<workspace-name>/<repo-2>
    ```
    
    Write `.geno/workspace.yaml`:
    
    ```yaml
    ticket: GH-geno-dev-42     # or PROJ-1234, or null
    slug: fix-auth-token
    status: active
    repos:
      - url: https://github.com/42euge/geno-dev
        path: geno-dev
      - url: https://github.com/42euge/geno-tools
        path: geno-tools
    color: code-purp
    created: 2026-04-25T12:00:00Z
    source: issue               # issue | repos | idea
    source_ref: https://github.com/42euge/geno-dev/issues/42
    ```
    
    Write `CLAUDE.local.md` at the workspace root:
    
    ```markdown
    # Workspace: <workspace-name>
    
    <Ticket/description context>
    Repos: <repo-1>, <repo-2>
    
    ## Agent Rules
    - Do not commit `.geno/` or `CLAUDE.local.md` in any repo in this workspace.
    - When staging files, always exclude `.geno/` and `CLAUDE.local.md`.
    - Worktrees for repos in this workspace live at `../.geno/worktrees/<repo>/<branch>/`.
    ```
    
    ### 6. Report
    
    Tell the user:
    - Workspace created at `~/<color>/<workspace-name>/`
    - Repos cloned: list each with its path
    - Next steps: `cd ~/<color>/<workspace-name>/<repo>/` to start working
    - Mention: `/geno-dev-worktrees-manage` is workspace-aware and will put worktrees in `.geno/worktrees/`
    
    ---
    
    ## Subcommand: config
    
    Manage workspace configuration at `~/.geno/config.yaml`.
    
    - `config` (no args) → display current mode and settings
    - `config mode <mode>` → switch code space method
    - For `color` mode:
      - `config default <color>` → set the default color folder
      - `config add <color>` → add a new color to the folders list
      - `config remove <color>` → remove a color (with `AskUserQuestion` confirmation)
    
    Read the file, modify the relevant field, write it back. Use YAML formatting.
    
    ---
    
    ## Subcommand: list
    
    List all workspaces across all configured color folders.
    
    1. Read `~/.geno/config.yaml` to get the folders list (for `color` mode).
    2. For each color folder, scan for directories ending in `-ws` or `-WS` (case-insensitive).
    3. For each match:
       - If `.geno/workspace.yaml` exists → parse metadata (ticket, repos, status, date, source)
       - If directory ends in `-WS` (uppercase) and no `workspace.yaml` → tag as `[legacy]`
       - If directory ends in `-ws` (lowercase) and no `workspace.yaml` → tag as `[unmanaged]`
    4. Display as a table:
    
    | Workspace | Color | Ticket | Repos | Status | Created | Tags |
    |---|---|---|---|---|---|---|
    | `GH-geno-dev-42-fix-auth-ws` | code-purp | GH-geno-dev-42 | geno-dev, geno-tools | active | 2026-04-25 | |
    | `geno-dev-WS` | code-purp | — | — | — | — | [legacy] |
    | `lottie-creator-ws` | code-purp | — | — | — | — | [unmanaged] |
    
    Sort: active workspaces first, then by creation date (newest first). Legacy and unmanaged at the end.

## geno-dev-worktrees-manage

**Slash command:** `/geno-dev-worktrees-manage`
  **Arguments:** `[list|create|switch|prune] [args...]`

> Manage git worktrees — list, create, switch, and prune.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` can optionally specify:
    - A subcommand: `list`, `create`, `switch`, `prune` (default: `list`)
    - Subcommand-specific arguments (see each section below)

??? example "Full skill definition (Level 4)"

    # Manage Worktrees
    
    Manage git worktrees for the current repository — create worktrees for feature branches, see what exists, switch context, and clean up stale ones.
    
    ## Input
    
    `$ARGUMENTS` can optionally specify:
    - A subcommand: `list`, `create`, `switch`, `prune` (default: `list`)
    - Subcommand-specific arguments (see each section below)
    
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
