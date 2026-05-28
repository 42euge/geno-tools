---
title: geno-run-kaggle-bench
description: "Run Kaggle Benchmark"
---

# geno-run-kaggle-bench

`/geno-run-kaggle-bench`

> "Run Kaggle Benchmark"

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Path to the `.ipynb` file to run, optionally followed by a benchmark task slug.

Examples:
- `notebooks/kaggle_benchmark.ipynb` — push and run, auto-detect or ask for task slug
- `notebooks/kaggle_benchmark.ipynb <your-kaggle-username>/new-benchmark-task-0def0` — push to specific task
- (empty) — search for `.ipynb` files and present options

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Kaggle CLI Setup

The Kaggle CLI v2.0+ is required for benchmark task operations.

- Upgrade: `pipx upgrade kaggle` or `pip install --upgrade kaggle`
- Verify: `kaggle --version` (should show 2.0.0+)
- Suppress version warnings: use `kaggle -W` prefix for all commands
- Auth: `~/.kaggle/kaggle.json` must exist with valid credentials

## Kaggle Benchmark Environment Constraints

These are hard facts about the Kaggle benchmark notebook runtime:

- **No `git` installed** — cannot `git clone`. Use `urllib.request.urlretrieve` to download files from GitHub raw URLs instead.
- **No `matplotlib` pre-installed** — must `pip install -q matplotlib` before importing.
- **Python 3.11** (not 3.12+) — avoid 3.12+ syntax like `type` statements.
- **SDK location**: `/benchmarks/.venv/lib/python3.11/site-packages/kaggle_benchmarks/`
- **`papermill` runs the notebook** — first cell error stops execution entirely. Guard risky imports/installs.
- **Markdown cells must NOT have `outputs` key** — invalid nbformat, causes warnings. Only code cells should have `outputs`.

## Workflow

### 1. Resolve the notebook

- If `$ARGUMENTS` is provided, resolve the notebook path and optional slug
- If not provided, glob for `**/*.ipynb` (excluding `.venv/`, `node_modules/`, `.ipynb_checkpoints/`) and present the list
- Verify the file exists and is valid JSON (valid notebook format)

### 2. Compatibility checks

Read all code cells from the notebook and run these checks. Report results as a checklist (pass/fail for each). If any **required** check fails, stop and offer to fix it.

#### Required checks

- **Imports `kaggle_benchmarks`**: At least one cell contains `import kaggle_benchmarks` or `import kaggle_benchmarks as kbench`
- **Defines at least one task**: Uses `@kbench.task(` or `@kaggle_benchmarks.task(` decorator
- **Uses `kbench.llm` (singular)**: Task evaluation uses `kbench.llm` as the default model placeholder (not only `kbench.llms[...]`). This is required so Kaggle can auto-swap models via the "Add Models" UI.
- **No SDK installation commands**: Must NOT contain `pip install kaggle-benchmarks` or `git clone.*kaggle-benchmarks` — the SDK is pre-installed on Benchmark Task notebooks. Installing it separately causes version conflicts (e.g., protobuf mismatch).
- **Task functions have `llm` as first parameter**: Every `@kbench.task` decorated function must accept `llm` as its first parameter.
- **Task functions have return type annotation**: Each task function should have a return type annotation (e.g., `-> tuple[int, int]`, `-> bool`, `-> float`, `-> None`). Missing annotations default to Pass/Fail which may not be intended.
- **No `git clone` or `git` subprocess calls**: `git` is not installed on the Kaggle benchmark runtime. Any `git clone`, `subprocess.run(["git"`, or `!git` commands will fail. Replace with `urllib.request.urlretrieve` fetching from GitHub raw URLs.
- **No bare `import matplotlib`**: If matplotlib is used, there must be a `pip install -q matplotlib` before the import (in the same or earlier cell).
- **Markdown cells have no `outputs` key**: Parse the notebook JSON and check that cells with `"cell_type": "markdown"` do not have an `"outputs"` key. This is invalid nbformat and causes papermill warnings.

#### Recommended checks (warn but don't block)

- **Has `description` in `@kbench.task()`**: Task decorators should include a `description=` parameter for the leaderboard.
- **Uses `evaluate()` or `run()`**: At least one task should be executed via `.evaluate()` or `.run()`.
- **No hardcoded model names in evaluate()**: `evaluate(llm=...)` should use `[kbench.llm]` rather than `[kbench.llms["specific/model"]]` for the primary run. Hardcoded models are fine for comparison/debugging cells but shouldn't be the only execution path.
- **No `%%time` magic on evaluation cells**: `%%time` can interfere with error propagation in papermill execution on Kaggle.
- **Result tuple handling**: If task return type is `tuple[int, int]`, warn that the `result` column in `runs.as_dataframe()` will contain tuples. Must convert to ratio before aggregation:
  ```python
  df["accuracy"] = df["result"].apply(lambda r: r[0]/r[1] if isinstance(r, tuple) else float(r))
  ```

