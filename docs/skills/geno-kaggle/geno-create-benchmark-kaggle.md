---
title: geno-create-benchmark-kaggle
description: "Create Kaggle Benchmark Notebook"
---

# geno-create-benchmark-kaggle

`/geno-create-benchmark-kaggle`

> "Create Kaggle Benchmark Notebook"

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Description of the benchmark to create. Can include:
- Track name (learning, metacognition, attention, executive functions, social cognition)
- Task description (what cognitive ability to test)
- Output path for the notebook
- (empty) — enter interactive mode to gather details

Examples:
- `attention "selective attention with distractor scaling" tasks/attention_v2.ipynb`
- `learning "in-context rule induction across difficulty tiers"`
- (empty) — ask the user what benchmark to create

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Kaggle Benchmark Environment Constraints

These are hard constraints for the generated notebook:

- **No `git` installed** — cannot `git clone`. Use `urllib.request.urlretrieve` for file downloads.
- **No `matplotlib` pre-installed** — must `pip install -q matplotlib` before importing.
- **Python 3.11** (not 3.12+) — avoid 3.12+ syntax like `type` statements.
- **SDK is pre-installed** — do NOT include `pip install kaggle-benchmarks`. It causes protobuf conflicts.
- **`papermill` runs the notebook** — first cell error stops execution entirely. Guard risky operations.
- **Markdown cells must NOT have `outputs` key** — invalid nbformat.
- **`kbench.llm` (singular) is required** — this is the placeholder the platform swaps when running different models via "Add Models" UI.
- **Task functions must have `llm` as first parameter** with return type annotation.

## Workflow

### 1. Gather benchmark specification

If `$ARGUMENTS` is empty or incomplete, prompt the user to provide:
- **Track**: Which of the 5 tracks?
- **Cognitive ability**: What specific ability within the track to test?
- **Task design**: How will the task work? What does the model need to do?
- **Data source**: Will data be generated inline, loaded from JSON embedded in the notebook, or fetched from a URL?
- **Evaluation metric**: How is correctness determined? (exact match, fuzzy match, scoring rubric)
- **Difficulty gradient**: How does difficulty scale? (what makes items harder)
- **Output path**: Where to save the notebook (default: `tasks/<track>_benchmark.ipynb`)

If the user provides a description, infer as much as possible and confirm the plan before generating.

### 2. Plan the notebook structure

Enter plan mode and design the notebook with these cells:

1. **Title + description** (markdown) — benchmark name, track, what it measures
2. **Imports + SDK setup** (code) — import kaggle_benchmarks, define helpers
3. **Data generation / loading** (code) — create or embed the evaluation dataset as a DataFrame
4. **Task definition** (code) — `@kbench.task` decorated function(s) with `llm` as first param
5. **Run evaluation** (code) — call `task.evaluate()` using `kbench.llm` as the default model
6. **Results analysis** (code) — aggregate results, compute metrics, print summary table
7. **Visualization** (code, optional) — plots if matplotlib is useful for showing discriminatory power

### 3. Generate the notebook

Create a valid `.ipynb` file (JSON format) with the planned cells. Follow these rules strictly:

**Notebook JSON structure:**
```json
{
  "cells": [...],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python",
      "version": "3.11.0"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}
```

**Code cell structure:**
```json
{
  "cell_type": "code",
  "execution_count": null,
  "id": "<unique-id>",
  "metadata": {},
  "outputs": [],
  "source": ["line1\n", "line2\n", "line3"]
}
```

**Markdown cell structure (NO `outputs` key):**
```json
{
  "cell_type": "markdown",
  "id": "<unique-id>",
  "metadata": {},
  "source": ["# Title\n", "\n", "Description"]
}
```

**Critical rules for the generated code:**

