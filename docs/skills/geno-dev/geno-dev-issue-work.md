---
title: geno-dev-issue-work
description: Select a GitHub issue or JIRA ticket and start working on it, with a choice of normal interactive mode or autonomous ...
---

# geno-dev-issue-work

`/geno-dev-issue-work "[issue number, JIRA key, search query, or URL]"`

> Select a GitHub issue or JIRA ticket and start working on it, with a choice of normal interactive mode or autonomous ...

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` is optional. Can be:

- A GitHub issue number (e.g., `42`)
- A JIRA ticket key (e.g., `PROJ-1234`)
- A URL to a GitHub issue or JIRA ticket
- A search query (e.g., `auth bug`)
- Empty — show open issues and let the user pick

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 0. Load knowledge context

Run `geno-notes context --skill geno-dev-issue-work [--task <id>]` and review the returned bundle (active tasks, recent journal, relevant wiki, skill health). Use these to inform your approach — prior failures, relevant patterns, and active tasks provide context the user may not have stated explicitly.

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

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-dev-worktrees-manage`

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-dev](index.md)
