---
name: geno-audit
description: >-
  Audit a geno-ecosystem repo for compliance with skillset conventions.
  Use when user says /geno-audit, wants to check if a repo is a valid
  geno-* skillset, or needs to verify ecosystem compliance before publishing.
allowed-tools: "Bash(find *) Bash(ls *) Bash(cat *) Bash(grep *) Bash(git *) Bash(python3 -c *) Read(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-audit — Ecosystem Compliance Auditor

Validates that a `geno-{name}` repo meets the conventions required for installation and management by `geno-tools`.

The audit runs checks in three tiers: **required** (FAIL), **recommended** (WARN), and **optional** (INFO). A repo must pass all required checks to be installable via `geno-tools install`.

---

## `.geno` Directory Convention

Every project in the geno ecosystem uses a two-tier `.geno` directory structure for runtime state, configuration, and tooling data. Neither tier should ever be committed to git — they contain machine-local paths, user-specific config, and transient runtime state that would break on any other machine.

### Global — `~/.geno/`

The global `.geno` directory at `~/.geno/` is the ecosystem-wide root. It contains shared infrastructure and per-project state that persists across workspaces:

```
~/.geno/
├── config.yaml                    # ecosystem-wide settings
├── agents/                        # agent registration and presence
├── sessions/                      # session history
├── messages/                      # inter-agent messages
├── bin/                           # symlinked CLI binaries
├── venv/                          # shared Python environments
└── geno-{name}/                   # per-skillset state
    ├── .git/                      # bare repo
    ├── main/                      # primary worktree
    ├── .worktrees/<variant>/      # additional worktrees
    ├── venvs/<venv-name>/         # isolated Python envs
    └── active -> main             # symlink to active variant
```

This is where `geno-tools install` clones repos, creates venvs, and materializes bin symlinks. Other ecosystem tools also keep state here — `geno-notes` stores the global task journal at `~/.geno/geno-notes/`, `geno-agents` stores registration data at `~/.geno/agents/`, etc.

### Local — `.geno/`

The local `.geno/` directory at the repo or workspace root holds per-workspace state. It has a fixed structure with a reserved `.workspace/` subdirectory for workspace metadata, and optional `{project-name}/` subdirectories for tools that need local state.

```
.geno/
├── .workspace/                    # workspace metadata (managed by geno-dev-workspaces-init)
│   ├── workspace.yaml             # slug, status, repos, color, ticket
│   └── worktrees/                 # local worktree checkouts
│       └── {repo}/{branch}/       # one per active worktree
└── {project-name}/                # per-tool local state (optional)
    └── ...                        # tool-specific files
```

**`.workspace/`** contains workspace metadata — the `workspace.yaml` (slug, status, repos, color assignment, source ticket) and any worktree checkouts created for repos in this workspace. This is always under `.workspace/` to keep it separate from tool state.

**`{project-name}/`** directories are created by individual tools when they need workspace-scoped state. For example, `geno-notes` may create `.geno/geno-notes/` to store project-scoped tasks and journal entries (as opposed to the global journal at `~/.geno/geno-notes/`). Not every workspace will have these — they appear only when a tool that needs local state is used in that workspace.

### Audit checks

**Required:**
- `.geno/` is not tracked by git (checked via `git ls-files`)
- `CLAUDE.local.md` is not tracked by git

**Recommended:**
- Global gitignore (`~/.config/git/ignore`) includes `.geno/` and `CLAUDE.local.md`. These entries belong in the global gitignore, not in any project's `.gitignore` — adding them to a project's `.gitignore` would leak geno ecosystem artifacts into committed files. The audit should check the global gitignore and suggest adding entries there if missing. Never modify a project's `.gitignore` for geno-specific patterns.

---

## Manifest — `genotools.yaml`

