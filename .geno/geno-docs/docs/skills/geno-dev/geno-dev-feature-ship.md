---
title: geno-dev-feature-ship
description: End-to-end feature shipping
---

# geno-dev-feature-ship

`/geno-dev-feature-ship "<feature description or issue URL>"`

> End-to-end feature shipping

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` is either a freeform feature description or an existing GitHub issue URL. If empty, ask the user what they want to build.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 0. Load knowledge context

Run `geno-notes context --skill geno-dev-feature-ship [--task <id>]` and review the returned bundle (active tasks, recent journal, relevant wiki, skill health). Use these to inform your approach — prior failures, relevant patterns, and active tasks provide context the user may not have stated explicitly.

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

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-dev](index.md)
