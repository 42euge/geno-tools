---
name: geno-tools-repos-scaffold
description: >-
  Scaffold a new geno-ecosystem repository with all required files and conventions.
  Use when user says /gt-repos-scaffold or wants to create a new geno-* project.
argument-hint: "<name> [--description 'short description'] [--python] [--docker]"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# Scaffold New Geno Repo

Create a new `geno-{name}` repository in the geno-ecosystem with all required files following ecosystem conventions.

## Input

`$ARGUMENTS` should include:
- **name** (required) — the short name (e.g. `foo` creates `geno-foo`)
- **--description** — one-line description (prompted if omitted)
- **--python** — include Python CLI scaffolding (`pyproject.toml`, `geno_name/cli.py`)
- **--docker** — include Dockerfile scaffolding

If `$ARGUMENTS` is empty, ask the user for the name and description.

## Ecosystem conventions

Every geno-* repo MUST have:

| File | Purpose |
|---|---|
| `CLAUDE.md` | Project instructions for agents, including compliance rules |
| `README.md` | Install instructions, commands table, repo structure, MIT license |
| `LICENSE` | MIT License, Copyright (c) 2025 Eugenio Ruiz |
| `.gitignore` | Standard Python/Node patterns + `.DS_Store` |
| `.geno-agents` | YAML: role, description, capabilities list |
| `package.json` | Vercel Skills manifest with name, version, description, skills map, repository |
| `skills/geno-{name}/SKILL.md` | Umbrella skill with YAML frontmatter (name, description, license, metadata) |

Skill names follow the nomenclature: `geno-{name}-{sub-skillset}-{skill-slug}` where sub-skillset is a pluralized noun. See https://42euge.github.io/geno-tools/skillsets/nomenclature/

## Workflow

### 1. Gather info

Determine from `$ARGUMENTS` or by asking:
- **name** — short kebab-case name (no `geno-` prefix, that gets added)
- **description** — one-line description
- **type** — pure markdown (default), python CLI, or docker-based

### 2. Create the repo directory

The ecosystem repos live at:
```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Everything/research/kaggle/gemma-4-good-hackathon/geno-ecosystem/repos/
```

Create `geno-{name}/` there. If it already exists, stop and tell the user.

### 3. Generate files

#### Always generated

**CLAUDE.md:**
```markdown
# geno-{name} — {description} skillset

{description} for Claude Code.

## Skills

| Skill name | Sub-skillset | Skill | Slash command |
|-----------|-------------|-------|---------------|
| `geno-{name}` | — | — | — (umbrella) |

## Compliance

This repo follows geno-ecosystem conventions. All contributors and agents must adhere to:

### Nomenclature

Skill names follow: `{skillset}-{sub-skillset}-{skill-slug}`

- **Skillset** = this repo's name: `geno-{name}`
- **Sub-skillset** = always a **pluralized noun**
- **Skill slug** = action verb
- **Umbrella** = just `geno-{name}`

Full spec: https://42euge.github.io/geno-tools/skillsets/nomenclature/

### Adding a new skill

1. Create `skills/geno-{name}-{sub-skillset}-{skill}/SKILL.md` with compliant frontmatter
2. Update the umbrella `skills/geno-{name}/SKILL.md`
3. Update `README.md` — command table and repo tree
4. Update this file's Skills table
```

**README.md:**
```markdown
# geno-{name}

{description} for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Install

\```bash
npx skills add 42euge/geno-{name}
\```

## Commands

| Command | Description |
|---|---|
| `/gt-{name}` | {description} |

## Repository structure

\```
geno-{name}/
├── package.json
├── .geno-agents
└── skills/
    └── geno-{name}/
        └── SKILL.md
\```

## Runtime

{runtime description}

## License

MIT
```

**LICENSE:** MIT License, Copyright (c) 2025 Eugenio Ruiz (use the standard text from other geno-* repos)

**.gitignore:**
```
.DS_Store
__pycache__/
*.pyc
*.py[cod]
*.egg-info/
dist/
build/
.venv/
.env
.idea/
.vscode/
```

**.geno-agents:**
```yaml
role: geno-{name}
description: {description}
capabilities:
  - {derive 2-3 capability keywords from the description}
```

**package.json:**
```json
{
  "name": "geno-{name}",
  "version": "0.1.0",
  "description": "{description}",
  "skills": {
    "geno-{name}": "skills/geno-{name}"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/42euge/geno-{name}"
  }
}
```

**skills/geno-{name}/SKILL.md:**
```markdown
---
name: geno-{name}
description: >-
  {description}.
  Use when user says /gt-{name}.
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-{name}

{description}.

## Commands

| Command | Description |
|---|---|
| `/gt-{name}` | {description} |

## Runtime

{runtime description}
```

#### If --python flag

Add:

**pyproject.toml:**
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "geno-{name}"
version = "0.1.0"
description = "{description}"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
geno-{name} = "geno_{name_underscored}.cli:main"

[tool.setuptools.packages.find]
include = ["geno_{name_underscored}*"]
```

**geno_{name_underscored}/__init__.py:** empty file

**geno_{name_underscored}/cli.py:**
```python
import argparse

def main():
    parser = argparse.ArgumentParser(description="{description}")
    parser.parse_args()

if __name__ == "__main__":
    main()
```

#### If --docker flag

Add a minimal **Dockerfile** and **build.sh** / **run.sh** scripts.

### 4. Initialize git

```bash
cd geno-{name}
git init
git add -A
git commit -m "Initial scaffold for geno-{name}"
```

### 5. Report

Tell the user:
- Where the repo was created
- What files were generated
- Next steps: add skills, commands, or a Python CLI
- How to install it: `geno-tools install /path/to/geno-{name}`