`genotools.yaml` is the manifest file every geno-* skillset must have at its root. It's what `geno-tools install` reads to know how to set up the skillset: what it's called, what version it is, whether it needs a Python venv, what scripts to symlink into `~/.geno/{project-name}/`, and what config files to copy on first install. Without a valid manifest, `geno-tools` doesn't know what it's installing and the install will fail.

**Required:**
- File exists at repo root
- Has a `name` field (the skillset name — `geno-` prefix is stripped if present)
- Has a `version` field (semver string, e.g. `0.1.0`)
- Has a non-empty `description` field

**Recommended:**
- `name` matches the repo directory name (with or without the `geno-` prefix)

**Optional:**
- If `venv` section exists, it should have `name` and `deps` fields
- If `runtime` section exists, each entry should have `src` and `dst`
- If `config` section exists, each entry should have `src` and `dst`
- If `pyproject.toml` also exists, its `project.name` should match the manifest name

---

## Versioning

The `version` field in `genotools.yaml` is the canonical version for every skillset. When a repo also has `pyproject.toml`, `package.json`, or a Python `__init__.py` with version fields, they must all agree. The audit checks consistency and detects unreleased work that may warrant a bump.

### Audit checks

**Required:**
- `genotools.yaml` `version` is a valid semver string (MAJOR.MINOR.PATCH)

**Recommended:**
- If `pyproject.toml` exists and has `project.version`, it matches `genotools.yaml` version
- If `package.json` exists and has `version`, it matches `genotools.yaml` version
- If root `SKILL.md` has `metadata.version` in frontmatter, it matches `genotools.yaml` version
- If a Python `__init__.py` in the package root has `__version__`, it matches `genotools.yaml` version

**Info:**
- If skills have been added or removed since the last git tag (compare `skills/` directories against the most recent tag), note that a version bump may be warranted

---

## Umbrella Skill — `SKILL.md`

`SKILL.md` at the repo root is the umbrella manifest that describes the skillset to Claude Code and other agents. When `geno-tools install` runs `npx skills add`, this file is what gets registered — it tells the agent what the skillset does, when to use it, and what tools it's allowed to call. A skillset without a valid `SKILL.md` will install on disk but won't be usable by any agent.

**Required:**
- File exists at repo root
- Has YAML frontmatter delimited by `---`
- Frontmatter includes a `name` field
- Frontmatter includes a non-empty `description` field

**Recommended:**
- `name` in frontmatter matches the repo name
- Frontmatter includes `allowed-tools` declaring what tools the skill needs

**Optional:**
- Frontmatter includes `metadata` with `author` and `version`

---

## Skill Nomenclature

Skills follow a three-level naming hierarchy: **skillset → sub-skillset → skill**. The full spec lives at `docs/skillsets/nomenclature.md` (published at `https://42euge.github.io/geno-tools/skillsets/nomenclature/`). The audit enforces it.

Quick reference: `{skillset}-{sub-skillset}-{skill}` where sub-skillset is a **pluralized noun** and skill is an **action verb**. The umbrella skill is just the skillset name. Directory names under `skills/` must match the `name` field in each SKILL.md frontmatter.

### Legacy `commands/` directory

Some repos still have a `commands/` directory with `gt-*.md` files from the old slash-command convention. This is legacy — all skill definitions now live under `skills/` as `SKILL.md` files. If a repo has both `commands/` and `skills/`, the `commands/` directory must be removed. Do not keep it for backward compatibility — `geno-tools install` registers skills from `skills/`, not `commands/`.

If `commands/` contains content that hasn't been migrated to `skills/` yet, migrate it: create the appropriate `skills/{skillset}-{sub-skillset}-{skill}/SKILL.md` file with proper frontmatter, move the command body into it, then delete the command file. Do not leave both in place.

### Audit checks

