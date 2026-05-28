---
title: geno-iso-containers-run
description: Spin up an isolated coding agent container with a mounted workspace
---

# geno-iso-containers-run

`/geno-iso-containers-run "[name] [workspace-path] [--rm] [-- agent-args...]"`

> Spin up an isolated coding agent container with a mounted workspace

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — optional container name and workspace path.

If empty, derive the name from the current working directory.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

1. Check if the Docker image exists: `geno-iso ls` or `docker images geno-iso --quiet`
2. If no image, build it: `geno-iso build`
3. For a persistent container: `geno-iso run $ARGUMENTS`
4. For a one-shot prompt: `geno-iso run --rm $ARGUMENTS -- -p "prompt" --max-turns 1`
5. Report the container name and how to enter it

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-iso](index.md)