### 3. Ensure the repo is public and code is pushed

If the notebook references the current repo (GitHub URL, raw download, etc.):

- Detect the GitHub remote URL from `git remote -v`
- Check repo visibility using `gh repo view --json visibility`
- If private, ask the user for confirmation, then make it public with `gh repo edit --visibility public --accept-visibility-change-consequences`
- If no remote, warn the user that the notebook may not work on Kaggle without a public repo

Then ensure everything is committed and pushed:

- Check `git status` for uncommitted changes to the notebook or any files it depends on (e.g., `src/`, `data/`)
- If there are uncommitted changes, commit and push them
- Verify the push succeeded

### 4. Push to benchmark task

This is the preferred method. You CAN push code directly to an existing benchmark task using `kaggle kernels push` with the benchmark task's slug. The notebook runs with LLM proxy access.

**Procedure:**

1. Check if the `kaggle` CLI is installed and configured (`~/.kaggle/kaggle.json` exists)
2. If not installed or outdated, run `pipx upgrade kaggle` or `pip install --upgrade kaggle` to get v2.0+
3. If no slug was provided, search for existing benchmark tasks:
   ```bash
   kaggle -W kernels list --mine --page-size 20
   ```
   Look for slugs containing "benchmark-task" or matching the project name. If multiple found, ask user which one. If none found, proceed to step 5.
4. Pull the existing task to get its `kernel-metadata.json`:
   ```bash
   kaggle -W kernels pull <slug> -p /tmp/kaggle-task-pull
   ```
5. Copy the local notebook file over the pulled notebook file (replacing it):
   ```bash
   cp <local-notebook-path> /tmp/kaggle-task-pull/<pulled-notebook-filename>
   ```
6. Push the updated notebook back:
   ```bash
   kaggle -W kernels push -p /tmp/kaggle-task-pull
   ```
7. If the push succeeds, proceed to step 6 (monitor and debug).
8. **If push fails with "Notebook not found"**: The benchmark task exists but hasn't been **saved/published** yet in the UI. A newly created benchmark task (via `kaggle.com/benchmarks/tasks/new`) must be saved at least once through the UI before CLI push works. Instruct the user to:
   - Open the benchmark task in the Kaggle editor
   - Import the notebook (File → Import Notebook → GitHub)
   - Click **"Save Version"** (top right) to publish it
   - After that first save, `kaggle kernels push` will work for all subsequent updates

If no existing benchmark task slug is available, proceed to step 5 to create one.

### 5. Create a new benchmark task (if needed)

Creating a benchmark task MUST be done via the Kaggle UI. There is no CLI command for this.

```
======================================================================
  Create New Benchmark Task
======================================================================

  1. Open https://www.kaggle.com/benchmarks/tasks/new
     -> This creates a new notebook with the SDK + LLM proxy

  2. In the new benchmark notebook:
     File -> Import Notebook -> GitHub tab
     -> Type the repo name in the search box: <owner>/<repo>
     -> Select: <path-to-notebook>
     -> Click Import

     NOTE: You must type the repo name in the search box
     (e.g., "42euge/attention-bench"), then select the notebook
     file from the results. Check "Private repositories" if needed.

  3. After import, verify the right sidebar still shows
     "Benchmark Task". If it was reset, go to:
     File -> Set as Benchmark Task

  4. Click "Run All" to execute and verify it works.

  5. Click "Save Task" (top right) to publish to the leaderboard.

  6. After saving, find the task slug via:
     kaggle -W kernels list --mine --page-size 20

     Then future updates can be pushed directly via CLI (step 4).

======================================================================
```

Provide direct URLs for reference:
- GitHub: `https://github.com/<owner>/<repo>/blob/main/<path-to-notebook>`
- Raw: `https://raw.githubusercontent.com/<owner>/<repo>/main/<path-to-notebook>`

### 6. Monitor, debug, and retrieve results

After pushing a notebook (step 4), monitor its execution. Poll status every 30-60 seconds until complete or error.

```bash
# Check status (will be: queued -> running -> complete/error)
kaggle -W kernels status <slug>

# Once complete or error, pull the output:
rm -rf /tmp/kaggle-output && kaggle -W kernels output <slug> -p /tmp/kaggle-output
```

**Parse the log file** — the output directory contains a JSON log file (`*.log`) with stdout/stderr entries and timestamps:

