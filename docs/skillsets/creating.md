# Creating a Skillset

Build your own `geno-{name}` skillset that geno-tools can install, update, and manage.

## Minimum viable skillset

```
geno-myskill/
├── genotools.yaml                # required — install manifest
├── GENO.md                       # agent instructions (single source of truth)
├── SKILL.md                      # umbrella skill manifest
├── CLAUDE.md                     # pointer: @./GENO.md
├── GEMINI.md                     # pointer: @./GENO.md
├── AGENTS.md                     # pointer: @import GENO.md
└── skills/
    ├── geno-myskill/             # umbrella skill
    │   └── SKILL.md
    └── geno-myskill-tasks-start/ # at least one sub-skill
        └── SKILL.md
```

## The manifest — `genotools.yaml`

This is the only required file by name. Everything else is whatever the manifest points at.

```yaml
name: myskill                    # "geno-" prefix stripped if present
version: 0.1.0
description: Short description of what this skillset does

# Optional — skip for skillsets with no Python dependencies
venv:
  name: default
  python: ">=3.10"
  deps: ["some-package>=1.0"]

# Optional — symlink runtime scripts
runtime:
  - { src: runtime/process.py, dst: process.py }
  - { src: runtime/helpers,    dst: helpers, recursive: true }

# Optional — copy-once config defaults (preserved across updates)
config:
  - { src: config/defaults/settings.yaml, dst: settings.yaml }
```

### Required fields

| Field | Description |
|-------|-------------|
| `name` | Skillset name. The `geno-` prefix is stripped if present. |
| `version` | Semantic version string |
| `description` | One-line description |

### Optional sections

#### `venv`

Declares an isolated Python environment:

| Field | Description |
|-------|-------------|
| `name` | Venv name (default: `default`) |
| `python` | Python version constraint |
| `deps` | List of pip requirements |

#### `runtime`

Symlinks from repo into `~/.geno-tools/geno-{name}/scripts/`:

| Field | Description |
|-------|-------------|
| `src` | Path relative to repo root |
| `dst` | Path relative to scripts dir |
| `recursive` | `true` to symlink a directory tree |

#### `config`

Copy-once files into `~/.geno-tools/geno-{name}/configs/`. Only created if missing — user edits are never overwritten.

| Field | Description |
|-------|-------------|
| `src` | Path relative to repo root |
| `dst` | Path relative to configs dir |

## Versioning

The `version` field in `genotools.yaml` is the canonical version for every skillset. If other files also carry a version — `pyproject.toml` (`project.version`), `package.json` (`version`), or a Python `__init__.py` (`__version__`) — they must all match. When bumping, update `genotools.yaml` first, then sync the rest.

### What to bump

| Change type | Bump | Examples |
|-------------|------|----------|
| Bug fix, typo, wording improvement in skill instructions | PATCH (0.0.x) | Fix broken bash snippet in SKILL.md, clarify ambiguous instruction |
| Doc-only changes with no behavior impact | PATCH | Update getting-started.md, add architecture doc |
| New skill added | MINOR (0.x.0) | Add `geno-{name}-reports-generate` skill |
| Existing skill behavior significantly expanded | MINOR | Add new workflow steps to an existing skill |
| New config options, runtime scripts, or dependencies | MINOR | Add a `runtime:` entry, add a pip dep to `venv.deps` |
| Removed skill or slash command | MAJOR (x.0.0) | Delete a `skills/` directory |
| Renamed slash command | MAJOR | Change a skill's `name` field |
| Incompatible manifest changes | MAJOR | Restructure `genotools.yaml` format |

### When NOT to bump

Not every commit needs a version bump. If you're making a series of related changes on a branch before merging, bump once in the final commit of the series. The version in `main` should always reflect the latest released state.

### What GENO.md should say

Individual repos must not restate the full versioning policy — that lives here in geno-tools. Instead, their `GENO.md` Conventions section should include a brief **Versioning** item that tells agents: (1) the canonical version lives in `genotools.yaml`, (2) which other files (if any) also contain versions and must stay in sync, and (3) to bump the version when adding/removing skills or changing behavior.

## Skills — `skills/`

Skills are defined as `SKILL.md` files under `skills/`. Each skill lives in its own directory. The directory name must match the `name` field in the SKILL.md frontmatter.

### Naming convention

Skills follow a three-level hierarchy: `{skillset}-{sub-skillset}-{skill}`. See [Nomenclature](nomenclature.md) for the full spec.

