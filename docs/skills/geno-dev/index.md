---
title: geno-dev
description: Developer utilities — commits, worktrees, workspaces, feature shipping
---

# geno-dev

Developer utilities — commits, worktrees, workspaces, feature shipping

[:material-github: GitHub](https://github.com/42euge/geno-dev){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-dev-branches-audit](#geno-dev-branches-audit) | `/geno-dev-branches-audit` | Audit all branches across a workspace or repo |
| [geno-dev-commits-rewrite](#geno-dev-commits-rewrite) | `/geno-dev-commits-rewrite` | Rewrite git commit history into a clean narrative (backup + soft reset + restage) |
| [geno-dev-feature-ship](#geno-dev-feature-ship) | `/geno-dev-feature-ship` | End-to-end feature shipping |
| [geno-dev-issue-work](#geno-dev-issue-work) | `/geno-dev-issue-work` | Select a GitHub issue or JIRA ticket and start working on it, with a choice of normal interactive mode or autonomous ... |
| [geno-dev-loops-autopilot](#geno-dev-loops-autopilot) | `/geno-dev-loops-autopilot` | Background monitoring loop |
| [geno-dev-loops-boost](#geno-dev-loops-boost) | `/geno-dev-loops-boost` | Time-boxed focus sessions (Pomodoro) |
| [geno-dev-loops-cruise](#geno-dev-loops-cruise) | `/geno-dev-loops-cruise` | Plan-driven sequential execution loop |
| [geno-dev-loops-drift](#geno-dev-loops-drift) | `/geno-dev-loops-drift` | Question-driven exploration loop |
| [geno-dev-loops-ignition](#geno-dev-loops-ignition) | `/geno-dev-loops-ignition` | Cold-start bootstrap loop |
| [geno-dev-loops-turbocharge](#geno-dev-loops-turbocharge) | `/geno-dev-loops-turbocharge` | Spec-driven convergence loop |
| [geno-dev-prs-check](#geno-dev-prs-check) | `/geno-dev-prs-check` | Check open PRs for repos in the current session and show which ones may need to be closed |
| [geno-dev-scheduling-snooze](#geno-dev-scheduling-snooze) | `/geno-dev-scheduling-snooze` | Snooze the current session |
| [geno-dev-sessions-fork](#geno-dev-sessions-fork) | `/geno-dev-sessions-fork` | Fork an agent session |
| [geno-dev-sessions-remote](#geno-dev-sessions-remote) | `/geno-dev-sessions-remote` | Start a Claude Code session with remote access in a workspace directory |
| [geno-dev-skills-retro](#geno-dev-skills-retro) | `/geno-dev-skills-retro` | Meta-harness |
| [geno-dev-tasks-start](#geno-dev-tasks-start) | `/geno-dev-tasks-start` | Pick up a task from lab notes, assess scope, plan if needed, execute, and mark done |
| [geno-dev-workspaces-init](#geno-dev-workspaces-init) | `/geno-dev-workspaces-init` | Create development workspaces from GitHub issues, JIRA tickets, repo names, or feature ideas |
| [geno-dev-worktrees-manage](#geno-dev-worktrees-manage) | `/geno-dev-worktrees-manage` | Manage git worktrees |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-dev — Developer Utilities
    
    Dev and infrastructure skills for AI coding agents. Task execution, git history rewriting, worktree management, workspace creation, session forking, end-to-end feature shipping, issue-driven development, agentic loops, background monitoring, PR checking and branch auditing, scheduled snoozing, and skill retrospectives.
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `/geno-dev-tasks-start [description]` | Pick up a task from lab notes, assess scope, plan if needed, execute, and mark done |
    | `/geno-dev-commits-rewrite` | Rewrite git commit history into a clean narrative (backup + soft reset + restage) |
    | `/geno-dev-worktrees-manage [list\|create\|switch\|prune]` | Manage git worktrees — list, create, switch, and prune |
    | `/geno-dev-workspaces-init [config\|list\|<text>]` | Create development workspaces from issues, tickets, repos, or ideas |
    | `/geno-dev-sessions-fork [session]` | Fork an agent session — extract context to continue in a new session |
    | `/geno-dev-feature-ship [description\|issue URL]` | End-to-end: scope, issue, branch, implement, and PR |
    | `/geno-dev-issue-work [number\|query\|URL]` | Pick a GitHub issue or JIRA ticket and work on it (normal or loop mode) |
    | `/geno-dev-loops-turbocharge [task] [--spec <file>]` | Spec-driven convergence loop — iterate until all acceptance criteria pass |
    | `/geno-dev-loops-cruise [task] [--plan <file>]` | Plan-driven sequential loop — execute a plan one step at a time |
    | `/geno-dev-loops-autopilot [task] [--watch <tests\|ci\|lint\|git\|all>]` | Background monitoring loop — watch CI, tests, lint, and git state |
    | `/geno-dev-loops-boost [task]` | Pomodoro focus loop — time-boxed work blocks with reflection |
    | `/geno-dev-loops-ignition [goal] [--blueprint <file>]` | Cold-start bootstrap loop — turn a high-level goal into a blueprint and verified first slice |
    | `/geno-dev-prs-check [repo\|--all]` | Check open PRs and flag ones that may need closing |
    | `/geno-dev-branches-audit [repo\|--all]` | Audit all branches — find ones needing PRs, ready to merge, or stale |
    | `/geno-dev-scheduling-snooze <time> [prompt]` | Snooze session until a specified time, then execute a prompt |
    | `/geno-dev-skills-retro [session] [--skill <name>]` | Meta-harness: analyze a failed session and patch the responsible skill |
    
    ## Runtime
    
    No venv or scripts — pure markdown workflows.

## geno-dev-branches-audit

**Slash command:** `/geno-dev-branches-audit`

> Audit all branches across a workspace or repo

??? example "Full skill definition (Level 4)"

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
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-dev-branches-audit \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = audit table rendered with status tags and suggested actions for all resolved repos
    - `failure` = no repos resolved, or git/gh commands failed before producing a usable table
    - `abandoned` = user stopped early

## geno-dev-commits-rewrite

**Slash command:** `/geno-dev-commits-rewrite`

> Rewrite git commit history into a clean narrative (backup + soft reset + restage)

??? example "Full skill definition (Level 4)"

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
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-dev-commits-rewrite \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = commit history rewritten and verified (diff against backup is empty, no content lost)
    - `failure` = rewrite failed mid-way, repo left in inconsistent state, or content was lost
    - `abandoned` = user rejected the proposed commit plan or stopped early

## geno-dev-feature-ship

**Slash command:** `/geno-dev-feature-ship`

> End-to-end feature shipping

??? info "Observability"

    success_signal: "PR created and URL presented to user" failure_signals: - "no GitHub remote available" - "implementation blocked" knowledge_reads: - "GitHub issues (via gh CLI)" knowledge_writes: - "GitHub issue (created)" - "GitHub PR (created)"

??? example "Full skill definition (Level 4)"

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
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-dev-feature-ship \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --produced "github-issue github-pr"
    ```
    
    - `success` = PR created
    - `failure` = could not complete implementation
    - `abandoned` = user stopped before PR

## geno-dev-issue-work

**Slash command:** `/geno-dev-issue-work`

> Select a GitHub issue or JIRA ticket and start working on it, with a choice of normal interactive mode or autonomous ...

??? info "Observability"

    success_signal: "PR created linking the issue" failure_signals: - "step failed twice in loop mode" - "no GitHub remote or JIRA access" knowledge_reads: - "GitHub issues or JIRA tickets" knowledge_writes: - "GitHub PR (created)"

??? example "Full skill definition (Level 4)"

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
    
    ## Completion
    
    When this skill finishes (in either normal or loop mode), emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-dev-issue-work \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --produced "github-pr"
    ```
    
    - `success` = PR created linking the issue
    - `failure` = could not complete (blocked, no access)
    - `abandoned` = user stopped before PR

## geno-dev-loops-autopilot

**Slash command:** `/geno-dev-loops-autopilot`

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
    
    ## Runtime
    
    No venv or scripts — pure markdown workflow. Uses `CronCreate` for 15–30 minute recurring checks over long-running sessions.

## geno-dev-loops-boost

**Slash command:** `/geno-dev-loops-boost`

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
    
    ## Runtime
    
    Pure markdown workflow. Uses `ScheduleWakeup` for time-boxing and `geno-notes` for reflection persistence.

## geno-dev-loops-cruise

**Slash command:** `/geno-dev-loops-cruise`

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
      --skill geno-dev-loops-cruise \
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

## geno-dev-loops-drift

**Slash command:** `/geno-dev-loops-drift`

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
    
    ## Runtime
    
    Pure markdown workflow. Uses `ScheduleWakeup` for self-pacing within `/loop`.

## geno-dev-loops-ignition

**Slash command:** `/geno-dev-loops-ignition`

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
    
    ## Runtime
    
    No venv or scripts — pure markdown workflow. Uses Agent subagents for role handoffs and `ScheduleWakeup` for self-pacing within `/loop`.

## geno-dev-loops-turbocharge

**Slash command:** `/geno-dev-loops-turbocharge`

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
      --skill geno-dev-loops-turbocharge \
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

## geno-dev-prs-check

**Slash command:** `/geno-dev-prs-check`

> Check open PRs for repos in the current session and show which ones may need to be closed

??? example "Full skill definition (Level 4)"

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
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-dev-prs-check \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = PR status table rendered with classification tags and summary for all resolved repos
    - `failure` = no repos resolved, or gh CLI failed to fetch PR data
    - `abandoned` = user stopped early

## geno-dev-scheduling-snooze

**Slash command:** `/geno-dev-scheduling-snooze`

> Snooze the current session

??? example "Full skill definition (Level 4)"

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

## geno-dev-sessions-fork

**Slash command:** `/geno-dev-sessions-fork`

> Fork an agent session

??? example "Full skill definition (Level 4)"

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
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-dev-sessions-fork \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = session context extracted and delivered (displayed or written to file)
    - `failure` = geno-mon not found, fork command failed, or no sessions available
    - `abandoned` = user stopped early or declined to select a session

## geno-dev-sessions-remote

**Slash command:** `/geno-dev-sessions-remote`

> Start a Claude Code session with remote access in a workspace directory

??? example "Full skill definition (Level 4)"

    Launch a Claude Code session with remote access enabled in a target workspace. Opens a new Terminal window running `claude --remote-control`, which provides a URL for connecting from any browser or device.
    
    ## Usage
    
    ```
    /geno-dev-sessions-remote <workspace-path> [--name <session-name>]
    /geno-dev-sessions-remote                   # uses current directory
    ```
    
    ## Arguments
    
    - `$ARGUMENTS` — path to the workspace directory. If omitted, uses the current working directory.
    - `--name <name>` — optional session name for the remote control session. Defaults to the directory basename.
    
    ## Workflow
    
    1. **Resolve path** — if `$ARGUMENTS` contains a path, resolve it. If it's a workspace name, look it up under the user's code directories (`~/code-red/*/`). If empty, use `$PWD`.
    
    2. **Validate** — confirm the directory exists. Check if it's a git repo or contains a `CLAUDE.md`.
    
    3. **Derive session name** — use `--name` if provided, otherwise use the directory basename.
    
    4. **Launch** — open a new Terminal window with `clauded` (alias for `claude --dangerously-skip-permissions`):
       ```bash
       osascript -e '
       tell application "Terminal"
           activate
           do script "cd <resolved-path> && clauded --remote-control <session-name>"
       end tell'
       ```
    
       **To resume a previous session**, use `--continue` (not `--resume`, which opens an interactive picker that blocks in the background):
       ```bash
       clauded --continue --remote-control <session-name>
       ```
    
    5. **Confirm** — tell the user the session is starting and to check the new Terminal window for the remote access URL.
    
    ## Important
    
    - Use `--continue` (resumes most recent session in that directory) rather than `--resume` (interactive picker) since the Terminal may not be visible and interactive input blocks silently.
    - Always use `clauded` (skip permissions) not plain `claude`.
    - The process needs an interactive TTY — cannot run in the background or via `&`.
    
    ## Examples
    
    ```
    /geno-dev-sessions-remote /Users/euge/code-red/comfy-geno-ws/comfyGeno
    /geno-dev-sessions-remote comfyGeno --name comfy
    /geno-dev-sessions-remote   # current directory
    ```
    
    ## Notes
    
    - The remote control session runs in a separate Terminal window because it requires an interactive TTY.
    - The session name is passed to `--remote-control` and used to identify the session in the remote control UI.
    - Remote sessions can be accessed from any device via the URL printed in the Terminal.
    - To stop the session, close the Terminal window or press Ctrl+C.

## geno-dev-skills-retro

**Slash command:** `/geno-dev-skills-retro`

> Meta-harness

??? info "Observability"

    success_signal: "patches applied and accepted by user" failure_signals: - "no actionable signals found in session" - "user rejected all patches" - "transcript not found or unreadable" knowledge_reads: - "~/.geno/traces/ (structured skill traces)" - "~/.geno/health/ (skill health cards)" - "~/.geno/retro/queue.jsonl (batch queue)" - "~/.claude/projects/ (session transcripts)" knowledge_writes: - ".geno/retro/<session-id>/ (analysis artifacts)" - "geno-notes journal (milestones)" - "skill SKILL.md files (patches)"

??? example "Full skill definition (Level 4)"

    Meta-harness for skill self-improvement. Reads a session transcript, identifies where the agent went wrong, traces the failure back to a skill deficiency, and generates a targeted patch to the skill's SKILL.md. The feedback loop: **session fails → retro finds the gap → skill gets patched → next session succeeds**.
    
    ## Input
    
    Parse `$ARGUMENTS` for:
    
    - **Session** — session ID (partial match OK), PID number, or JSONL path (optional — defaults to most recent session in this project)
    - **`--skill <name>`** — skip auto-detection and target a specific skill for patching
    - **`--dry-run`** — analyze and propose changes but don't write them
    - **`--batch`** — process the retro queue at `~/.geno/retro/queue.jsonl` instead of a single session. Each line contains a trace ID referencing a failed skill run. Process all queued items, deduplicate findings, and present a unified patch set.
    
    If no session is given and `--batch` is not set, list the 5 most recent sessions for this project and ask the user to pick one.
    
    ## When to Use
    
    - A session went sideways and you want to prevent the same failure next time
    - The user says "that didn't work" or "the skill keeps doing X wrong"
    - After a turbocharge/cruise loop stalled or failed
    - Periodic skill hygiene — retro the last N sessions to find recurring patterns
    
    Do **not** use for one-off user errors, infrastructure failures (API outage, network), or bugs in external tools.
    
    ## Workflow
    
    ### 1. Locate the transcript
    
    Resolve the session to a JSONL transcript file:
    
    ```bash
    # List sessions for this project
    ls -lt ~/.claude/projects/$(pwd | tr '/' '-' | sed 's/^-//')/*.jsonl | head -5
    ```
    
    Also check session metadata for context:
    
    ```bash
    # Match session metadata by ID prefix
    python3 -c "
    import json, glob
    for f in glob.glob(os.path.expanduser('~/.claude/sessions/*.json')):
        with open(f) as fh:
            s = json.load(fh)
            print(f'{s.get(\"pid\")} | {s.get(\"sessionId\",\"\")[:12]} | {s.get(\"name\",\"unnamed\")} | {s.get(\"cwd\",\"\")}')
    "
    ```
    
    If the user gave a partial ID or PID, match it. If ambiguous, show candidates and ask.
    
    ### 1.5. Check for structured traces (preferred)
    
    Before parsing raw transcripts, check if structured traces exist for this session:
    
    ```bash
    geno-trace list --json --limit 100
    ```
    
    Filter traces matching the session. If traces are found:
    
    - Each trace gives you the skill name, outcome status, error type, tool call count, and thrashing score directly — no need to infer these from raw JSONL.
    - Use `geno-trace health --skill <name>` for each involved skill to see aggregate patterns (success rate, recurring error types, whether the skill already `needs_retro`).
    - For `--batch` mode: read `~/.geno/retro/queue.jsonl`, look up each trace ID via `geno-trace list`, and group findings by skill.
    - Traces with `outcome.status == "failure"` or `outcome.status == "partial"` are the primary retro targets.
    
    If traces exist and provide enough signal (skill name + error type are known), you can skip the raw transcript parsing (step 2) and jump directly to step 4 (trace to skill) with the trace metadata. Fall back to full transcript parsing only when:
    - No traces exist for this session (pre-trace-era sessions)
    - The trace lacks sufficient detail (`error_type` is null and you need to understand *why* it failed)
    
    ### 2. Parse the transcript
    
    Read the JSONL file and extract a structured timeline. Use a python script (inline) to parse:
    
    ```python
    import json, sys
    
    timeline = []
    with open(sys.argv[1]) as f:
        for i, line in enumerate(f):
            obj = json.loads(line.strip())
            t = obj.get('type')
    
            if t == 'user':
                msg = obj.get('message', {}).get('content', '')
                # Detect skill invocations
                is_skill = '<command-name>' in str(msg) or '<command-message>' in str(msg)
                timeline.append({
                    'line': i, 'type': 'user', 'content': msg[:500],
                    'is_skill_invocation': is_skill
                })
    
            elif t == 'assistant':
                blocks = obj.get('message', {}).get('content', '')
                if isinstance(blocks, list):
                    for block in blocks:
                        if isinstance(block, dict):
                            if block.get('type') == 'tool_use':
                                timeline.append({
                                    'line': i, 'type': 'tool_call',
                                    'tool': block.get('name'),
                                    'input_preview': str(block.get('input', {}))[:300]
                                })
                            elif block.get('type') == 'text':
                                timeline.append({
                                    'line': i, 'type': 'assistant_text',
                                    'content': block['text'][:500]
                                })
    
            elif t == 'tool_result':
                is_err = obj.get('is_error', False)
                content = str(obj.get('content', ''))[:500]
                timeline.append({
                    'line': i, 'type': 'tool_result',
                    'is_error': is_err, 'content': content
                })
    
    json.dump(timeline, sys.stdout, indent=2)
    ```
    
    Write the parsed timeline to `.geno/retro/<session-id>/timeline.json`.
    
    ### 3. Identify failure signals
    
    Scan the timeline for these signal types, in order of strength:
    
    #### A. Hard failures (strongest signal)
    
    - **Tool errors**: `tool_result` entries with `is_error: true`
    - **Command failures**: Bash tool results containing non-zero exit codes, "command not found", "No such file", "Permission denied", stack traces
    - **Repeated retries**: Same tool called 3+ times with similar input (agent stuck in a loop)
    
    #### B. User corrections (strong signal)
    
    - **Explicit corrections**: User messages containing negation ("no", "not that", "wrong", "stop", "don't"), redirection ("instead", "actually", "what I meant"), or frustration markers ("again", "still", "keeps")
    - **Abandoned approaches**: User interrupts with a new instruction mid-workflow (the previous approach was failing)
    - **Manual takeover**: User provides the exact command or code to use (agent couldn't figure it out)
    
    #### C. Soft failures (weak signal — needs corroboration)
    
    - **Excessive tool calls**: More than 15 tool calls between user messages (thrashing)
    - **Context loss**: Agent re-reads the same file multiple times
    - **Stalled progress**: Long assistant text blocks with hedging language ("I'm not sure", "let me try", "this might")
    
    For each signal, record:
    - **Where**: line number in transcript
    - **What**: the failure event
    - **Context**: what the agent was trying to do (preceding user message + recent tool calls)
    
    Write findings to `.geno/retro/<session-id>/signals.md`.
    
    ### 4. Trace to skill
    
    Determine which skill (if any) was active when the failure occurred:
    
    1. Scan for skill invocations in user messages (`<command-name>` tags or `/skill-name` patterns)
    2. Map each failure signal to the nearest preceding skill invocation
    3. If `--skill` was provided, filter to only signals relevant to that skill
    
    If no skill was invoked (plain conversation), check if the failure pattern *should* have been handled by an existing skill (e.g., agent tried to do manually what a skill automates). Flag this as a "missing skill trigger" issue.
    
    Read the identified skill's SKILL.md:
    
    ```bash
    # Check installed location first, then repo
    cat ~/.agents/skills/<skill-name>/SKILL.md 2>/dev/null || \
    cat ./skills/<skill-name>/SKILL.md 2>/dev/null
    ```
    
    ### 5. Root cause analysis
    
    Classify each failure into one of these root cause categories:
    
    | Category | Description | Skill fix |
    |---|---|---|
    | **Missing guard** | Skill doesn't check a prerequisite that failed at runtime | Add a prerequisite check or "Step 0" validation |
    | **Wrong approach** | Skill prescribes method A but method B works for this case | Add conditional branch or replace approach |
    | **Missing edge case** | Skill handles the happy path but not this variant | Add handling to Error Recovery or a conditional in the workflow |
    | **Ambiguous instruction** | Skill's wording led the agent to misinterpret | Tighten the language, add an example or "Do NOT" entry |
    | **Missing context** | Skill doesn't tell the agent to gather needed information | Add a context-gathering step early in the workflow |
    | **Stale reference** | Skill references a tool, path, or API that changed | Update the reference |
    | **Missing skill** | No skill covers this workflow — agent improvised and failed | Recommend creating a new skill (don't patch an unrelated one) |
    
    Write the analysis to `.geno/retro/<session-id>/analysis.md`:
    
    ```markdown
    # Retro Analysis — <session-id>
    
    ## Session
    - ID: <session-id>
    - Project: <project path>
    - Date: <timestamp>
    - Skill(s) invoked: <list>
    
    ## Failure Signals
    ### Signal 1: <type>
    - **Line**: <n>
    - **What happened**: <description>
    - **Context**: <what was being attempted>
    
    ## Root Causes
    ### 1. <category>: <one-line summary>
    - **Evidence**: <which signals point to this>
    - **Skill**: <skill-name>
    - **Section**: <which part of the skill is deficient>
    - **Proposed fix**: <what to change>
    ```
    
    ### 6. Generate patch
    
    For each root cause that maps to an existing skill, generate a targeted edit:
    
    - Read the current SKILL.md content
    - Identify the exact section to modify (use line numbers)
    - Write the proposed change as an `old_string → new_string` diff
    - Keep changes minimal — add what's missing, don't rewrite working sections
    - Preserve the skill's existing voice and structure
    
    Present the patch to the user in a clear format:
    
    ```markdown
    ## Proposed Patch: <skill-name>/SKILL.md
    
    ### Change 1: <summary>
    **Root cause**: <category> — <one-line>
    **Section**: <heading path, e.g., "Workflow > Step 3 > Execute">
    
    **Before:**
    > <existing text>
    
    **After:**
    > <proposed text>
    
    **Why**: <one sentence explaining how this prevents the failure>
    ```
    
    If `--dry-run`, stop here. Otherwise, proceed to step 7.
    
    ### 7. Apply (with confirmation)
    
    Use `AskUserQuestion` to confirm each change:
    
    - **Apply all** — write all proposed changes
    - **Apply selectively** — show each change and let the user accept/reject
    - **Save analysis only** — keep the retro artifacts but don't modify skills
    - **Discard** — this wasn't a skill issue
    
    For accepted changes, use the `Edit` tool to modify the skill's SKILL.md. Edit the **repo copy** (under `./skills/<name>/SKILL.md`) — the installed copy at `~/.agents/skills/` is a symlink or will be synced by `geno-tools update`.
    
    #### Mode-aware delivery
    
    After applying patches, create a local branch for the changes:
    
    ```bash
    cd <skill-repo-root>
    git checkout -b retro/<skill-name>-$(date +%Y%m%d)
    git add skills/<skill-name>/SKILL.md
    git commit -m "retro: patch <skill-name> — <root-cause-category>"
    ```
    
    **Dev mode** (check `$GENO_MODE` env var or if cwd is in a geno-* workspace):
    - Push the branch and create a PR with `gh pr create`
    - Scrub the PR body: strip absolute paths (`/Users/...` → `./...`), raw code snippets from user projects, and error messages that might contain secrets
    - PR body should describe *what* was patched and *why* (root cause category), not reproduce raw session content
    
    **User mode** (default):
    - Keep the branch local — do not push
    - Write a notification to `~/.geno/iso/inbox.jsonl`:
      ```bash
      echo '{"type":"retro","skill":"<name>","branch":"retro/<name>-<date>","summary":"<one-line>","timestamp":"<ISO>"}' >> ~/.geno/iso/inbox.jsonl
      ```
    
    After applying:
    
    ```bash
    geno-notes note "Skills retro: patched <skill-name> — <summary of changes>" \
      --project --kind milestone 2>/dev/null || true
    ```
    
    ### 8. Log the retro
    
    Write a summary to `.geno/retro/<session-id>/retro.md`:
    
    ```markdown
    # Retro Summary — <date>
    
    ## Session: <session-id>
    ## Skills patched: <list>
    ## Changes applied: <count>
    
    ### Patches
    1. **<skill>**: <one-line summary of change>
       - Root cause: <category>
       - Prevents: <what failure this addresses>
    
    ## Patterns noticed
    <any recurring themes across this and previous retros — worth watching>
    ```
    
    If this project has a geno-notes scope, also log the retro:
    
    ```bash
    geno-notes note "Retro complete for session <id>: <n> patches applied to <skills>" \
      --project --kind milestone 2>/dev/null || true
    ```
    
    ## Multi-Session Retro
    
    If the user says "retro the last N sessions" or provides multiple session IDs:
    
    1. Run steps 1–5 for each session independently
    2. Before step 6, cross-reference findings:
       - **Recurring failures** — same root cause across sessions → higher priority patch
       - **Contradictory signals** — one session says add X, another says remove X → flag for user
       - **Cascade** — session B failed because session A's skill patch was incomplete → compound fix
    3. Deduplicate patches (don't propose the same edit twice)
    4. Present a unified patch set with frequency annotations ("seen in 3/5 sessions")
    
    ## Feedback Memory Integration
    
    After a retro is applied, check if the root cause reveals a **user preference** or **project convention** that should be saved to memory:
    
    - If the failure was "agent used approach A but user always wants approach B" → this is a feedback memory, not just a skill patch. Save it so the preference applies across skills.
    - If the failure was "agent didn't know about project constraint X" → this is a project memory. Save it.
    
    Only save memories for patterns that transcend the specific skill being patched. Skill-specific fixes go in the skill file, not memory.
    
    ## Error Recovery
    
    - If the transcript JSONL is malformed (truncated, corrupt), parse what you can and note the gap. A partial retro is better than none.
    - If the identified skill doesn't exist (was deleted or renamed), check git history: `git log --oneline --all -- 'skills/*<name>*'`. If found, note the rename. If not, classify as "missing skill."
    - If the user denies all patches, ask what they think the actual issue was. Their answer is valuable feedback — consider saving it as a feedback memory.
    - If `geno-notes` is not available, skip journaling steps — don't let journal failures block the retro.
    
    ## What NOT to Do
    
    - **Don't patch skills for infrastructure failures.** API outages, network errors, and disk full are not skill bugs.
    - **Don't rewrite skills from scratch.** Retros produce targeted patches, not rewrites. If a skill needs a rewrite, that's a separate task.
    - **Don't infer failures that aren't there.** If the session succeeded, say so — not every session needs a patch.
    - **Don't modify the transcript.** Transcripts are immutable records. Analysis goes in `.geno/retro/`, not the JSONL.
    - **Don't apply patches without user confirmation** (unless `--auto` is explicitly passed — not in v0.1).
    - **Don't patch external tools.** If the failure is in `geno-notes`, `git`, or a test runner, note it but don't try to fix their code.
    
    ## Batch Mode
    
    When `--batch` is passed:
    
    1. Read `~/.geno/retro/queue.jsonl`. Each line is a JSON object with at minimum `{"trace_id": "..."}`.
    2. For each trace ID, look up the trace via `geno-trace list --json` and match by ID.
    3. Group traces by skill name. For each skill:
       - Read the skill's health card: `geno-trace health --skill <name>`
       - Collect all failure traces (status = failure or partial)
       - Cross-reference with the raw transcript only if the trace lacks `error_type`
    4. Deduplicate findings — if the same root cause appears across multiple traces, present it once with a frequency annotation ("seen in N traces").
    5. Present a unified patch set per skill, prioritized by:
       - Skills with `needs_retro: true` in their health card (success rate < 70%)
       - Skills with the most failure traces
       - Skills with declining success rates (recent failures outweigh older successes)
    6. After processing, truncate `~/.geno/retro/queue.jsonl` to remove processed entries.
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-dev-skills-retro \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --produced ".geno/retro/<session-id>/retro.md"
    ```
    
    - `success` = patches applied and accepted
    - `failure` = no actionable signals found, or analysis failed
    - `abandoned` = user rejected all patches or stopped early
    
    ## Runtime
    
    No venv or scripts — pure markdown workflow. Uses inline Python for transcript parsing. Retro artifacts live in `.geno/retro/<session-id>/`.

## geno-dev-tasks-start

**Slash command:** `/geno-dev-tasks-start`

> Pick up a task from lab notes, assess scope, plan if needed, execute, and mark done

??? info "Observability"

    success_signal: "task marked done in geno-notes" failure_signals: - "user had to abandon task" - "no geno-notes scope found" knowledge_reads: - "geno-notes tasks" - "geno-notes journal" - "geno-notes plans" knowledge_writes: - "geno-notes journal (milestones)" - "geno-notes plans (if medium/large task)"

??? example "Full skill definition (Level 4)"

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

## geno-dev-workspaces-init

**Slash command:** `/geno-dev-workspaces-init`

> Create development workspaces from GitHub issues, JIRA tickets, repo names, or feature ideas

??? example "Full skill definition (Level 4)"

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

> Manage git worktrees

??? example "Full skill definition (Level 4)"

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
