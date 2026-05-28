---
title: geno-tools-create-skillset-repo
description: Scaffold a new geno ecosystem skillset repo from scratch
---

# geno-tools-create-skillset-repo

`/geno-tools-create-skillset-repo [skillset-name|freeform description]`

> Scaffold a new geno ecosystem skillset repo from scratch — creates the full directory structure, initializes git, and wires all agent instruction files

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Usage

Scaffold by explicit name:
```
/geno-tools-create-skillset-repo geno-finance
```

Describe what you want and let the skill pick the name:
```
/geno-tools-create-skillset-repo "skillset for tracking household budgets and expenses"
```

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## What gets created

```
geno-{name}/
├── genotools.yaml          # install manifest (name, version, description)
├── GENO.md                 # agent instructions
├── CLAUDE.md               # → @./GENO.md
├── GEMINI.md               # → @./GENO.md
├── AGENTS.md               # → @import GENO.md
├── SKILL.md                # → skills/geno-{name}/SKILL.md (symlink)
├── pyproject.toml          # Python package scaffold (optional)
├── skills/
│   └── geno-{name}/
│       └── SKILL.md        # umbrella skill definition
├── docs/
│   ├── index.md
│   └── getting-started.md
├── mkdocs.yml              # MkDocs Material config
├── .specs/
│   ├── GOALS.md
│   └── TENETS.md
├── .github/
│   └── workflows/
│       └── docs.yml        # GitHub Pages deploy
└── .gitignore
```

## What it does NOT create

- Individual sub-skill SKILL.md files — use `/geno-skills-create` for those
- Python source code — just the package scaffold
- Tests — add those manually or via `/geno-skills-create`

## After creation

1. `cd geno-{name} && git init && git add . && git commit -m "init: scaffold geno-{name}"`
2. Create a GitHub repo: `gh repo create 42euge/geno-{name} --public`
3. Push: `git remote add origin git@github.com:42euge/geno-{name}.git && git push -u origin main`
4. Install into geno-tools: `geno-tools install geno-{name}`

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Repo-level scaffolding** — this is the repo-level counterpart to `geno-skills-create`, which adds individual skills to an existing repo. Use this to bootstrap a brand new skillset from nothing.
- **Canonical structure** — generated repos pass the `geno-audit` compliance checks out of the box.

</div>

</div>

[:material-arrow-left: Back to geno-tools](index.md)