```python
import json
with open('/tmp/kaggle-output/<slug>.log') as f:
    logs = json.load(f)
for entry in logs:
    d = entry['data'].rstrip()
    if d:
        print(f"[{entry['time']:.1f}s {entry['stream_name']}] {d}")
```

**Retrieve output files** — the output directory also contains any files the notebook saved (e.g., generated datasets, result JSON files, plots). List them with `ls /tmp/kaggle-output/` and read/copy as needed.

**Common error patterns and fixes:**

| Error | Cause | Fix |
|---|---|---|
| `FileNotFoundError: 'git'` | `git` not installed in runtime | Replace `git clone` with `urllib.request.urlretrieve` from raw GitHub URLs |
| `ModuleNotFoundError: 'matplotlib'` | Not pre-installed | Add `pip install -q matplotlib` before import |
| `TypeError: float() argument must be... not 'tuple'` | `result` column has `(correct, total)` tuples | Add `df["accuracy"] = df["result"].apply(lambda r: r[0]/r[1])` |
| `PapermillExecutionError` in cell N | First error stops notebook | Fix the failing cell; all subsequent cells are skipped |
| `nbformat` warnings about `outputs` in markdown | Invalid notebook structure | Remove `outputs` key from markdown cells in notebook JSON |
| `VersionError: Detected incompatible Protobuf` | SDK was pip-installed on top of pre-installed | Remove any `pip install kaggle-benchmarks` from notebook |
| `AttributeError: module 'kaggle_benchmarks' has no attribute 'llms'` | Not running in benchmark task notebook | Must push to a benchmark task slug, not a regular kernel |
| `Kernel push error: Notebook not found` | Benchmark task created but never saved/published in UI | User must save the task once via the Kaggle UI ("Save Version") before CLI push works |
| `TypeError: '<' not supported between instances of 'OpenAI' and 'OpenAI'` | Model column contains LLM objects, not strings | Add `model_name` string column: `df["model_name"] = df["llm"].apply(lambda x: str(x))` or use an `id()`→name lookup dict |
| Reasoning model (R1, Qwen-thinking) scores near 0% | `<think>...</think>` blocks parsed as answers | Add `strip_thinking()` that splits on `</think>` and takes the part after |
| Reasoning model preamble shifts answers | Lines like "Here are the answers:" counted as answer #1 | Parser should require `^\d+[\.\)\:\-]` prefix; skip non-numbered lines |

### Parser requirements for robust answer extraction

The `parse_numbered_answers` function must handle these model behaviors:
1. **Thinking models**: Strip `<think>...</think>` blocks before parsing
2. **Preamble lines**: Skip lines like "Here are the answers:" — only accept lines starting with `^\d+[\.\)\:\-]`
3. **Fallback**: If no numbered lines found, fall back to all non-empty lines
4. **Markdown formatting**: Some models use `1. **answer**` or `1. answer  ` with trailing whitespace

If there is an error, fix the notebook locally, re-push (repeat step 4), and monitor again. Continue this loop until the notebook completes successfully.

### 7. Log results to the journal

After a successful run (or informative failure), log the results via `geno-notes`:

```bash
geno-notes note "<summary>" --kind milestone --task <task-id-if-linked>
```

Use `--kind milestone` for a completed run, `--kind bug` for an error worth remembering. The entry lands in the active scope's `journal/YYYY/YYYY-MM.{md,jsonl}` with seconds-precision timestamp. Scope auto-resolves (project if `./geno/geno-notes/` exists, else global).

The message body should capture:
- Task slug, version number, status (complete/error), runtime
- If complete: key metrics (accuracy tables, attention thresholds, model comparison)
- If error: error type and what was fixed
- Available models (what `kbench.llms.keys()` returned)
- Paths to any retrieved output files

Example:
```bash
geno-notes note "Kaggle Benchmark v4 — COMPLETE. Task <your-kaggle-username>/new-benchmark-task-0def0. Models: gemini-2.5-flash, gemini-2.5-pro, claude-sonnet-4. SIN: adversarial 10:1, related 25:1, unrelated 25:1. Vigilance: 99-100%. Output → /tmp/kaggle-output/" --kind milestone
```

For multi-line context or code blocks, quote-escape carefully or use a heredoc:

```bash
geno-notes note "$(cat <<'EOF'
Kaggle Benchmark v4 — COMPLETE
Task: <your-kaggle-username>/new-benchmark-task-0def0
Models: gemini-2.5-flash, gemini-2.5-pro
SIN Results: adversarial 10:1, related 25:1, unrelated 25:1
Output → /tmp/kaggle-output/
EOF
)" --kind milestone
```

