---
name: geno-data-workspaces-init
description: >-
  Create data workspaces for personal/life skills (taxes, remodel, career, custom).
  Scaffolds a directory with metadata, agent context, and links to related workspaces.
  Use when user says /geno-data-workspaces-init.
argument-hint: "[list|<freeform text>]"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
observability:
  success_signal: "data workspace directory created with metadata and CLAUDE.local.md, registry updated"
  failure_signals:
    - "workspace directory creation failed"
    - "config.yaml missing and could not be created"
    - "user cancelled during confirmation"
  knowledge_reads:
    - "~/.geno/config.yaml (workspace settings)"
    - "~/.geno/data-workspaces.yaml (existing data workspaces)"
  knowledge_writes:
    - "~/.geno/data-workspaces.yaml (registry entry for new workspace)"
    - "<workspace>/.geno/.workspace/workspace.yaml (workspace metadata)"
    - "<workspace>/CLAUDE.local.md (agent context)"
---

# Create Data Workspace

Create data workspaces for personal/life skills that operate on user data, not code. Unlike dev workspaces (which clone repos), data workspaces are lightweight launchpads with metadata linking to where the skill's data actually lives and cross-links to related workspaces.

## Input

`$ARGUMENTS` is either a utility subcommand (`list`) or freeform text describing what to work on. If empty, launch the interactive flow.

## Zero Footprint Policy

This skill never modifies a project's tracked files. All geno artifacts (`.geno/`, `CLAUDE.local.md`) live in the workspace directory.

## Config System

Uses the same `~/.geno/config.yaml` workspace settings as dev workspaces. Auto-created on first use if missing.

```yaml
workspaces:
  mode: color
  base_path: "~"
  color:
    default: code-purp
    folders:
      - code-red
      - code-blue
      - code-purp
      - code-indigo
```

## Known Skills

Hard-coded registry of skills with known data paths and workspace conventions (v0.1):

| Skill | Data Path | Structure | Notes |
|-------|-----------|-----------|-------|
| `geno-taxes` | `~/docs/finance/taxes/` | `TY{year}/` subdirs | External data, workspace is a launchpad |
| `geno-remodel` | `~/docs/home/remodel/` | `{project}/` subdirs | External data, workspace is a launchpad |
| `geno-career` | workspace-local `data/` | `profile.yaml`, `resumes/`, `generated/` | Data lives in workspace; scaffold `data/` on create |
| Custom | user-specified or none | user-defined | Freeform workspace for any data-oriented task |

## Central Registry

All data workspaces are tracked in `~/.geno/data-workspaces.yaml`. This file is created on first workspace creation and updated on each subsequent creation.

```yaml
version: 1
workspaces:
  - slug: taxes-2026
    skill: geno-taxes
    path: "~/code-purp/taxes-2026-ws"
    color: code-purp
    status: active
    data_path: "~/docs/finance/taxes/"
    created: 2026-04-26T00:00:00Z
```

## Workflow

### 1. Load config

- Read `~/.geno/config.yaml`.
- If the file does not exist, create it with the defaults shown above.
- Read `mode` to determine the folder strategy.
- For `color` mode: read `default` folder and `folders` list.

### 2. Route subcommands

If `$ARGUMENTS` starts with `list`, route to the **list** subcommand (see below) and stop.

If `$ARGUMENTS` is empty, proceed to step 3.

If `$ARGUMENTS` contains a known skill name (e.g., `taxes`, `geno-taxes`, `remodel`, `career`) or freeform text, use it to pre-select the skill and skip the skill selection prompt.

### 3. Select skill

Use `AskUserQuestion` to ask "Which skill is this data workspace for?" with options:

- **geno-taxes** — Tax filing (data at `~/docs/finance/taxes/`)
- **geno-remodel** — Home remodel (data at `~/docs/home/remodel/`)
- **geno-career** — Career toolkit (data in workspace)
- **Custom** — Custom data workspace

If the user selects "Custom", use `AskUserQuestion` to ask for a brief description of the workspace purpose.

### 4. Name the workspace

Use `AskUserQuestion` to ask "Name this workspace?" with a suggested default based on the skill:

- **geno-taxes**: suggest `taxes-{current-year}` (e.g., `taxes-2026`)
- **geno-remodel**: suggest `remodel-{project}` — ask for the project name first
- **geno-career**: suggest `career-general` or `career-{focus}` — ask for focus area
- **Custom**: ask for a name

Present the suggested name as the first option (recommended) plus "Custom name" as an alternative.

Slugify the final name: lowercase, hyphens only, 5–25 characters. The workspace directory will be `{slug}-ws`.

### 5. Select color folder

Use `AskUserQuestion` with the color folders from config. Pre-select the default from `~/.geno/config.yaml`.

Options are the folder names (e.g., `code-red`, `code-blue`, `code-purp`, `code-indigo`). Mark the default as "(Recommended)".

### 6. Scan registry and cross-link

Read `~/.geno/data-workspaces.yaml` if it exists. If other data workspaces are registered:

