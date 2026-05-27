---
name: geno-lifecycle-status
description: >-
  Show the installation status of the geno ecosystem — version, commit,
  branch, and freshness of each installed skillset. Use when user says
  /geno-skills-status, wants to check what's installed, or asks about
  ecosystem versions.
allowed-tools: "Bash(geno-tools *) Bash(git *) Bash(ls *) Bash(cat *) Bash(find *) Bash(python3 *) Bash(readlink *) Read(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-skills-status — Ecosystem Installation Status

Shows the current state of every installed geno skillset: version from the manifest, git commit, branch, skill count, and whether the install is behind origin. Also reports the geno-tools version itself and the geno-tools plugin source.

## When to invoke

- The user asks "what's installed", "what version am I on", "is everything up to date".
- Before troubleshooting — to see which skillsets are present and at what revision.
- After running `geno-tools update` to verify results.

## Input

`$ARGUMENTS` — optional:
- **Empty** — report on all installed skillsets
- **A skillset name** (e.g. `geno-dev`, `dev`) — report on just that one in detail

## Workflow

### 1. Report geno-tools itself

Get the geno-tools version and source:

```bash
geno-tools --version
```

Determine where the geno-tools plugin is loaded from. Check the plugin root — this is the repo the agent session loaded geno-tools from. Use `$CLAUDE_PLUGIN_ROOT` if set, otherwise check the known install locations:
- `~/.claude/plugins/geno-tools/`
- The current repo if it has `.claude-plugin/plugin.json`

Report:

```
geno-tools v{version}
  plugin: {plugin-path}
```

### 2. Enumerate installed skillsets

List all installed skillsets from `~/.geno-tools/`:

```bash
ls -d ~/.geno-tools/geno-*/ 2>/dev/null | grep -v geno-bootstrap
```

If `$ARGUMENTS` names a specific skillset, filter to just that one. If the named skillset is not installed, report that and stop.

### 3. Gather per-skillset info

For each installed skillset at `~/.geno-tools/geno-{name}/`:

#### Version and description

Read `genotools.yaml` from the active worktree:

```bash
cat ~/.geno-tools/geno-{name}/active/genotools.yaml
```

Extract `name`, `version`, and `description`. If the manifest is missing, report "(no manifest)".

#### Git state

From the `main/` worktree:

```bash
git -C ~/.geno-tools/geno-{name}/main log --oneline -1
git -C ~/.geno-tools/geno-{name}/main branch --show-current
git -C ~/.geno-tools/geno-{name}/main log --format="%ci" -1
```

Extract: short SHA, commit message, branch name, commit date.

#### Active variant

Check which variant is active:

```bash
readlink ~/.geno-tools/geno-{name}/active
```

This is usually `main`. If it points elsewhere, note the variant.

#### Skill count

Count registered skills:

```bash
find ~/.geno-tools/geno-{name}/active/skills -name "SKILL.md" -mindepth 2 -maxdepth 2 2>/dev/null | wc -l
```

Also check for a root-level `SKILL.md`:

```bash
test -f ~/.geno-tools/geno-{name}/active/SKILL.md && echo "+1 umbrella"
```

#### Freshness (optional — only when reporting all)

Check if the installed commit is behind origin. This requires a fetch, which is slow, so only do this when the user explicitly asks for freshness or passes a single skillset name:

```bash
git -C ~/.geno-tools/geno-{name}/.git fetch --quiet origin 2>/dev/null
git -C ~/.geno-tools/geno-{name}/main log --oneline HEAD..@{upstream} 2>/dev/null | wc -l
```

If behind, report how many commits behind. If the fetch fails (offline, no remote), skip silently.

Only run freshness checks when:
- A single skillset is specified (`$ARGUMENTS` is not empty)
- The user explicitly asks about freshness or "is it up to date"

For the all-skillsets overview, skip fetching to keep the report fast.

#### Dependencies

Read `requires:` from `genotools.yaml`:

```bash
python3 -c "
import yaml, sys
data = yaml.safe_load(open(sys.argv[1]))
for r in data.get('requires', []):
    print(r)
" ~/.geno-tools/geno-{name}/active/genotools.yaml 2>/dev/null
```

### 4. Format the report

#### All skillsets (no argument)

Print a summary table:

```
geno-tools v0.1.0

Installed skillsets:

  Skillset              Version   Commit     Date         Branch   Skills
  ─────────────────────────────────────────────────────────────────────────
  geno-agents           0.1.0     11ac1bb    2026-04-28   main     5
  geno-dev              0.1.0     3eff77d    2026-04-30   main     12
  geno-kaggle           —         f9077a5    2026-04-25   main     4
  geno-media            0.2.0     e582cb0    2026-04-22   main     7
  geno-notes            0.1.0     52c3908    2026-04-29   main     6
  geno-research         0.4.0     34206f5    2026-04-27   main     3

  Total: 6 skillsets, 37 skills
```

Use aligned columns. Mark skillsets with no `genotools.yaml` version as `—`. If the active variant is not `main`, append `(active: {variant})` to the branch column.

#### Single skillset (with argument)

Print detailed info including freshness and dependencies:

```
geno-dev v0.1.0
  Developer and infrastructure utilities — task execution from lab notes,
  git commit history rewriting, worktree management, workspace creation,
  and session forking.

  Commit:   3eff77d — Merge pull request #19 from 42euge/feat/gt-snooze
  Date:     2026-04-30
  Branch:   main
  Active:   main
  Remote:   https://github.com/42euge/geno-dev.git
  Freshness: up to date (or: 3 commits behind origin)

  Skills (12):
    geno-dev                          (umbrella)
    geno-dev-commits-rewrite
    geno-dev-feature-ship
    geno-dev-issue-work
    geno-dev-loops-cruise
    geno-dev-loops-turbocharge
    geno-dev-prs-check
    geno-dev-scheduling-snooze
    geno-dev-sessions-fork
    geno-dev-tasks-start
    geno-dev-workspaces-init
    geno-dev-worktrees-manage

  Dependencies: geno-notes
```

List each skill by reading the `skills/` directory names. Mark the umbrella. List dependencies from `requires:` or "none" if empty.

### 5. Actionable suggestions

After the report, if any issues are detected, suggest next steps:

- Skillsets behind origin: "Run `geno-tools update {name}` to pull latest."
- Skillsets with no manifest: "Add a `genotools.yaml` to {name} for version tracking."
- Active variant not `main`: "Switch back with `geno-tools use {name}@main`."
- Dirty worktree detected: "Uncommitted changes in {name}; `geno-tools update` will skip it."

## Don'ts

- Don't modify any files — this is a read-only status report.
- Don't fetch from origin when showing all skillsets — keep the overview fast.
- Don't use aliased prefixes like `gt-` in output.
- Don't show geno-bootstrap in the list — it's internal infrastructure.
