# Repo Template

Boilerplate files for the root of a new `geno-{name}` skillset repo. The orchestrator substitutes the variables `$REPO`, `$NAME`, `$DESCRIPTION`, `$LONG_DESCRIPTION`, `$TITLE`, `$DEPS`, `$REPO_UNDERSCORE` (the repo name with hyphens replaced by underscores) when rendering each template.

## Directory tree

```
$REPO/
├── .github/
│   └── workflows/
│       └── docs.yml          # see ci-template.md
├── .specs/
│   ├── VISION.md             # see docs-template.md
│   ├── GOALS.md              # see docs-template.md
│   ├── TENETS.md             # see docs-template.md
│   └── features/.gitkeep
├── docs/                     # see docs-template.md
│   ├── index.md
│   ├── getting-started.md
│   └── stylesheets/extra.css
├── skills/
│   └── $REPO/SKILL.md        # umbrella skill (this file)
├── .gitignore
├── CLAUDE.md
├── GENO.md
├── README.md
├── SKILL.md                  # symlink → skills/$REPO/SKILL.md
├── genotools.yaml
└── mkdocs.yml                # see docs-template.md
```

If `$HAS_PYTHON` is true, also:
```
├── pyproject.toml
└── ${REPO_UNDERSCORE}/
    └── __init__.py
```

## `genotools.yaml`

```yaml
name: $REPO
version: "0.1.0"
description: $DESCRIPTION
```

If `$DEPS` is non-empty, append:
```yaml
requires:
  - $DEP1
  - $DEP2
```

## `GENO.md`

```markdown
# $REPO — $TITLE

$LONG_DESCRIPTION

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| $REPO | /$REPO | Umbrella — lists available skills |

## Repo structure

$REPO/
├── GENO.md
├── SKILL.md -> skills/$REPO/SKILL.md
├── genotools.yaml
└── skills/
    └── $REPO/SKILL.md
```

## `CLAUDE.md`

```
@./GENO.md
```

## `.gitignore`

```
__pycache__/
*.pyc
.geno/
```

## `README.md`

```markdown
# $REPO

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://42euge.github.io/$REPO/)

$DESCRIPTION

Part of the [geno ecosystem](https://github.com/42euge/geno-tools).

## Installation

\`\`\`bash
geno-tools install $REPO
\`\`\`
```

## `skills/$REPO/SKILL.md` (umbrella)

```markdown
---
name: $REPO
description: >-
  $DESCRIPTION
  Use when user says /$REPO.
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# $REPO

$LONG_DESCRIPTION

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| $REPO | /$REPO | Umbrella — lists available skills |
```

## `SKILL.md` (root symlink)

```bash
ln -s skills/$REPO/SKILL.md SKILL.md
```

## `pyproject.toml` (only if `$HAS_PYTHON`)

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "$REPO"
version = "0.1.0"
description = "$DESCRIPTION"
requires-python = ">=3.10"
license = "MIT"
authors = [{ name = "42euge" }]
```

## `${REPO_UNDERSCORE}/__init__.py` (only if `$HAS_PYTHON`)

```python
__version__ = "0.1.0"
```