**Required:**
- An umbrella skill exists at `skills/{skillset}/SKILL.md`
- Every directory under `skills/` contains a `SKILL.md`
- No `commands/` directory exists — if found, migrate contents to `skills/` and delete it
- **Monolithic CLI check**: if the skillset has a CLI backend (`[project.scripts]` in `pyproject.toml` or a standalone bin script) with multiple subcommands, it must have corresponding sub-skillset skill directories under `skills/` beyond the umbrella. To check: (a) find the CLI entry point from `[project.scripts]` and inspect it for `add_parser` / `add_command` / `app.command` / `@cli.command` calls (argparse, click, typer) to count subcommands; (b) count directories under `skills/` that contain a `SKILL.md` and subtract 1 for the umbrella. A skillset with ≥ 3 CLI subcommands and 0 sub-skillset skill directories **fails**. A comment in `CLAUDE.md` or `GENO.md` claiming the repo is a "single-skill skillset" does not exempt it from this check. **Correct pattern**: geno-dev (`geno-dev-tasks-start`, `geno-dev-commits-rewrite`, `geno-dev-loops-cruise`, `geno-dev-sessions-fork`, etc. — 9 sub-skills for 9 functional groups). **Failure example**: geno-notes (18 CLI subcommands — add, start, done, abandon, note, inbox, triage, list, show, search, promote, reindex, compile, lint, site, path, scope, init — but only the umbrella skill under `skills/`).

**Recommended:**
- All skill directory names follow the `{skillset}-{sub-skillset}-{skill}` pattern
- Sub-skillset segment is a pluralized noun (not a verb or adjective)
- Skill segment is an action verb
- The `name` field in each SKILL.md frontmatter matches its directory name
- The umbrella skill's `description` lists all available sub-skill commands
- No skill directories exist outside of `skills/`

---

## Agent Instruction Files

Coding agents read repo-level instruction files to understand architecture, entry points, and conventions. Without these, agents rediscover the repo structure every session. Each agent has its own file convention:

| Agent | Instruction file | Notes |
|-------|-----------------|-------|
| Claude Code | `CLAUDE.md` | Read automatically on session start |
| Gemini CLI | `GEMINI.md` | Pointed to by `gemini-extension.json` via `contextFileName` |
| OpenAI Codex | `AGENTS.md` | Read automatically on session start |
| OpenCode | `.opencode/INSTALL.md` | Plugin-based — context loaded via `.opencode/plugins/` |

### Single source of truth — `GENO.md`

