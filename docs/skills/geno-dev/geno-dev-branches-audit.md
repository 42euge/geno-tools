---
title: geno-dev-branches-audit
description: Audit all branches across a workspace or repo
---

# geno-dev-branches-audit

`/geno-dev-branches-audit "[repo|--all]"`

> Audit all branches across a workspace or repo

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` can be:

- Empty — audits the current repo (from `git remote -v`)
- A repo name or `owner/repo` — audits that specific repo
- `--all` — if inside a workspace, audits all repos listed in `.geno/workspace.yaml`

</div>

<div class="zoom-section zoom-section-4" markdown>

---

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

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-dev`

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-dev](index.md)
