---
title: geno-specs-validate
description: Run a spec's completion checks
---

# geno-specs-validate

`/geno-specs-validate "<spec-id>"`

> Run a spec's completion checks

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` is the spec ID.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

```bash
geno-specs validate <spec-id>
```

This runs two categories of checks:

1. **Output checks** — verify expected output files exist and satisfy their content checks (e.g., `contains "class Foo"`)
2. **Validation commands** — run shell commands and check exit codes (e.g., `pytest` → exit 0)

Report results. If all pass and the spec is in `running` status, suggest marking it done:
```bash
geno-specs done <spec-id>
```

## Completion

When this skill finishes (success or failure), emit a trace:

```bash
geno-trace emit \
  --skill geno-specs-validate \
  --status <success|failure> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors> \
  --scope project
```

- `success` = all output checks and validation commands passed
- `failure` = one or more checks failed or spec ID not found

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-specs](index.md)
