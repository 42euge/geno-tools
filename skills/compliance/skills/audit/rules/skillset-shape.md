# Skillset Shape

Everything a `geno-{name}` repo must have to be installable and operable across the ecosystem: manifest, versioning, umbrella skill, naming, agent instructions, docs, hygiene, agent-agnostic language, install compliance, command-prefix aliasing, and the single-source-of-truth boundary.

## Manifest — `genotools.yaml`

`genotools.yaml` is the manifest file every geno-* skillset must have at its root. It's what `skills/lifecycle/skills/install/resources/install.sh` reads to know how to set up the skillset: what it's called, what version it is, whether it needs a Python venv, what scripts to symlink into `~/.geno/{project-name}/`, and what config files to copy on first install. Without a valid manifest, the installer doesn't know what it's installing and the install will fail.

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

## Versioning

The `version` field in `genotools.yaml` is the canonical version for every skillset. When a repo also has `pyproject.toml`, `package.json`, or a Python `__init__.py` with version fields, they must all agree. The audit checks consistency and detects unreleased work that may warrant a bump.

**Required:**
- `genotools.yaml` `version` is a valid semver string (MAJOR.MINOR.PATCH)

**Recommended:**
- If `pyproject.toml` exists and has `project.version`, it matches `genotools.yaml` version
- If `package.json` exists and has `version`, it matches `genotools.yaml` version
- If root `SKILL.md` has `metadata.version` in frontmatter, it matches `genotools.yaml` version
- If a Python `__init__.py` in the package root has `__version__`, it matches `genotools.yaml` version

**Info:**
- If skills have been added or removed since the last git tag (compare `skills/` directories against the most recent tag), note that a version bump may be warranted

## Umbrella Skill — `SKILL.md`

`SKILL.md` at the repo root is the umbrella manifest that describes the skillset to Claude Code and other agents. When the installer runs `npx skills add`, this file is what gets registered — it tells the agent what the skillset does, when to use it, and what tools it's allowed to call. A skillset without a valid `SKILL.md` will install on disk but won't be usable by any agent.

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

## Skill Nomenclature

Skills follow a three-level naming hierarchy: **skillset → sub-skillset → skill**. The full spec lives at `docs/skillsets/nomenclature.md` (published at `https://42euge.github.io/geno-tools/skillsets/nomenclature/`). The audit enforces it.

Quick reference: `{skillset}-{sub-skillset}-{skill}` where sub-skillset is a **pluralized noun** and skill is an **action verb**. The umbrella skill is just the skillset name. Directory names under `skills/` must match the `name` field in each SKILL.md frontmatter — **except** when using the nested tree layout (see [upstream conventions](../../../../docs/skillsets/upstream-conventions.md)), where leaf directories use bare nouns and the frontmatter `name:` carries the full qualified name.

### Legacy `commands/` directory

Some repos still have a `commands/` directory with `gt-*.md` files from the old slash-command convention. This is legacy — all skill definitions now live under `skills/` as `SKILL.md` files. If a repo has both `commands/` and `skills/`, the `commands/` directory must be removed. Do not keep it for backward compatibility — the installer registers skills from `skills/`, not `commands/`.

If `commands/` contains content that hasn't been migrated to `skills/` yet, migrate it: create the appropriate `skills/{skillset}-{sub-skillset}-{skill}/SKILL.md` file with proper frontmatter, move the command body into it, then delete the command file. Do not leave both in place.

**Required:**
- An umbrella skill exists at `skills/{skillset}/SKILL.md`
- Every directory under `skills/` (at any depth in nested layouts) contains a `SKILL.md`
- No `commands/` directory exists — if found, migrate contents to `skills/` and delete it
- **Monolithic CLI check**: if the skillset has a CLI backend (`[project.scripts]` in `pyproject.toml` or a standalone bin script) with multiple subcommands, it must have corresponding sub-skillset skill directories under `skills/` beyond the umbrella. To check: (a) find the CLI entry point from `[project.scripts]` and inspect it for `add_parser` / `add_command` / `app.command` / `@cli.command` calls (argparse, click, typer) to count subcommands; (b) count directories under `skills/` (including nested leaves) that contain a `SKILL.md` and subtract 1 for the umbrella. A skillset with ≥ 3 CLI subcommands and 0 sub-skillset skill directories **fails**. A comment in `CLAUDE.md` or `GENO.md` claiming the repo is a "single-skill skillset" does not exempt it from this check.

**Recommended:**
- All skill names follow the `{skillset}-{sub-skillset}-{skill}` pattern (in frontmatter `name:`, regardless of directory shape)
- Sub-skillset segment is a pluralized noun (not a verb or adjective)
- Skill segment is an action verb
- The umbrella skill's `description` lists all available sub-skill commands
- No skill directories exist outside of `skills/`

## Agent Instruction Files

Coding agents read repo-level instruction files to understand architecture, entry points, and conventions. Without these, agents rediscover the repo structure every session. Each agent has its own file convention:

| Agent | Instruction file | Notes |
|-------|-----------------|-------|
| Claude Code | `CLAUDE.md` | Read automatically on session start |
| Gemini CLI | `GEMINI.md` | Pointed to by `gemini-extension.json` via `contextFileName` |
| OpenAI Codex | `AGENTS.md` | Read automatically on session start |
| OpenCode | `.opencode/INSTALL.md` | Plugin-based — context loaded via `.opencode/plugins/` |

### Single source of truth — `GENO.md`

Rather than maintaining duplicate content across `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, and OpenCode configs, every geno-* repo should have a single `GENO.md` file at the repo root containing all agent instructions. The per-agent files become thin pointers that import it.

`GENO.md` is the canonical instruction file — the single document any agent reads to understand the repo cold. It should contain everything an agent needs to start working without asking questions or exploring the codebase first.

**Required sections in GENO.md:**

1. **Title and summary** — one-line description of what this skillset does, framed agent-neutrally.
2. **Skills table** — every skill in the repo with its name, sub-skillset group, and slash command.
3. **Repo structure** — a tree showing the key files and directories. Include what each is for.
4. **Conventions** — the rules an agent must follow when modifying code in this repo:
   - Nomenclature as it applies to this skillset (do not restate ecosystem-wide rules)
   - SKILL.md frontmatter format for new skills
   - Adding a new skill (step-by-step checklist)
   - Command prefix aliasing (canonical `geno-` in source, runtime alias is per-install)
   - Versioning (which files contain the version, when to bump)

**Recommended sections:**
5. **Architecture / how it works** — for skillsets with runtime code, explain entry points, key modules, data flow.
6. **Dependencies and runtime** — venvs, external tools, system dependencies.

**What NOT to put in GENO.md:**
- Install instructions for end users (those go in `README.md` and `docs/getting-started.md`)
- Agent-specific syntax (this file is read by all agents)
- Transient state like current tasks (those go in `.geno/` or conversation context)

### Per-agent pointer files

The per-agent files are thin pointers. No content lives in them — they exist only because each agent looks for a different filename.

- **`CLAUDE.md`**: `@./GENO.md`
- **`GEMINI.md`**: `@./GENO.md`
- **`AGENTS.md`**: `@import GENO.md`
- **`gemini-extension.json`** (if present): `"contextFileName": "GEMINI.md"`

**Required:**
- `GENO.md` exists at repo root and is non-empty

**Recommended:**
- `CLAUDE.md` exists and contains only `@./GENO.md` (no other content)
- `GEMINI.md` exists and contains only `@./GENO.md`
- `AGENTS.md` exists and contains only `@import GENO.md`
- If `gemini-extension.json` exists, its `contextFileName` points to `GEMINI.md`
- No agent instruction content is duplicated across files — all substance lives in `GENO.md`
- `GENO.md` Conventions section mentions command prefix aliasing — at minimum, states that source files use canonical `geno-` prefixed names, not aliased prefixes
- `GENO.md` Conventions section includes skill creation guidance — at minimum, a checklist for adding a new skill
- `GENO.md` skills table uses canonical `/geno-{name}-*` slash command names, not aliased forms like `/gt-*`
- `GENO.md` Conventions section includes versioning guidance — at minimum, identifies which files contain the version and states that the version should be bumped when skills are added, removed, or behavior changes

## Documentation — `docs/`

Every geno-* repo should ship a MkDocs Material documentation site. This is how users and contributors learn what the skillset does, how to use it, and how it's built. The convention follows geno-tools' own docs structure, minus the animated landing page.

### Required structure

```
docs/
├── index.md                       # docs home — title, summary, nav links
├── getting-started.md             # install, prerequisites, first use
└── assets/
    └── icon.png                   # project icon (generated via geno-assets-icons)
```

### Recommended additions

```
docs/
├── cli-reference.md               # if the skillset has CLI commands
├── architecture/
│   └── index.md                   # how it works internally
├── stylesheets/
│   └── extra.css                  # custom styles
└── <topic>/
    └── index.md
```

### `mkdocs.yml`

Each repo needs a `mkdocs.yml` at the repo root following geno-tools' theme configuration (Material, Inter/JetBrains Mono fonts, light/dark toggle, navigation features) — but skipping `custom_dir: docs/overrides`, `extra_javascript` for `face.js`, and the `docs-home.md` hero page.

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

## Repo Hygiene

General repo quality checks. None block installation, but they prevent common issues.

**Recommended:**
- `README.md` exists — human-readable documentation for anyone browsing the repo on GitHub.
- `LICENSE` file exists — declares the license so others know if they can use the skillset.
- Repo directory name matches `geno-*` convention.

## Agent-Agnostic Language

The geno ecosystem is CLI-agnostic — skillsets work with Claude Code, Gemini CLI, Codex, OpenCode, and any future coding agent. Documentation and user-facing text must reflect this. Referring to "Claude Code" as if it's the only supported agent misleads users and creates the impression that the skillset is locked to one platform.

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

**Do NOT replace** references to agent-specific features, paths, or APIs that are genuinely specific to one agent — `.claude/worktrees/`, "Codex sandbox", "Gemini CLI extension", agent-specific plugin manifests. The rule is about how the *skillset itself* is described, not about suppressing legitimate references to agent-specific behavior.

**Recommended:**
- Scan `README.md`, `docs/**/*.md`, `SKILL.md`, `AGENTS.md`, `GEMINI.md`, and `getting-started.md` for language that frames the skillset as exclusive to one agent
- Descriptions and headings use agent-neutral phrasing
- Prerequisites list supported CLIs generically
- Do not modify references to agent-specific features, paths, directories, or APIs

## Installation Compliance

Geno-* skillsets must be installed through the geno-tools install resource script, not by calling `npx skills add` directly. The installer at `skills/lifecycle/skills/install/resources/install.sh` does more than just register skills — it clones the repo, creates venvs, materializes bin symlinks, and sets up the `~/.geno/geno-{name}/` directory structure. Bypassing it leaves the skillset partially installed.

Docs should always reference the canonical install script path: `"$CLAUDE_PLUGIN_ROOT/skills/lifecycle/skills/install/resources/install.sh" geno-{name}`. Command aliases are user-configured per installation, so they must never appear in repo documentation.

**Recommended:**
- No file in the repo contains `npx skills add` as a user-facing install instruction. Check `README.md`, `docs/**/*.md`, `GENO.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, and `SKILL.md` for this pattern.
- Install instructions reference the canonical install script path.