Rather than maintaining duplicate content across `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, and OpenCode configs, every geno-* repo should have a single `GENO.md` file at the repo root containing all agent instructions. The per-agent files become thin pointers that import it:

### What goes in `GENO.md`

`GENO.md` is the canonical instruction file — the single document any agent reads to understand the repo cold. It should contain everything an agent needs to start working without asking questions or exploring the codebase first. Write it for an agent that just walked into the room: no prior context, no assumptions.

#### Required sections

1. **Title and summary** — one-line description of what this skillset does, framed agent-neutrally.

2. **Skills table** — every skill in the repo with its name, sub-skillset group, and slash command. This is the index an agent checks to understand what capabilities are available.

   ```markdown
   | Skill | Sub-skillset | Slash command |
   |-------|-------------|---------------|
   | geno-{name} | — | — (umbrella) |
   | geno-{name}-tasks-start | tasks | /geno-{name}-tasks-start |
   ```

3. **Repo structure** — a tree showing the key files and directories. Agents use this to navigate without running `find`. Include what each directory/file is for.

   ```markdown
   ## Repo structure

   geno-{name}/
   ├── GENO.md              # agent instructions (this file)
   ├── SKILL.md             # umbrella skill manifest
   ├── genotools.yaml       # geno-tools manifest
   ├── skills/              # skill definitions
   │   ├── geno-{name}/     #   umbrella
   │   └── geno-{name}-*/   #   sub-skills
   ├── docs/                # MkDocs Material site
   └── pyproject.toml       # Python package (if applicable)
   ```

4. **Conventions** — the rules an agent must follow when modifying code in this repo. This is where naming conventions, file placement rules, and contribution workflows live. Key conventions to document:

   - **Nomenclature**: how skills are named in this repo (e.g. `geno-{name}-{sub-skillset}-{skill}`). Do not restate ecosystem-wide naming rules — just show the pattern as it applies to this skillset.
   - **SKILL.md frontmatter**: required fields and format for new skills
   - **Adding a new skill**: step-by-step checklist (create directory under `skills/`, write SKILL.md with frontmatter, update umbrella description, update docs, update this file's skills table)
   - **Command prefix aliasing**: slash commands in repo source files must always use the canonical `geno-` prefix (e.g. `/geno-{name}-tasks-start`). The prefix users type (`/gt-`, `/geno-`, or bare `/`) is configured per-installation in `~/.geno/config.yaml` and applied at install time by `geno-tools install`. Never hardcode an aliased prefix like `gt-` in SKILL.md descriptions, GENO.md, or any committed file.
   - **Versioning**: which files contain the version number (always `genotools.yaml`; plus any others like `pyproject.toml` or `package.json`) and the rule that the version must be bumped when adding/removing skills or changing behavior

#### Recommended sections

5. **Architecture / how it works** — for skillsets with runtime code (Python packages, scripts), explain the entry points, key modules, and data flow. Skip this for pure-markdown skillsets.

6. **Dependencies and runtime** — if the skillset needs a venv, external tools, or system dependencies, list them here so agents know what's available and what constraints exist.

#### What NOT to put in `GENO.md`

- Install instructions for end users — those go in `README.md` and `docs/getting-started.md`
- Agent-specific syntax or references — this file is read by all agents
- Transient state like current tasks or in-progress work — those go in `.geno/` or conversation context

### Per-agent pointer files

The per-agent files are thin pointers. No content lives in them — they exist only because each agent looks for a different filename.

**`CLAUDE.md`**:
```markdown
@./GENO.md
```

**`GEMINI.md`**:
```markdown
@./GENO.md
```

**`AGENTS.md`**:
```markdown
@import GENO.md
```

**`gemini-extension.json`** (if present):
```json
{
  "name": "geno-{name}",
  "description": "...",
  "version": "0.1.0",
  "contextFileName": "GEMINI.md"
}
```

This way, updating `GENO.md` updates every agent at once. No content lives in the per-agent files — they are pure pointers.

### Audit checks

**Required:**
- `GENO.md` exists at repo root and is non-empty

**Recommended:**
- `CLAUDE.md` exists and contains only `@./GENO.md` (no other content)
- `GEMINI.md` exists and contains only `@./GENO.md`
- `AGENTS.md` exists and contains only `@import GENO.md`
- If `gemini-extension.json` exists, its `contextFileName` points to `GEMINI.md`
- No agent instruction content is duplicated across files — all substance lives in `GENO.md`
- `GENO.md` contains a Conventions section (a heading matching `Conventions`, case-insensitive)
- `GENO.md` Conventions section mentions command prefix aliasing — at minimum, states that source files use canonical `geno-` prefixed names for slash commands, not aliased prefixes
- `GENO.md` Conventions section includes skill creation guidance — at minimum, a checklist for adding a new skill
- `GENO.md` skills table uses canonical `/geno-{name}-*` slash command names, not aliased forms like `/gt-*`
- `GENO.md` Conventions section includes versioning guidance — at minimum, identifies which files contain the version and states that the version should be bumped when skills are added, removed, or behavior changes

---

## Documentation — `docs/`

Every geno-* repo should ship a MkDocs Material documentation site. This is how users and contributors learn what the skillset does, how to use it, and how it's built. The convention follows geno-tools' own docs structure, minus the animated landing page (that's unique to geno-tools as the ecosystem entry point).

### Required structure

```
docs/
├── index.md                       # docs home — title, one-paragraph summary, nav links
├── getting-started.md             # install, prerequisites, first use
└── assets/
    └── icon.png                   # project icon (generated via geno-icons)
