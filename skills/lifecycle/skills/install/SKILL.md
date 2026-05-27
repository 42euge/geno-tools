---
name: geno-lifecycle-install
description: >-
  Install skills from a local geno ecosystem repo checkout globally via
  npx skills add. Detects the repo from the current directory, accepts a
  path or name as an argument, or offers selection when called from a
  multi-repo workspace. Use when user says /geno-skills-install, wants to
  register local skill changes globally, or test skills from a dev checkout.
argument-hint: "[repo-path|repo-name]"
allowed-tools: "Bash(npx *) Bash(find *) Bash(ls *) Bash(grep *) Bash(git *) Bash(python3 *) Read(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-skills-install — Install Local Skills Globally

Registers all skills from a local geno ecosystem repo checkout as global slash commands across all supported agents. This is the dev-loop companion to `geno-tools install` — instead of cloning from a remote, it installs from whatever is on disk right now so you can test local changes immediately.

## When to invoke

- You've edited a SKILL.md and want to pick up the changes in new agent sessions.
- You've added a new skill directory and need to register it.
- You want to test a skillset branch before merging.
- The user says "install these skills", "register skills globally", or "pick up my skill changes".

## Input

`$ARGUMENTS` — one of:
- **Empty** — detect from context (see Resolution below)
- **A path** — absolute or relative path to a geno repo checkout
- **A repo name** — e.g. `geno-dev`, `geno-media` — resolved as a subdirectory of the current workspace

## Resolution

### 1. Explicit argument

If `$ARGUMENTS` is provided:

- If it's an absolute path or starts with `./` or `../`, use it directly. Verify it's a geno repo (has `genotools.yaml` or a `skills/` directory with at least one `SKILL.md`).
- If it's a repo name (e.g. `geno-dev`), look for it as a subdirectory of the workspace root. The workspace root is the nearest ancestor directory containing `.geno/workspace.yaml`.

### 2. Inside a geno repo

If no argument is given, check the current working directory and its ancestors for `genotools.yaml` or a `skills/` directory. If found, that's the target repo.

### 3. Inside a workspace

If no repo is detected in the current directory, look for `.geno/workspace.yaml` in the current directory or its ancestors. Read the `repos:` list.

- **Single repo** — use it automatically. Resolve its path relative to the workspace root.
- **Multiple repos** — use `AskUserQuestion` to let the user pick:

  > Which repo do you want to install skills from?

  Options: each repo's `path` value from workspace.yaml (e.g. `geno-dev`, `geno-media`). Include an **All** option to install from every repo.

### 4. Nothing found

If none of the above match, tell the user:

> Could not detect a geno ecosystem repo. Run this from inside a geno-* repo checkout or pass a path as an argument.

Stop here.

## Workflow

### 1. Validate the target

Once the repo path is resolved:

```bash
REPO_ROOT="<resolved-path>"
```

Verify the repo is a valid geno skillset:
- Check for `genotools.yaml` at root (read `name` field if present)
- Check for `skills/` directory
- Check for at least one `SKILL.md` (root or under `skills/*/`)

If validation fails, report what's missing and stop.

### 2. Enumerate skills

Find all skill directories that will be registered:

```bash
find "$REPO_ROOT/skills" -name "SKILL.md" -mindepth 2 -maxdepth 2 | sort
```

Also check for a root-level `SKILL.md`:

```bash
test -f "$REPO_ROOT/SKILL.md" && echo "$REPO_ROOT/SKILL.md"
```

Print a summary of what will be installed:

```
Found N skills to install from geno-{name}:
  - geno-{name} (umbrella)
  - geno-{name}-foo-bar
  - geno-{name}-baz-qux
```

### 3. Install skills globally

For each skill directory, run:

```bash
npx --yes skills add "<skill-dir>" --agent '*' --global --yes
```

Where `<skill-dir>` is:
- `$REPO_ROOT` for the root-level SKILL.md (if it exists)
- `$REPO_ROOT/skills/<skill-name>` for each sub-skill

Run these sequentially and capture output. Report success or failure for each.

### 4. Handle "All" (multi-repo)

If the user selected **All** in step 3 of Resolution, repeat steps 1–3 for each repo in the workspace. Process repos sequentially and report a combined summary at the end.

### 5. Report

Print a summary:

```
Installed N skills globally from geno-{name} (<path>):
  ✓ geno-{name}
  ✓ geno-{name}-foo-bar
  ✓ geno-{name}-baz-qux

Skills are now available in new agent sessions.
Current session may need a restart to pick up changes.
```

If any failed:

```
  ✗ geno-{name}-broken — npx error: <message>
```

### 6. Git context (informational)

After installation, show the current git state of the repo for context:

```bash
git -C "$REPO_ROOT" log --oneline -1
git -C "$REPO_ROOT" branch --show-current
```

Report:

```
Source: branch <branch> @ <short-sha> <commit-message>
```

This helps the user know exactly what version of the skills they just installed.

## Don'ts

- Don't clone or fetch — this skill works on the local checkout as-is.
- Don't create venvs, bin symlinks, or worktrees — those are `geno-tools install` responsibilities.
- Don't modify any files in the target repo.
- Don't use `geno-tools install` — this skill calls `npx skills add` directly because it's registering from a local path, not going through the full install flow.
- Don't use aliased prefixes like `gt-` in any output — always use canonical `geno-` prefix.