## Ecosystem Freshness

Installed skillsets should stay on the latest main branch. Stale installs lead to agents using outdated skill definitions, missing features, and broken cross-skillset interactions. The update script at `skills/self/skills/update/resources/update.sh` pulls the latest main for all installed skillsets.

**Recommended:**
- Run the update script as part of the audit to ensure the target repo's installed copy (if any) is on the latest main. If behind origin, note how many commits behind.
- If the target repo's `main` worktree at `~/.geno-tools/geno-{name}/main/` has a dirty working tree or is on a non-default branch, warn that the install is in a non-standard state.

**Info:**
- Report the current installed revision (short SHA) and the date of the last commit on main. Stale installs older than 30 days get an INFO note.

## Command Prefix Aliasing in Repo Source

Slash commands in the geno ecosystem use a configurable prefix. Users set their preferred prefix in `~/.geno/config.yaml`:

```yaml
aliases:
  command_prefix: "gt"   # /gt-install, /gt-media-audiobook-create
  # or "geno"            # /geno-install (default)
  # or ""                # /install
```

The prefix is applied at install time by the install script. Repo source files — SKILL.md frontmatter, SKILL.md body, GENO.md, README.md, docs — must always use the **canonical name** with the `geno-` prefix.

### What to check

Scan all committed files: SKILL.md (root and nested), GENO.md, README.md, `docs/**/*.md`, CLAUDE.md, AGENTS.md, GEMINI.md.

Look for patterns indicating an aliased prefix was hardcoded:
- `/gt-` followed by a skill name (e.g. `/gt-notes`, `/gt-dev-tasks-start`)
- `gt-` used as a command prefix in section headers
- Any non-`geno-` prefix in slash command references

Do NOT flag:
- The string `gt-` in non-slash-command contexts (`gt-*.md` legacy file naming, `"gt"` as a config value)
- References to `command_prefix: "gt"` in configuration examples
- The `name` field in SKILL.md frontmatter — already caught by Skill Nomenclature checks

**Required:**
- No SKILL.md file (root or under `skills/` at any depth) contains aliased command prefixes like `/gt-` in its `description` frontmatter field or body content. Functional requirement — agents use these descriptions to match user intent to skills.

**Recommended:**
- No file in the repo contains aliased slash command references in body content.

## Single Source of Truth Enforcement

**geno-tools is the single source of truth for the geno ecosystem.** Every ecosystem-wide convention — how skills are named, what files a repo must have, how SKILL.md frontmatter is formatted — is defined exactly once, in geno-tools. No other repo defines, restates, or interprets these rules.

Individual repos describe *themselves* — what skills they contain, what they do, how their specific code is structured. They do not describe *how the ecosystem works*.

When a repo restates a convention, it creates a copy. Copies drift. The audit prevents this by detecting and removing locally redefined conventions.

### What counts as a local redefinition

Sections in repo files that restate ecosystem-level rules:

- Nomenclature rules (how skills/sub-skillsets/slugs are named)
- Required repo structure definitions
- SKILL.md frontmatter format specifications
- Step-by-step checklists for adding a new skill
- Ecosystem-level compliance rules

### How to detect

Check `GENO.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `README.md`, and `docs/**/*.md` for:

- Headings containing: `Nomenclature`, `Compliance`, `Convention`, `Repo structure`, `Required files`, `Frontmatter format`, `Adding a new skill`, `Contribution guide`
- Paragraphs that define what "every geno-* repo must have"
- Tables that redefine the `{skillset}-{sub-skillset}-{skill}` pattern
- References to the geno-tools nomenclature spec followed by a local restatement

### What to do

Remove the offending sections entirely. If a section mixes ecosystem rules with repo-specific details, keep only the repo-specific content. A repo's `GENO.md` should contain a skills table for *this* repo — that's repo-specific. It should not explain *how to name* skills in general — that's the ecosystem spec.

**Required:**
- No file in the repo contains locally redefined ecosystem conventions.
