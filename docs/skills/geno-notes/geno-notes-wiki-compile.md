---
title: geno-notes-wiki-compile
description: Compile primary sources (tasks, journal, plans) into wiki pages using the Karpathy llm-wiki pattern
---

# geno-notes-wiki-compile

`/geno-notes-wiki-compile "[--global|--project]"`

> Compile primary sources (tasks, journal, plans) into wiki pages using the Karpathy llm-wiki pattern

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` are passed as flags to `geno-notes compile`.


## Options

| Flag | Effect |
|------|--------|
| `--global` | Force global scope |
| `--project` | Force project scope |

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

1. Run `geno-notes compile` — this dumps all source material AND existing wiki pages.
2. Read the output. Identify distinct topics, entities, themes, and connections across the sources.
3. For each topic, either **update an existing wiki page** or **create a new one**:
   - Write to `<scope-dir>/wiki/<topic-slug>.md`
   - Use `[[page-name]]` wikilinks to connect related pages
   - Cite source tasks by ID (e.g. `(task: 20260425-auth-flow)`) and journal entries by date
   - Include YAML frontmatter: `tags`, `sources` (list of task IDs / journal months referenced), `updated` (ISO date)
4. Update `<scope-dir>/wiki/index.md` — a catalog of every wiki page with a link and one-line summary, organized by category.
5. Log the compile: `geno-notes note "wiki compile: N pages created, M updated" --kind milestone`

## Page guidelines

- Each page covers one distinct topic, entity, or concept
- Pages should be self-contained but link to related pages
- Prefer updating over creating — the wiki compounds over time
- When sources contradict, note the contradiction and cite both sides
- Status-aware: reflect task statuses (done = resolved, active = in progress, abandoned = dropped)

## Examples

```bash
geno-notes compile
geno-notes compile --global
geno-notes compile --project
```

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-notes](index.md)