- **Sub-skillset** — a pluralized noun (e.g. `tasks`, `sessions`, `notebooks`)
- **Skill** — an action verb (e.g. `start`, `create`, `manage`)
- **Umbrella** — just the skillset name, no suffix

Example layout:

```
skills/
├── geno-myskill/                    # umbrella
│   └── SKILL.md
├── geno-myskill-tasks-start/        # sub-skillset: tasks, skill: start
│   └── SKILL.md
└── geno-myskill-configs-export/     # sub-skillset: configs, skill: export
    └── SKILL.md
```

### SKILL.md frontmatter

```yaml
---
name: geno-myskill-tasks-start
description: >-
  Start a task from the project journal.
  Use when user says /geno-myskill-tasks-start.
allowed-tools: "Bash(find *) Read(*)"
license: MIT
metadata:
  author: your-username
  version: "0.1.0"
---
```

### Umbrella SKILL.md

The root `SKILL.md` at the repo root is the umbrella manifest. It describes the entire skillset and lists all available sub-skill commands in its `description` field. This is what agents read to understand what the skillset can do.

## Agent instruction files

### GENO.md — the single source of truth

`GENO.md` at the repo root is the canonical instruction file that any agent reads to understand the repo. It should contain:

1. **Title and summary** — one-line description of the skillset
2. **Skills table** — every skill with its name and slash command
3. **Repo structure** — tree of key files and directories
4. **Conventions** — rules for modifying code in this repo, including:
    - How skills are named in this repo
    - SKILL.md frontmatter format
    - Checklist for adding a new skill
    - Command prefix aliasing (see below)
    - Versioning: which files contain the version and when to bump (see [Versioning](#versioning))

### Per-agent pointer files

Each agent looks for a different filename. Create thin pointers — no content, just an import:

| File | Content |
|------|---------|
| `CLAUDE.md` | `@./GENO.md` |
| `GEMINI.md` | `@./GENO.md` |
| `AGENTS.md` | `@import GENO.md` |

This way, updating `GENO.md` updates every agent at once.

## Command prefix aliasing

Slash commands use a configurable prefix. Users set their preferred prefix in `~/.geno/config.yaml`:

```yaml
aliases:
  command_prefix: "gt"   # /gt-myskill, /gt-myskill-tasks-start
  # or "geno"            # /geno-myskill, /geno-myskill-tasks-start
  # or ""                # /myskill, /myskill-tasks-start
```

The prefix is applied when the skill is baked into an environment. **Repo source files must always use the canonical `geno-` prefix.** Never hardcode `gt-` or any other alias in:

- SKILL.md `description` fields
- SKILL.md body content
- GENO.md skills tables and section headers
- README.md, docs, or any committed file

The canonical name is the skill's `name` field in frontmatter — use that everywhere.

## Agent-agnostic language

The geno ecosystem is CLI-agnostic — skillsets work with Claude Code, Antigravity CLI, Codex, OpenCode, and any future coding agent. Use generic terms like "coding agent" or "agent session" instead of naming a specific agent. When listing prerequisites, mention the supported agents generically.

## Testing locally

Your repo is a **layer**: a `layer.json` plus skills under `skills/<category>/<name>/SKILL.md`. To test it, add it to a `geno-image.yaml` and bake:

```yaml
layers:
  - ./layers/meta-geno-core
  - ~/src/geno-myskill          # your local checkout

install:
  - core/my-new-skill
```

```bash
geno bake
```

Edits take effect on the next bake (the builder shows a drift banner when the build is stale). When you're happy, push to a git remote and others can consume it as a remote layer:

```yaml
layers:
  - https://github.com/you/geno-myskill
```

## Making your layer discoverable

Declare your ecosystem category in `layer.json` at the repo root — the interactive builder groups layers by it during discovery:

```json
{
  "name": "geno-myskill",
  "ecosystem": "geno-ecosystem / Developer Tools"
}
```

## Compliance

Every `geno bake` runs the built-in compliance scan over your skills — curl-pipe-sh installs, prompt-injection phrasing, credential access, destructive commands, and over-broad `allowed-tools` grants. Error-severity findings block the bake, so fix them (or justify them via the manifest's `audit: allow:` list) before publishing. For full ecosystem-convention checks, run the `geno-audit` skill against your repo; see the [audit process](../onboarding/audit.md) for details.

!!! note "Skillsets vs. plugins"
    Ecosystem skillsets use the skills format (`SKILL.md` + `skills/`) and are consumed as layers by `geno bake`. Agents install the compiled `build/` output, never a skillset repo directly.
