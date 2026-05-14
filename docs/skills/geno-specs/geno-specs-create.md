---
title: geno-specs-create
description: Create a new structured execution spec
---

# geno-specs-create

`/geno-specs-create "[title or template:name]"`

> Create a new structured execution spec

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` is optional. Formats:
- `title words here` — create a spec with that title
- `template:bug-fix Title here` — use a template
- (empty) — interactive mode

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Determine scope

Check if a project scope exists (`./geno/geno-specs/`). If not, ask the user:
- Initialize project scope here
- Use global scope (`~/.geno/geno-specs/`)

### 2. Parse arguments

If `$ARGUMENTS` starts with `template:`, extract the template name and remaining title.

If no arguments, use `AskUserQuestion` to gather:
- Title (required)
- Template (optional — show available templates)
- Tags (optional)

### 3. Create the spec file

Run:
```bash
geno-specs create "Title" [--template name] [--tag tag1 --tag tag2]
```

### 4. Fill in the spec

Read the created spec file. Then help the user fill in the key sections interactively:

1. **Context** — what problem this solves, background information
2. **Inputs** — files the agent needs to read
3. **Steps** — ordered execution steps (templates pre-fill these)
4. **Outputs** — files that should exist/change when done
5. **Checks** — commands to validate completion (e.g., `pytest`, `ruff check`)
6. **Acceptance criteria** — human-readable done conditions
7. **Agent requirements** — capabilities needed, preferred model

Use `geno-specs edit <id>` to add each piece:
```bash
geno-specs edit <id> --add-input "src/auth.py:Current auth module"
geno-specs edit <id> --add-output "src/auth.py:contains TokenRefresher"
geno-specs edit <id> --add-check "pytest tests/:exit 0"
geno-specs edit <id> --add-step "Implement the refresh logic"
geno-specs edit <id> --agent-cap python --agent-cap api
```

Or edit the markdown file directly — it's YAML frontmatter + markdown body.

### 5. Mark ready (optional)

Ask if the spec is complete. If yes:
```bash
geno-specs ready <id>
```

### 6. Report

Show the final spec and its file path. Suggest next steps:
- `geno-specs show <id> --prompt` to preview the agent prompt
- `geno-specs run <id>` to execute
- Edit the file directly for fine-tuning

## Available Templates

| Template | Use case |
|---|---|
| `bug-fix` | Fix a bug: reproduce, root-cause, patch, verify |
| `feature` | Add a new feature end-to-end |
| `refactor` | Restructure code without changing behavior |
| `migration` | Data, schema, or API migration |
| `test` | Add or improve test coverage |
| `review` | Code review with structured feedback |

## Completion

When this skill finishes (success, failure, or abandoned), emit a trace:

```bash
geno-trace emit \
  --skill geno-specs-create \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors> \
  --scope project \
  --produced "<path to created spec file>"
```

- `success` = spec file created with populated frontmatter and body sections
- `failure` = spec creation command failed or scope could not be initialized
- `abandoned` = user cancelled before completing required fields

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-specs`

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-specs](index.md)
