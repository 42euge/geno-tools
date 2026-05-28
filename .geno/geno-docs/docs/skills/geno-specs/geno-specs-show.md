---
title: geno-specs-show
description: Show a spec's full contents, as JSON, or as an agent-executable prompt
---

# geno-specs-show

`/geno-specs-show "<spec-id> [--prompt|--json]"`

> Show a spec's full contents, as JSON, or as an agent-executable prompt

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` is the spec ID, optionally followed by `--prompt` or `--json`.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

```bash
geno-specs show <spec-id> [--prompt] [--json]
```

- Default: show the raw spec file (YAML frontmatter + markdown body)
- `--prompt`: render as a self-contained agent prompt (what an agent would receive)
- `--json`: structured JSON for machine consumption

## Completion

When this skill finishes (success or failure), emit a trace:

```bash
geno-trace emit \
  --skill geno-specs-show \
  --status <success|failure> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors> \
  --scope project
```

- `success` = spec contents displayed in the requested format
- `failure` = spec ID not found, ambiguous match, or show command failed

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-specs](index.md)
