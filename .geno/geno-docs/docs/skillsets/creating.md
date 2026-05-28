# Creating a Skillset

Build your own `geno-{name}` skillset that geno-tools can install, update, and manage.

> geno layers conventions on top of the upstream Agent Skills format from `vercel-labs/agent-skills`. If you're coming from upstream or planning to publish to a wider audience, see [Upstream Conventions](upstream-conventions.md) for what's shared, what's extended, and migration recipes.

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

The prefix is applied at install time by `geno-tools install`. **Repo source files must always use the canonical `geno-` prefix.** Never hardcode `gt-` or any other alias in:

- SKILL.md `description` fields
- SKILL.md body content
- GENO.md skills tables and section headers
- README.md, docs, or any committed file

The canonical name is the skill's `name` field in frontmatter — use that everywhere.

## Agent-agnostic language

The geno ecosystem is CLI-agnostic — skillsets work with Claude Code, Gemini CLI, Codex, OpenCode, and any future coding agent. Use generic terms like "coding agent" or "agent session" instead of naming a specific agent. When listing prerequisites, mention the supported agents generically.

## Testing locally

Use `dev` to link your local checkout:

```bash
geno-tools dev geno-myskill ~/src/geno-myskill
```

Edits take effect immediately. When you're happy, push to a git remote and others can install it:

```bash
geno-tools install https://github.com/you/geno-myskill.git
```

## Adding to the registry

To add your skillset to the built-in registry, submit a PR adding an entry to `genotools/registry.py`:

```python
_FALLBACK: dict[str, str] = {
    # ...existing entries...
    "geno-myskill": "https://github.com/you/geno-myskill.git",
}
```

## Compliance

Run `geno-audit` against your repo before submitting. It checks all ecosystem conventions — manifest, skills, naming, GENO.md content, aliasing, docs, and more. See the [audit process](../onboarding/audit.md) for details.

!!! note "Skillsets vs. plugins"
    Ecosystem skillsets use the skills format (`SKILL.md` + `skills/`) and are installed via `geno-tools install`. Only geno-tools itself ships as a coding agent plugin to provide the install, remove, and list commands.
