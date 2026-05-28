---
title: geno-notes-wiki-lint
description: Health-check the wiki against primary sources
---

# geno-notes-wiki-lint

`/geno-notes-wiki-lint "[--global|--project]"`

> Health-check the wiki against primary sources

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` are passed as flags to `geno-notes lint`.


## Options

| Flag | Effect |
|------|--------|
| `--global` | Force global scope |
| `--project` | Force project scope |

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

1. Run `geno-notes lint` — this dumps existing wiki pages AND all source material.
2. Read the output. Check for:
   - **Stale pages** — wiki claims that newer tasks/journal entries have superseded
   - **Orphan pages** — wiki pages with no inbound wikilinks from other pages
   - **Missing pages** — topics referenced via `[[wikilink]]` but no page exists
   - **Gaps** — important topics in the sources that have no wiki page yet
   - **Contradictions** — wiki pages that conflict with each other or with source material
   - **Dead references** — citations to task IDs or journal entries that no longer exist
3. Report findings as a checklist. For each issue, state what's wrong and suggest a fix.
4. If the user approves, apply fixes directly (update/create/delete wiki pages).
5. Log the lint: `geno-notes note "wiki lint: N issues found, M fixed" --kind milestone`

## Examples

```bash
geno-notes lint
geno-notes lint --global
geno-notes lint --project
```

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-notes](index.md)
