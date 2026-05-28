---
title: geno-dev-prs-check
description: Check open PRs for repos in the current session and show which ones may need to be closed
---

# geno-dev-prs-check

`/geno-dev-prs-check "[repo|--all]"`

> Check open PRs for repos in the current session and show which ones may need to be closed

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` can be:

- Empty — uses the current repo (from `git remote -v`)
- A repo name or `owner/repo` — checks that specific repo
- `--all` — if inside a workspace, checks all repos listed in `.geno/workspace.yaml`

</div>

<div class="zoom-section zoom-section-4" markdown>

---

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

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-dev`

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-dev](index.md)
