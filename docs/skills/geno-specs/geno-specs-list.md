---
title: geno-specs-list
description: List specs with optional status and tag filters
---

# geno-specs-list

`/geno-specs-list "[--status ready] [--tag feature]"`

> List specs with optional status and tag filters

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` can contain filter flags:
- `--status <status>` or just `ready`, `draft`, `running`, `done`, `failed`
- `--tag <tag>`
- `--json` for machine-readable output

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

Parse `$ARGUMENTS` for any filters, then run:

```bash
geno-specs list [--status STATUS] [--tag TAG] [--json]
```

Display the results. If the list is empty, suggest creating a spec with `/geno-specs-create`.

## Completion

When this skill finishes (success, failure, or abandoned), emit a trace:

```bash
geno-trace emit \
  --skill geno-specs-list \
  --status <success|failure> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors> \
  --scope project
```

- `success` = spec listing displayed (including empty lists with suggestion)
- `failure` = list command failed or no scope directory found

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-specs-create`

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-specs](index.md)
