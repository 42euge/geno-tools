---
title: geno-iso-containers-enter
description: Interactively enter a running geno-iso container
---

# geno-iso-containers-enter

`/geno-iso-containers-enter "[container-name] [--shell]"`

> Interactively enter a running geno-iso container

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-4" markdown>

---

## Important

`geno-iso it` uses `os.execvp` to replace the current process with an interactive Docker exec session. This cannot be run from within a skill -- the user must run it directly in their terminal.

## Workflow

1. Run `geno-iso ls --json` to show running containers
2. Tell the user to run the command directly:
   - `geno-iso it {name}` — launches the agent CLI inside the container
   - `geno-iso it {name} --shell` — launches bash instead
3. For non-interactive commands, use: `docker exec geno-iso-{name} claude -p "prompt" --max-turns 1`

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-iso](index.md)
