---
name: geno-tools-author-repo
description: >-
  Scaffold a new geno ecosystem skillset repo from scratch. Creates the full
  directory structure (genotools.yaml, GENO.md, CLAUDE.md, umbrella SKILL.md,
  docs, specs, CI) and initializes git. Use when user says
  /geno-tools-create-skillset-repo, wants to create a new geno-* repo, or
  bootstrap a new skillset from scratch.
argument-hint: "[skillset-name|freeform description]"
allowed-tools: "Bash(mkdir *) Bash(ln *) Bash(ls *) Bash(find *) Bash(git *) Bash(gh *) Bash(geno-tools *) Read(*) Write(*) Edit(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-tools-create-skillset-repo — Skillset Repo Scaffolder

Creates a new `geno-{name}` skillset repo from scratch with the full directory structure required by the geno ecosystem. This is the repo-level counterpart to `geno-skills-create`, which adds skills to existing repos.

## When to invoke

- The user wants to create a brand new skillset repo (not add a skill to an existing repo).
- The user says "create a new geno repo", "bootstrap a skillset", "scaffold a new skillset".
- The user is starting a new domain of skills that doesn't fit any existing skillset.

## Input

`$ARGUMENTS` is either:
- A skillset name (e.g. `geno-pipelines`, `geno-career`) — skip naming, go straight to details
- Freeform text describing what the skillset should do — use it to derive the name
- Empty — launch the interactive flow

## Workflow

### 1. Determine the skillset name

If `$ARGUMENTS` contains a name matching `geno-*`, use it directly. Strip `geno-` to get the bare slug.

If `$ARGUMENTS` is freeform or empty, ask:

> What domain does this skillset cover? Give a short name (1-2 words, noun).
> Examples: pipelines, career, fitness, finance

Construct `geno-{slug}` from the answer. The slug must be:
- Lowercase, hyphen-separated if multi-word
- A noun or noun phrase (not a verb)
- Not already taken — check with `geno-tools ls --available 2>/dev/null` and `ls ~/.geno-tools/`

Record:
- `$NAME` — the bare slug (e.g. `career`)
- `$REPO` — the full repo name (e.g. `geno-career`)

### 2. Gather details

Use `AskUserQuestion` to collect:

> Describe what this skillset does in 1-2 sentences.

From the description, draft:
- `$DESCRIPTION` — one-line description for genotools.yaml and README
- `$LONG_DESCRIPTION` — opening paragraph for GENO.md

Ask the user to confirm or edit.

### 3. Choose optional features

Use `AskUserQuestion` (multiSelect):

> Which optional features should this skillset include?
> - **Python package** — adds pyproject.toml and a Python package directory
> - **Dependencies** — this skillset depends on other geno-* skillsets
> - **GitHub repo** — create the remote repo on GitHub after scaffolding

Record selections:
- `$HAS_PYTHON` — boolean
- `$DEPS` — list of dependency names (ask follow-up if selected)
- `$CREATE_REMOTE` — boolean

### 4. Determine target directory

Check for a workspace context:
- If inside a workspace (has `.geno/.workspace/workspace.yaml`), scaffold inside the workspace root.
- Otherwise, scaffold in the current working directory.

The repo will be created at `$TARGET_DIR/$REPO/`.

Verify the directory doesn't already exist. If it does, warn and ask whether to overwrite.

### 5. Scaffold the repo

Create the following structure. Every file is described below with its exact content.

```
$REPO/
├── .github/
│   └── workflows/
│       └── docs.yml
├── .specs/
│   ├── VISION.md
│   ├── GOALS.md
│   ├── TENETS.md
│   └── features/
├── docs/
│   ├── index.md
│   ├── getting-started.md
│   └── stylesheets/
│       └── extra.css
├── skills/
│   └── $REPO/
│       └── SKILL.md          # umbrella skill
├── .gitignore
├── CLAUDE.md
├── GENO.md
├── README.md
├── SKILL.md                  # symlink -> skills/$REPO/SKILL.md
├── genotools.yaml
└── mkdocs.yml
```

If `$HAS_PYTHON` is true, also create:
```
├── pyproject.toml
└── ${REPO_UNDERSCORE}/       # geno_{name} with hyphens → underscores
    └── __init__.py
```

#### 5a. `genotools.yaml`

```yaml
name: $REPO
version: "0.1.0"
description: $DESCRIPTION
```

If `$DEPS` is non-empty, add:
```yaml
requires:
  - $DEP1
  - $DEP2
```

#### 5b. `GENO.md`

```markdown
# $REPO — $TITLE

$LONG_DESCRIPTION

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| $REPO | /$REPO | Umbrella — lists available skills |

## Repo structure

```
$REPO/
├── GENO.md
├── SKILL.md -> skills/$REPO/SKILL.md
├── genotools.yaml
└── skills/
    └── $REPO/SKILL.md
```
```

#### 5c. `CLAUDE.md`

```
@./GENO.md
```

#### 5d. `.gitignore`

```
__pycache__/
*.pyc
.geno/
```

#### 5e. `README.md`

```markdown
# $REPO

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://42euge.github.io/$REPO/)

$DESCRIPTION

Part of the [geno ecosystem](https://github.com/42euge/geno-tools).

## Installation

```bash
geno-tools install $REPO
```
```

#### 5f. `skills/$REPO/SKILL.md` (umbrella)

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

#### 5g. `SKILL.md` (root symlink)

```bash
ln -s skills/$REPO/SKILL.md SKILL.md
```

#### 5h. `mkdocs.yml`

