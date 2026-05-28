---
title: geno-notes-vault-generate
description: Generate an Obsidian vault from geno-notes content
---

# geno-notes-vault-generate

`/geno-notes-vault-generate "[--all] [--global|--project]"`

> Generate an Obsidian vault from geno-notes content

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` are passed as flags to `geno-notes vault`.


## Options

| Flag | Effect |
|------|--------|
| `--all` | Merge project + global scopes into one vault |
| `--global` | Force global scope |
| `--project` | Force project scope |

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

1. Run `geno-notes vault` with any scope flags from `$ARGUMENTS`. Pipe `n` to stdin to skip the interactive prompt: `echo n | geno-notes vault [flags]`
2. Capture the vault path from the "Vault ready →" output line.
3. Report what was generated — number of tasks, journal months, wiki pages, plans staged.
4. Ask the user if they'd like to open the vault in Obsidian.
5. If yes, open it: `open "obsidian://open?path=<vault-path>"`

## What it builds

The vault generator stages content from the active scope(s) into an Obsidian-ready directory:

- **Home.md** — Map of Content (MOC) linking to all sections
- **Tasks/** — one file per task with frontmatter, plus `_index.md` MOC grouped by status
- **Journal/** — monthly entries preserving the `YYYY/YYYY-MM.md` structure
- **Wiki/** — compiled topic pages with native `[[wikilinks]]`
- **Plans/** — task-linked planning documents
- **Inbox.md** — quick captures
- **.obsidian/** — vault config with graph view color groups, workspace defaults

## Obsidian features

- **Graph view** — color-coded by section (Tasks=purple, Journal=teal, Wiki=orange, Plans=gray)
- **Wikilinks** — `[[page]]` links work natively (geno-notes already uses this format)
- **Tags** — task tags rendered as `#tag` for Obsidian tag search
- **MOCs** — Home and Tasks index pages for navigation

## Examples

```bash
geno-notes vault
geno-notes vault --all
geno-notes vault --project
```

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.

</div>

</div>

[:material-arrow-left: Back to geno-notes](index.md)
