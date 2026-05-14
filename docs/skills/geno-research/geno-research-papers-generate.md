---
title: geno-research-papers-generate
description: Generate an academic paper (workshop / extended abstract style) from research findings
---

# geno-research-papers-generate

`/geno-research-papers-generate`

> Generate an academic paper (workshop / extended abstract style) from research findings

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Optional instructions (e.g., "focus on adversarial noise findings", "target NeurIPS workshop format", "max 4 pages"). If empty, generate a complete paper covering all findings.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Output Location

`paper/` directory in the current working directory. Creates:
- `paper/paper.md` — the paper in Markdown (primary output)
- `paper/figures/` — any generated figures or diagrams (ASCII/Mermaid/description)

## Workflow

### Step 1: Gather all evidence

Read these sources **in parallel** to build the complete picture:

**Code & data:**
- `src/generate.py` — how the dataset is constructed (passage generation, noise types, interleaving)
- `src/benchmark.py` — task definitions, evaluation metrics
- `src/analyze.py` — analysis methods and metrics
- `data/manifest.json` — dataset statistics
- `notebooks/kaggle_benchmark.ipynb` — the evaluation notebook (cell-by-cell)

**Results:**
- `results/` — all result directories. Read the `.run.json` files to extract actual numbers. Focus on the latest version (highest v-number).
- Parse results to build tables: accuracy by model x noise_type x noise_ratio, vigilance accuracy by model x task_type x position

**Documentation & context:**
- Project tasks and journal via `geno-notes` (scope auto-resolves — project if one exists, else global):
  - `geno-notes list --json --all` — planned vs completed tasks (add `--all` to union project + global)
  - `$(geno-notes path)/journal/**/*.md` — development history, bug discoveries, key findings; entries tagged by kind (note/finding/decision/bug/milestone)
  - `geno-notes search <term> --all` — pull findings across related repos when synthesizing cross-project narrative
- Existing documentation
- Agent instruction files — project context and track description
- `README.md` — project overview

**Research context:**
- Walk up to 3 parent directories looking for `research/` folders
- Read any relevant research notes for theoretical grounding

**Git history:**
- `git log --oneline -30` — development trajectory and key milestones

### Step 2: Analyze and synthesize

Before writing, form a clear understanding of:

1. **The research question** — what gap does this benchmark fill?
2. **The methodology** — how was the benchmark constructed and why those choices?
3. **The results** — what did we actually find? Build precise tables from run data.
4. **The insights** — what do the results tell us about LLM attention?
5. **The limitations** — what doesn't the benchmark capture? What went wrong?
6. **The contribution** — what's novel here that others should know?

Compute any statistics not already in the notes:
- Effect sizes between model families
- Correlation between model size and adversarial threshold
- Statistical significance of key comparisons (if enough samples)

### Step 3: Write the paper

Write `paper/paper.md` following standard academic structure: Abstract, Introduction, Methodology, Results, Discussion, Related Work, Conclusion, References, and Appendix.

### Step 4: Generate supporting materials

- Extract or generate key figures as descriptions in `paper/figures/`

### Step 5: Review and polish

Re-read the paper and check:
- Every claim is supported by data from the results
- Tables contain actual numbers (not placeholders)
- The narrative flows logically from problem to method to results to insight
- The writing is concise and precise (no filler)
- Technical details are correct
- The paper honestly addresses limitations
- The contribution is clearly stated

### Step 6: Report

Print a summary with sections, word count, key findings highlighted, and any gaps/TODOs.

## Important Guidelines

- **Data-driven**: Every claim must trace back to actual run results. Parse the JSON files — don't rely solely on lab notes summaries.
- **Honest**: Report what we found, including surprises and failures.
- **Specific**: Use exact numbers, model names, and noise ratios.
- **Novel framing**: Emphasize what's new.
- **Concise**: Aim for 3,000-5,000 words. Workshop paper length, not a full conference paper.
- **No fluff**: Every sentence should add information. Cut filler ruthlessly.
- **Version awareness**: Use the latest results (highest version number).

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.

</div>

</div>

[:material-arrow-left: Back to geno-research](index.md)
