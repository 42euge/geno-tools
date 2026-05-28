---
title: geno-term-sessions-restart
description: Restart coding agent sessions in a project tree after a crash by opening them as iTerm2 tabs and panes grouped by wor...
---

# geno-term-sessions-restart

`/geno-term-sessions-restart "<target_dir>"`

> Restart coding agent sessions in a project tree after a crash by opening them as iTerm2 tabs and panes grouped by wor...

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — the target directory. Defaults to the current working directory if empty.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Steps

1. Resolve `$ARGUMENTS` (or `pwd`) to an absolute path.
2. Run `geno-term discover "<path>"` and show the user the grouped list.
3. Ask before restarting if more than 8 sessions would open.
4. Run `geno-term restart "<path>"`.
5. Report the number of tabs and panes opened.

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-term](index.md)