Use `AskUserQuestion` with `multiSelect: true` to ask "Include context from other data workspaces?"

Each option shows: `{slug} ({skill}, {color})` with description `Data: {data_path}`.

Selected workspaces will appear in the `includes:` field of `workspace.yaml` and in the "Linked Workspaces" section of `CLAUDE.local.md`.

If no other data workspaces exist, skip this step.

### 7. Confirm and create

Use `AskUserQuestion` to present the workspace plan with a preview:

```
Workspace: {slug}-ws
Location:  ~/{color}/{slug}-ws/
Skill:     {skill}
Data path: {data_path}
Linked:    {linked-slugs or "none"}
```

Options:
- **Create** (Recommended) — proceed with creation
- **Change color** — go back to color selection
- **Change name** — go back to naming

### 8. Create workspace

#### 8a. Create directory structure

```bash
mkdir -p ~/{color}/{slug}-ws/.geno/.workspace
```

#### 8b. Write workspace metadata

Write `~/{color}/{slug}-ws/.geno/.workspace/workspace.yaml`:

```yaml
type: data
skill: {skill}
slug: {slug}
status: active
repos: []
color: {color}
created: {ISO-8601-timestamp}
source: skill
source_ref: {skill}
data_path: "{data_path}"          # null for custom without a data path
includes:                          # omit if no cross-links
  - slug: {linked-slug}
    path: "~/{linked-color}/{linked-slug}-ws"
    skill: {linked-skill}
```

#### 8c. Write CLAUDE.local.md

Write `~/{color}/{slug}-ws/CLAUDE.local.md`:

```markdown
# Data Workspace: {slug}-ws

{description — one sentence about the workspace purpose}

## Skill

**{skill}** — data at `{data_path}`

## Linked Workspaces

{For each included workspace:}
- **{linked-slug}** ({linked-skill}) — `{linked-path}`
  Data: `{linked-data-path}`

{If no links: "No linked workspaces."}

## Agent Rules
- Do not commit `.geno/` or `CLAUDE.local.md`.
- When staging files, always exclude `.geno/` and `CLAUDE.local.md`.
- This is a **data workspace** — it does not contain git repos to develop.
- The skill's data lives at `{data_path}`, not in this directory.
- When reading or writing data for {skill}, use `{data_path}` as the root.
{If includes: "- Linked workspace data is read-only. Do not modify data in other workspaces without asking."}
```

For **geno-career** (workspace-local data), replace data path references with `./data/` and adjust the agent rules:

```markdown
## Skill

**geno-career** — data at `./data/` (local to this workspace)

## Agent Rules
- Do not commit `.geno/` or `CLAUDE.local.md`.
- When staging files, always exclude `.geno/` and `CLAUDE.local.md`.
- This is a **data workspace** — it does not contain git repos to develop.
- The `data/` directory contains personal information. Never commit or push it.
{If includes: "- Linked workspace data is read-only. Do not modify data in other workspaces without asking."}
```

#### 8d. Scaffold skill-specific data (career only)

For **geno-career**, create the data directory structure:

```bash
mkdir -p ~/{color}/{slug}-ws/data/{resumes,source,generated/resumes,generated/cover-letters}
```

For other skills, their data directories already exist at external paths (`~/docs/...`). If the data directory does not exist, create it:

```bash
mkdir -p {data_path}
```

#### 8e. Update central registry

Read `~/.geno/data-workspaces.yaml`. If it does not exist, create it with:

```yaml
version: 1
workspaces: []
```

Append the new workspace entry to the `workspaces` list:

```yaml
- slug: {slug}
  skill: {skill}
  path: "~/{color}/{slug}-ws"
  color: {color}
  status: active
  data_path: "{data_path}"
  created: {ISO-8601-timestamp}
```

Write the updated file back.

### 9. Report

Tell the user:

- Workspace created at `~/{color}/{slug}-ws/`
- Data path: `{data_path}` (or `./data/` for career)
- Linked workspaces: list each, or "none"
- Next steps: `cd ~/{color}/{slug}-ws/` and start an agent session to use {skill}

---

## Subcommand: list

List all data workspaces.

1. Read `~/.geno/data-workspaces.yaml` if it exists.
2. Additionally, read `~/.geno/config.yaml` to get color folders. For each color folder, scan for directories ending in `-ws` that have `.geno/.workspace/workspace.yaml` with `type: data`.
3. Merge: registry entries + scanned entries (deduplicate by path). Scanned entries not in the registry are tagged `[unregistered]`.
4. Display as a table:

| Workspace | Skill | Color | Data Path | Status | Created | Tags |
|-----------|-------|-------|-----------|--------|---------|------|
| `taxes-2026-ws` | geno-taxes | code-purp | `~/docs/finance/taxes/` | active | 2026-04-26 | |
| `remodel-kitchen-ws` | geno-remodel | code-red | `~/docs/home/remodel/` | active | 2026-04-25 | |
| `career-general-ws` | geno-career | code-red | (workspace-local) | active | 2026-04-24 | |

Sort: active first, then by creation date (newest first).