### 8. Multi-model evaluation

"Add Models" in the Kaggle UI is for manually scheduling runs across models. There is no CLI equivalent.

To run multiple models programmatically from within the notebook:

```python
# Run all available models
llms = [kbench.llms[m] for m in kbench.llms]
runs = task.evaluate(llm=llms, evaluation_data=df, n_jobs=2)

# Or specific models
models = ["gemini-2.5-flash-preview-05-20", "gemini-2.5-pro-preview-05-06"]
llms = [kbench.llms[m] for m in models]
runs = task.evaluate(llm=llms, evaluation_data=df, n_jobs=2)
```

The primary evaluation path should still use `kbench.llm` (singular) so the platform can auto-swap via UI. Multi-model is for explicit comparison runs.

### 9. Orthogonal model selection

When running multi-model evaluations, avoid testing near-duplicate models. Pick an orthogonal set that maximizes information per compute:

**Selection criteria:**
- One model per capability tier (don't test opus-4-1, 4-5, AND 4-6 — pick the latest)
- One model per family (don't test all Gemini variants — pick representative ones)
- Include a scaling ladder if available (e.g., gemma-3-1b → 4b → 12b → 27b)
- Include at least one reasoning/thinking model (deepseek-r1, qwen-thinking)
- Include budget and frontier from different providers

**Example orthogonal set (~10 min runtime):**
```python
ORTHOGONAL_MODELS = [
    "google/gemma-3-1b",          # Floor
    "google/gemma-3-4b",          # Scaling
    "google/gemma-3-12b",         # Scaling
    "google/gemma-3-27b",         # Scaling ceiling
    "anthropic/claude-haiku-4-5@20251001",  # Budget frontier
    "deepseek-ai/deepseek-r1-0528",        # Reasoning
    "google/gemini-2.5-flash",              # Mid-tier
    "anthropic/claude-opus-4-6@default",    # Top frontier
]
```

### 10. Version numbers and concurrent runs

The benchmark task version number increments on each `kaggle kernels push`, regardless of which notebook pushes. If multiple benchmarks are being developed simultaneously and push to different slugs, each has its own version counter. If pushing to the SAME slug from different places, versions will increment non-sequentially. This is cosmetic — the slug is the stable identifier.

### 11. Saving results

Always save results locally after a run:
```bash
mkdir -p results/<run_label>
cp /tmp/kaggle-output/*.log results/<run_label>/raw_log.json
cp /tmp/kaggle-output/*.run.json results/<run_label>/
cp /tmp/kaggle-output/*.png results/<run_label>/
```

The `.run.json` files contain full conversations (prompts + responses), token counts, latencies, and results — invaluable for debugging and analysis.

### 12. Downloading the executed notebook

- **`kaggle kernels pull <slug>`** downloads **source code only** — no cell outputs.
- **The web UI "Download .ipynb" button** downloads the **executed notebook with cell outputs** (plots, printed results, etc.).
- Direct link to the rendered notebook: `https://www.kaggle.com/code/<owner>/<slug>`
- After a run, always provide this link so the user can view the notebook with outputs in-browser or download via the UI.
- There is no CLI equivalent for downloading the executed notebook with outputs as of Kaggle CLI v2.0.

## Important reminders to always display

- **Benchmark Task notebooks != regular Kaggle notebooks.** Benchmark notebooks have the SDK pre-installed and access to the LLM Model Proxy. Regular notebooks pushed via `kaggle kernels push` to your own slug do NOT have LLM proxy access.
- **Direct push to benchmark task slug DOES work** — `kaggle kernels push` with the benchmark task's slug gives full LLM proxy access. This is the preferred update method after initial creation.
- **`kbench.llm` placeholder is required** so the platform can schedule runs across models via the "Add Models" UI.
- **Do NOT install the SDK** in the notebook (`pip install kaggle-benchmarks`). It is pre-installed on benchmark notebooks and installing separately causes protobuf version conflicts.
- **No `git` in runtime** — use `urllib.request.urlretrieve` for file downloads from GitHub raw URLs.
- Available models can be listed with `kbench.llms.keys()` but the primary evaluation should use `kbench.llm`.

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-run-kaggle-bench \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = notebook pushed, executed on Kaggle without errors, results retrieved and saved to results/
- `failure` = compatibility checks failed, push rejected, or Kaggle execution errored after all fix attempts
- `abandoned` = user stopped early

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-notes`

- **Error recovery section** — LLMs can get stuck in retry loops or abandon tasks on first failure. Explicit fallback steps prevent both.
- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-kaggle](index.md)