```

### Recommended additions

```
docs/
├── cli-reference.md               # if the skillset has CLI commands
├── architecture/
│   └── index.md                   # how it works internally
├── stylesheets/
│   └── extra.css                  # custom styles (dark/light theme support)
└── <topic>/                       # domain-specific sections as needed
    └── index.md
```

### `mkdocs.yml`

Each repo needs a `mkdocs.yml` at the repo root. Follow geno-tools' theme configuration (Material, Inter/JetBrains Mono fonts, light/dark toggle, navigation features) but skip:
- `custom_dir: docs/overrides` (no hero overrides)
- `extra_javascript` for `face.js` (no animated splash)
- The `docs-home.md` hero page with feature cards

A minimal `mkdocs.yml`:

```yaml
site_name: geno-{name}
site_description: One-line description
site_url: https://42euge.github.io/geno-{name}
repo_url: https://github.com/42euge/geno-{name}
repo_name: 42euge/geno-{name}

theme:
  name: material
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: custom
      accent: custom
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: custom
      accent: custom
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  font:
    text: Inter
    code: JetBrains Mono
  icon:
    repo: fontawesome/brands/github
  features:
    - navigation.sections
    - navigation.top
    - content.code.copy
    - search.highlight
    - toc.follow

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  # ... additional pages

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.tabbed:
      alternate_style: true
  - attr_list
  - toc:
      permalink: true
```

### Audit checks

**Recommended:**
- `docs/` directory exists
- `docs/index.md` exists
- `docs/getting-started.md` exists
- `mkdocs.yml` exists at repo root
- `mkdocs.yml` uses `material` theme

**Optional:**
- `docs/assets/icon.png` exists
- `docs/cli-reference.md` exists (if the skillset exposes CLI commands)
- `mkdocs.yml` has `site_url` and `repo_url` configured

---

## Repo Hygiene

General repo quality checks. None block installation, but they prevent common issues.

**Recommended:**
- `README.md` exists — human-readable documentation for anyone browsing the repo on GitHub.
- `LICENSE` file exists — declares the license so others know if they can use the skillset.
- Repo directory name matches `geno-*` convention.

---

## Agent-Agnostic Language

The geno ecosystem is CLI-agnostic — skillsets work with Claude Code, Gemini CLI, Codex, OpenCode, and any future coding agent. Documentation and user-facing text must reflect this. Referring to "Claude Code" as if it's the only supported agent misleads users and creates the impression that the skillset is locked to one platform.

Use generic terms like "coding agent", "agent session", or "coding CLI" instead of naming a specific agent. When listing prerequisites, mention the supported agents rather than singling one out. When describing how to invoke a skill, show the generic form.

**Avoid:**
- "Developer skills for Claude Code"
- "Prerequisites: Claude Code installed"
- "From within a Claude Code session"
- "Claude Code slash commands"

**Prefer:**
- "Developer skills for AI coding agents"
- "Prerequisites: a supported coding CLI (Claude Code, Gemini CLI, Codex, or OpenCode)"
- "From within an agent session"
- "Slash commands" (no agent prefix)

**Do NOT replace** references to agent-specific features, paths, or APIs that are genuinely specific to one agent. For example:
- `.claude/worktrees/` — this is a real Claude Code directory path, not branding
- "Codex sandbox" — this is a Codex-specific runtime concept
- "Gemini CLI extension" — this refers to the actual Gemini extension format
- Agent-specific plugin manifests (`.claude-plugin/`, `.codex-plugin/`, etc.)

The rule is about how the *skillset itself* is described, not about suppressing legitimate references to agent-specific behavior within skill instructions.

### Audit checks

**Recommended:**
- Scan `README.md`, `docs/**/*.md`, `SKILL.md`, `AGENTS.md`, `GEMINI.md`, and `getting-started.md` for language that frames the skillset as exclusive to one agent
- Descriptions and headings should use agent-neutral phrasing
- Prerequisites should list supported CLIs generically, not single out one
- Do not modify references to agent-specific features, paths, directories, or APIs — only replace branding/framing language

---

## Installation Compliance

Geno-* skillsets must be installed through `geno-tools`, not by calling `npx skills add` directly. `geno-tools install` does more than just register skills — it clones the repo, creates venvs, materializes bin symlinks, and sets up the `~/.geno/geno-{name}/` directory structure. Bypassing it with `npx skills add` skips all of that, leaving the skillset partially installed: skills appear in the agent but the underlying tooling, venvs, and state directories are missing.

Docs, READMEs, and getting-started guides should instruct users to install via `geno-tools`:

```bash
geno-tools install geno-dev
```

or via the skill within an agent session:

```
/geno-tools install geno-dev
```

Never instruct users to run `npx skills add <user>/<repo>` directly. That's an internal implementation detail of how `geno-tools install` registers skills — it should not be user-facing.

Docs should always use the canonical `geno-tools install geno-{name}` or `/geno-tools install geno-{name}` form. Command aliases are user-configured and vary per installation, so they must never appear in repo documentation.

This rule applies to install commands. For the general rule about slash command prefixes across all repo content, see **Command Prefix Aliasing in Repo Source** below.

### Audit checks

**Recommended:**
- No file in the repo contains `npx skills add` as a user-facing install instruction. Check `README.md`, `docs/**/*.md`, `GENO.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, and `SKILL.md` for this pattern.
- Install instructions use the canonical `geno-tools install geno-{name}` or `/geno-tools install geno-{name}` form, not raw `npx`, `pip install`, or any aliased command names.