```yaml
site_name: $REPO
site_description: $DESCRIPTION
site_url: https://42euge.github.io/$REPO/
repo_url: https://github.com/42euge/$REPO
repo_name: 42euge/$REPO

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
    - navigation.tabs
    - navigation.tabs.sticky
    - navigation.sections
    - navigation.top
    - content.code.copy
    - content.code.annotate
    - search.highlight
    - search.suggest
    - toc.follow

nav:
  - Home: index.md
  - Getting Started: getting-started.md

extra_css:
  - stylesheets/extra.css

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
  - md_in_html
  - def_list
  - toc:
      permalink: true

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/42euge
  generator: false
```

#### 5i. `docs/index.md`

```markdown
# $REPO

$DESCRIPTION

## Installation

```bash
geno-tools install $REPO
```

## Quick Start

See [Getting Started](getting-started.md) for usage instructions.

## Links

- [GitHub](https://github.com/42euge/$REPO)
- [Docs](https://42euge.github.io/$REPO/)
```

#### 5j. `docs/getting-started.md`

```markdown
# Getting Started

## Prerequisites

- [geno-tools](https://github.com/42euge/geno-tools) installed

## Installation

```bash
geno-tools install $REPO
```

## Usage

Run `/$REPO` in Claude Code to get started.
```

#### 5k. `docs/stylesheets/extra.css`

```css
:root {
  --md-primary-fg-color: #1a0a2e;
  --md-primary-fg-color--light: #2d1b4e;
  --md-primary-fg-color--dark: #0f0619;
  --md-accent-fg-color: #e8650a;
}
[data-md-color-scheme="slate"] {
  --md-primary-fg-color: #1a0a2e;
  --md-accent-fg-color: #f0923a;
  --md-default-bg-color: #0e0b14;
}
.md-header {
  background: linear-gradient(135deg, #1a0a2e 0%, #2d1050 50%, #3a1560 100%);
}
.md-tabs {
  background: linear-gradient(135deg, #0f0619 0%, #1a0a2e 100%);
}
.md-footer {
  background: linear-gradient(135deg, #0f0619, #1a0a2e);
}
```

#### 5l. `.specs/VISION.md`

```markdown
# Vision

$DESCRIPTION

## Why this exists

<!-- What problem does $REPO solve? Who benefits? -->

## Where we're headed

<!-- What does the world look like when $REPO succeeds? -->
```

#### 5m. `.specs/GOALS.md`

```markdown
# Goals

Current goals for $REPO. Review and update regularly.

## Active

- <!-- Goal 1: description, target date -->

## Completed

- <!-- Moved here when done -->

## Deferred

- <!-- Moved here when deprioritized -->
```

#### 5n. `.specs/TENETS.md`

```markdown
# Tenets

Architectural principles that guide development decisions in $REPO. When tenets conflict, earlier entries take precedence.

1. **<!-- Tenet 1 -->** — <!-- Description -->
2. **<!-- Tenet 2 -->** — <!-- Description -->
3. **<!-- Tenet 3 -->** — <!-- Description -->
```

#### 5o. `.specs/features/` (empty directory)

Create with a `.gitkeep`:

```bash
mkdir -p .specs/features && touch .specs/features/.gitkeep
```

#### 5p. `.github/workflows/docs.yml`

```yaml
name: Deploy docs to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
      - run: pip install mkdocs-material
      - run: mkdocs build
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

#### 5q. `pyproject.toml` (only if `$HAS_PYTHON`)

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

#### 5r. Python package (only if `$HAS_PYTHON`)

Create `${REPO_UNDERSCORE}/__init__.py` where `$REPO_UNDERSCORE` is `$REPO` with hyphens replaced by underscores (e.g. `geno_career`):

```python
__version__ = "0.1.0"
```

### 6. Initialize git

```bash
cd $TARGET_DIR/$REPO
git init
git add -A
git commit -m "Initial scaffold via geno-tools-create-skillset-repo"
```

### 7. Create GitHub remote (only if `$CREATE_REMOTE`)

```bash
gh repo create 42euge/$REPO --private --source . --push --description "$DESCRIPTION"
```

Use `--private` by default. Ask the user if they want public instead.

After push, enable GitHub Pages:
```bash
gh api repos/42euge/$REPO/pages -X POST -f build_type=workflow 2>/dev/null || true
```

### 8. Report

Tell the user what was created:

```
Created $REPO at $TARGET_DIR/$REPO

Files:
  genotools.yaml          — install manifest
  GENO.md                 — agent instructions
  CLAUDE.md               — Claude Code pointer
  SKILL.md                — symlink to umbrella skill
  skills/$REPO/SKILL.md   — umbrella skill definition
  mkdocs.yml              — documentation site config
  docs/                   — MkDocs Material site
  .specs/                 — vision, goals, tenets
  .github/workflows/      — GitHub Pages CI
  .gitignore              — standard ignores
  README.md               — project README
  [pyproject.toml]        — Python package (if selected)

Next steps:
  1. Add skills:        /geno-skills-create (from inside the repo)
  2. Install locally:   geno-tools install $TARGET_DIR/$REPO
  3. Audit compliance:  /geno-audit (from inside the repo)
```

## Don'ts

- Don't use aliased prefixes like `gt-` in any generated content — always use canonical `geno-` prefix.
- Don't scaffold skills beyond the umbrella — use `/geno-skills-create` for that.
- Don't overwrite an existing repo directory without asking.
- Don't commit `.geno/` or `CLAUDE.local.md` in the initial commit.
- Don't create GEMINI.md or AGENTS.md — these are not currently used in the ecosystem and would be stale pointers.
- Don't invent skill content in the umbrella — it should just list available skills (which starts as just itself).
- Don't hardcode a GitHub org other than `42euge` without asking.

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-tools-create-skillset-repo \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = repo scaffolded, git initialized, all files written
- `failure` = directory collision, git init failed, or file write failed
- `abandoned` = user stopped during naming or detail gathering
