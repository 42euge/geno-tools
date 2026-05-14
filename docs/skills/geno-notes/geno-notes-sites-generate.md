---
title: geno-notes-sites-generate
description: Generate a MkDocs Material website from geno-notes content
---

# geno-notes-sites-generate

`/geno-notes-sites-generate "[--serve] [--open] [--port PORT] [--all] [--global|--project]"`

> Generate a MkDocs Material website from geno-notes content

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` are passed as flags to `geno-notes site`.


## Options

| Flag | Effect |
|------|--------|
| `--open` | Build and open the site in the default browser |
| `--serve` | Start `mkdocs serve` for live-reloading preview |
| `--port PORT` | Port for serve mode (default 8000) |
| `--all` | Merge project + global scopes into one site |
| `--global` | Force global scope |
| `--project` | Force project scope |

Default behavior (no flags): build, then ask the user if they want to open.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Examples

```bash
geno-notes site --open
geno-notes site --serve --all
geno-notes site --serve --port 3000 --project
```

## What it builds

The site generator stages content from the active scope(s) into a temporary MkDocs project:

- **Tasks** — grouped by status (active, backlog, done, abandoned)
- **Journal** — monthly entries rendered as timeline pages
- **Wiki** — compiled topic pages with wikilinks
- **Plans** — task-linked planning documents

## Dependencies

Requires `mkdocs` and `mkdocs-material`. The CLI will prompt to install them if missing.

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.

</div>

</div>

[:material-arrow-left: Back to geno-notes](index.md)
