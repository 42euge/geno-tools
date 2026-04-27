# Creating a Skillset

Build your own `geno-{name}` skillset that geno-tools can install, update, and manage.

## Minimum viable skillset

```
geno-myskill/
├── genotools.yaml      # required — the manifest
├── SKILL.md            # umbrella description for the agent
└── commands/
    └── gt-myskill.md   # at least one slash command
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

# Optional — override the commands directory (default: "commands/")
commands:
  source: commands/
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

## SKILL.md

The umbrella manifest that describes your skillset to the agent. Use YAML frontmatter:

```markdown
---
name: geno-myskill
description: >-
  What this skillset does and when to use it.
  Use when user says /gt-myskill.
license: MIT
metadata:
  author: your-username
  version: "0.1.0"
---

# geno-myskill

Description, install instructions, command table, runtime notes.
```

## Slash commands

Each `.md` file in `commands/` becomes a `/gt-*` slash command. The filename (minus `.md`) is the command name.

Write these as instructions for the agent — what to do when the user invokes the command, what tools to use, what output to produce.

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

!!! note "Skillsets vs. plugins"
    Ecosystem skillsets use the skills format (`SKILL.md` + `commands/*.md`) and are installed via `geno-tools install`. Only geno-tools itself ships as a Claude Code plugin (`.claude-plugin/plugin.json`) to provide the `/gt-install`, `/gt-remove`, `/gt-ls`, and `/gt-update` slash commands.
