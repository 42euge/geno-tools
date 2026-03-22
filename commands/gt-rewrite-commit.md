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
- Read `geno-tools/labnotes/notes.md` if it exists for context on what was done and in what order
- Read `geno-tools/labnotes/tasks.md` if it exists to understand the logical units of work
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