---

## Ecosystem Freshness

Installed skillsets should stay on the latest main branch. Stale installs lead to agents using outdated skill definitions, missing features, and broken cross-skillset interactions. `geno-tools update` pulls the latest main for all installed skillsets (or a specific one) and re-registers skills.

### Audit checks

**Recommended:**
- Run `geno-tools update` as part of the audit to ensure the target repo's installed copy (if any) is on the latest main. If the installed copy is behind origin, the audit should note how many commits behind it is.
- If the target repo's `main` worktree at `~/.geno-tools/geno-{name}/main/` has a dirty working tree or is on a non-default branch, warn that the install is in a non-standard state.

**Info:**
- Report the current installed revision (short SHA) and the date of the last commit on main. Stale installs older than 30 days get an INFO note.

---

## Command Prefix Aliasing in Repo Source

Slash commands in the geno ecosystem use a configurable prefix. Users set their preferred prefix in `~/.geno/config.yaml`:

```yaml
aliases:
  command_prefix: "gt"   # /gt-install, /gt-media-audiobook-create
  # or "geno"            # /geno-install, /geno-media-audiobook-create
  # or ""                # /install, /media-audiobook-create
```

The prefix is applied at install time by `geno-tools install` when materializing skills via `npx skills add`. Repo source files — SKILL.md frontmatter, SKILL.md body, GENO.md, README.md, docs — must always use the **canonical name**, which uses the `geno-` prefix. The canonical name is the skill's `name` field in its SKILL.md frontmatter (e.g. `geno-notes`, `geno-dev-tasks-start`).

### What to check

Scan all committed files that reference slash commands: SKILL.md (root and `skills/*/SKILL.md`), GENO.md, README.md, `docs/**/*.md`, CLAUDE.md, AGENTS.md, GEMINI.md.

Look for patterns that indicate an aliased prefix was hardcoded:

- `/gt-` followed by a skill name (e.g. `/gt-notes`, `/gt-dev-tasks-start`, `/gt-research`)
- `gt-` used as a command prefix in section headers (e.g. `### /gt-notes add`)
- Any non-`geno-` prefix in slash command references

Do NOT flag:

- The string `gt-` in contexts that aren't slash command references (e.g. `gt-*.md` when referring to legacy file naming, or `"gt"` as a config value example)
- References to `command_prefix: "gt"` in configuration examples — those describe the user config, not a hardcoded command name
- The `name` field in SKILL.md frontmatter — this should already be canonical (`geno-*`), but if it's wrong, that's caught by the Skill Nomenclature checks

### How to fix

Replace every aliased slash command reference with its canonical form:

- `/gt-notes` → `/geno-notes`
- `/gt-dev-tasks-start` → `/geno-dev-tasks-start`
- `/gt-research-paper-generate` → `/geno-research-paper-generate`

In SKILL.md `description` fields, replace trigger phrases like `Use when user says /gt-foo` with `Use when user says /geno-foo`.

### Audit checks

**Required:**
- No SKILL.md file (root or under `skills/`) contains aliased command prefixes like `/gt-` in its `description` frontmatter field or body content. Slash command references must use the canonical `geno-` prefix. This is a functional requirement — agents use these descriptions to match user intent to skills, and aliased names may not match the installed command name.

**Recommended:**
- No file in the repo (`GENO.md`, `README.md`, `docs/**/*.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) contains aliased slash command references. All slash command references use the canonical `geno-` prefix.

---

## Single Source of Truth Enforcement

**geno-tools is the single source of truth for the geno ecosystem.** This means every ecosystem-wide convention — how skills are named, what files a repo must have, how SKILL.md frontmatter is formatted, how to add a new skill — is defined exactly once, in the geno-tools repo (its docs, this audit spec, and its own codebase). No other repo defines, restates, or interprets these rules.

Individual repos describe *themselves* — what skills they contain, what they do, how their specific code is structured. They do not describe *how the ecosystem works*. That boundary is what "single source of truth" means: geno-tools owns the rules, other repos follow them.

When a repo restates a convention from geno-tools, it creates a copy. Copies drift. An agent reading geno-dev's local nomenclature section might get rules that were correct six months ago but have since been updated in geno-tools. Now two sources disagree and neither knows it. The audit prevents this by detecting and removing locally redefined conventions.

### What counts as a local redefinition

Sections in repo files that restate ecosystem-level rules. These include but are not limited to:

- Nomenclature rules (how skills/sub-skillsets/slugs are named)
- Required repo structure definitions (what files every geno-* repo must have)
- SKILL.md frontmatter format specifications
- Step-by-step checklists for adding a new skill
- Ecosystem-level compliance rules

### What to scan

Check all markdown files that agents or contributors read: `GENO.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `README.md`, and `docs/**/*.md`.

### How to detect

Look for sections that match these patterns:

- Headings containing: `Nomenclature`, `Compliance`, `Convention`, `Repo structure`, `Required files`, `Frontmatter format`, `Adding a new skill`, `Contribution guide` (when it restates ecosystem rules rather than repo-specific workflows)
- Paragraphs that define what "every geno-* repo must have" or "every SKILL.md must include"
- Tables or lists that redefine the `{skillset}-{sub-skillset}-{skill}` naming pattern
- References to the geno-tools nomenclature spec followed by a local restatement of the same rules

### What to do

Remove the offending sections entirely. If the file becomes empty or loses important repo-specific content in the process, preserve only the repo-specific parts. If a section mixes ecosystem rules with repo-specific details (e.g. a compliance section that restates nomenclature rules but also lists this repo's specific skills), keep only the repo-specific content.

A repo's `GENO.md` should contain a skills table showing what skills *this* repo has — that's repo-specific. It should not explain *how to name* skills in general — that's the ecosystem spec.

### Audit checks

**Required:**
- No file in the repo contains locally redefined ecosystem conventions. If found, remove them and note the removal in the PR.

---

## Running the Audit

### Input

`$ARGUMENTS` — the target repo. Accepts:
- A skillset short name (e.g. `dev`, `media`, `research`) — resolved via the registry
- A GitHub URL
- A local path to a repo directory
- Empty — audits the current working directory

### Procedure

1. **Clone the target into a fresh working copy.** Never operate on an existing workspace checkout — always clone into an isolated directory so the audit doesn't interfere with other agents or in-progress work.

   - If `$ARGUMENTS` is a short name, resolve it to a GitHub URL via the registry (`genotools/registry.py` or `geno-tools ls --available`)
   - If `$ARGUMENTS` is a GitHub URL, use it directly
   - If `$ARGUMENTS` is a local path or empty, skip cloning and work in-place

   Clone to a temporary directory within the current workspace:
   ```bash
   AUDIT_DIR="$(pwd)/.geno-audit/geno-{name}"
   git clone <url> "$AUDIT_DIR"
   cd "$AUDIT_DIR"
   ```

2. **Detect the repo name.** Use the directory basename.

3. **Run all checks.** For each section (`.geno` Convention, Manifest, SKILL.md, Skill Nomenclature, Agent Instruction Files, Documentation, Repo Hygiene, Agent-Agnostic Language, Installation Compliance, Ecosystem Freshness, Command Prefix Aliasing in Repo Source, Single Source of Truth Enforcement), check every item at every tier. For each check, determine PASS, FAIL, WARN, or INFO and collect a short reason for non-PASS results.

4. **Parse YAML carefully.** Use Python for YAML parsing:
   ```bash
   python3 -c "
   import yaml, sys, json
   with open(sys.argv[1]) as f:
       data = yaml.safe_load(f)
   print(json.dumps(data, default=str))
   " <file>
   ```
   For SKILL.md frontmatter, extract the YAML between the first pair of `---` lines:
   ```bash
   python3 -c "
   import yaml, sys, json
   text = open(sys.argv[1]).read()
   if text.startswith('---'):
       end = text.index('---', 3)
       fm = yaml.safe_load(text[3:end])
       print(json.dumps(fm, default=str))
   else:
       print('null')
   " <file>
   ```

5. **Fix all non-PASS items.** After running the checks, fix every FAIL, WARN, and INFO item that can be addressed:
   - Create missing files (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `README.md`, `LICENSE`, `docs/`, `mkdocs.yml`, etc.) using the conventions defined in this document
   - Add missing fields to `genotools.yaml` or `SKILL.md` frontmatter
   - For `CLAUDE.md` / agent instruction files, generate content from the repo's `SKILL.md`, `genotools.yaml`, and code structure
   - For `docs/`, scaffold the required structure (`index.md`, `getting-started.md`) and `mkdocs.yml` using the template from the Documentation section
   - For `README.md`, generate from the manifest description and SKILL.md
   - Do not modify the project's `.gitignore` for `.geno/` or `CLAUDE.local.md` — those belong in the global gitignore only

6. **Create a PR with the fixes.** Once all fixable items are addressed:
   - Create a branch named `chore/geno-audit-compliance`
   - Commit all changes with a message summarizing what was added/fixed
   - Push and open a PR with the audit report as the body

   PR format:
   ```
   gh pr create --title "chore(geno-audit): bring repo into ecosystem compliance" --body "$(cat <<'EOF'
   ## Audit Report: geno-{name}

   Automated compliance audit via `geno-audit`.

   ### Summary
     PASS: NN    FAIL: NN fixed    WARN: NN fixed    INFO: NN fixed

   ### Changes

   - [list of files created or modified, grouped by audit section]

   ### Remaining items (if any)

   - [items that could not be auto-fixed, with explanation]
   EOF
   )"
   ```

7. **Clean up.** Remove the cloned directory after the PR is created:
   ```bash
   rm -rf "$AUDIT_DIR"
   ```
   If the entire `.geno-audit/` directory is now empty, remove it too.

8. **Report the result.** Print the PR URL and a summary of what was fixed vs. what needs manual attention.