- Import `kaggle_benchmarks as kbench` (no try/except needed — SDK is pre-installed)
- Every `@kbench.task` function must have `llm` as first parameter
- Every task function must have a return type annotation (`-> bool`, `-> float`, `-> tuple[int, int]`)
- Use `kbench.llm` for the primary evaluation (the platform-swappable model)
- Include `description=` in `@kbench.task()` decorator
- Evaluation data must be a pandas DataFrame with columns matching the task function parameters (excluding `llm`)
- For `tuple[int, int]` returns, include conversion logic: `df["accuracy"] = df["result"].apply(lambda r: r[0]/r[1] if isinstance(r, tuple) else float(r))`
- Add `strip_thinking()` helper to handle reasoning models (`<think>...</think>` blocks)
- Parse answers with `^\d+[\.\)\:\-]` prefix patterns; skip non-numbered preamble lines
- If matplotlib is needed, add `!pip install -q matplotlib` in the cell BEFORE the import
- Print `kbench.llms.keys()` early so available models are visible in logs
- All data must be self-contained in the notebook (inline generation or embedded JSON) — no external file dependencies

**Template for the task function pattern:**

```python
import kaggle_benchmarks as kbench
import pandas as pd
import re
import json

def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from reasoning model output."""
    if "</think>" in text:
        return text.split("</think>", 1)[1].strip()
    return text.strip()

@kbench.task(
    name="task_name",
    description="What this task measures"
)
def task_name(llm, prompt: str, expected: str) -> bool:
    response = llm.prompt(prompt)
    response = strip_thinking(response)
    # ... evaluation logic ...
    return response_clean == expected

# Generate evaluation data
data = [...]  # list of dicts with columns matching task params (minus llm)
df = pd.DataFrame(data)

# Run with platform-default model
runs = task_name.evaluate(
    llm=[kbench.llm],
    evaluation_data=df,
    n_jobs=2,
    timeout=120,
    max_attempts=2,
)
results = runs.as_dataframe()
print(results)
```

### 4. Validate the notebook

After writing the notebook file:

1. **Parse as JSON** — verify it's valid JSON
2. **Check nbformat** — verify `nbformat: 4`, cells array exists
3. **No `outputs` on markdown cells** — scan all cells
4. **Has `kaggle_benchmarks` import** — at least one code cell
5. **Has `@kbench.task`** — at least one task definition
6. **Task functions have `llm` first param** — check all task decorators
7. **Uses `kbench.llm`** — at least one reference to the platform model
8. **No `pip install kaggle-benchmarks`** — would break pre-installed SDK
9. **No `git clone`** — git not available in runtime
10. **Cell IDs are unique** — each cell has a distinct `id`

Report validation results as a checklist. Fix any failures.

### 5. Provide next steps

After generating and validating the notebook, print:

```
Notebook created: <path>

Next steps:
1. Review the notebook locally (open in Jupyter/VS Code)
2. Upload to Kaggle as a benchmark task:
   /geno-run-kaggle-bench <path>

   Or manually:
   - Go to https://www.kaggle.com/benchmarks/tasks/new
   - File → Import Notebook → Upload → select the .ipynb
   - Click "Run All" to verify
   - Click "Save Task" to publish

3. Add models via the "Add Models" button in the Kaggle UI
4. Monitor results with: /geno-run-kaggle-bench <path> <slug>
```

## Important Notes

- The notebook MUST be fully self-contained — all data generated or embedded inline
- The primary evaluation MUST use `kbench.llm` so models can be swapped via UI
- Never include `pip install kaggle-benchmarks` — the SDK is pre-installed
- Always include `strip_thinking()` helper for reasoning model compatibility
- Always include answer parsing that handles numbered prefixes and preamble lines
- Generate unique cell IDs (use short hex strings like `"a1b2c3"`)
- Target 50-200 evaluation items for good discriminatory power without excessive runtime
- Include difficulty scaling so the benchmark isn't trivially easy or impossible

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-create-benchmark-kaggle \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = valid .ipynb notebook created and all 10 validation checks pass
- `failure` = notebook generation failed, or validation checks could not be resolved
- `abandoned` = user stopped early

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-run-kaggle-bench`

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-kaggle](index.md)
