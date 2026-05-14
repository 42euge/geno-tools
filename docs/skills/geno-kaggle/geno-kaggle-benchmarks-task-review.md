---
title: geno-kaggle-benchmarks-task-review
description: "Review Kaggle Benchmark Task Results"
---

# geno-kaggle-benchmarks-task-review

`/geno-kaggle-benchmarks-task-review`

> "Review Kaggle Benchmark Task Results"

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Task name (e.g., `change_blindness`). Must match a folder under `tasks/`.

If no arguments provided, list available tasks in `tasks/` and ask the user which one to review.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Resolve the task

- If `$ARGUMENTS` is provided, verify `tasks/<task_name>/` exists and contains a `.ipynb` file
- If not provided, list directories under `tasks/` and ask the user which one to review

### 2. Pull the latest run from Kaggle

- Determine the Kaggle kernel slug. Check `kaggle kernels list --user` to find the matching kernel (the slug typically matches the task name with hyphens instead of underscores)
- Pull the notebook with outputs: `kaggle kernels pull <user>/<slug> -p /tmp/kaggle-review-<task_name>`
- If pull fails, tell the user the kernel wasn't found and suggest they check the Kaggle UI

### 3. Verify version matches

- Extract the `# Last updated: YYYY-MM-DD HH:MM UTC` timestamp from the first code cell of both the pulled notebook and the local notebook
- If timestamps match, proceed with review
- If timestamps differ, warn the user: "Kaggle run is from `<kaggle_timestamp>`, local is `<local_timestamp>`. Re-run on Kaggle after pulling the latest from GitHub."
- If no timestamp found in the pulled notebook, fall back to comparing the data generation cell and task definition cell code

### 4. Extract results

Parse all cell outputs from the pulled notebook:
- Find cells with output text containing results tables, accuracy numbers, error messages
- Extract any error tracebacks
- Note if any cells have no output (didn't run)
- Save raw extracted outputs to `tasks/<task_name>/results/latest_run.md`

### 5. Analyze and review

Write a review markdown file to `tasks/<task_name>/review/review_<date>.md` with:

```markdown
# <Task Name> — Review <YYYY-MM-DD>

## Run Status
- Kernel: <kaggle URL>
- Status: <success/error/partial>
- Local timestamp: <from local notebook>
- Kaggle timestamp: <from pulled notebook>
- Version match: <yes/no/warning>

## Results Summary
<Key metrics from the output — detection rates, accuracy tables, etc.>

## Assessment

### Does it work?
<Did the task run without errors? Did the scoring produce reasonable results?>

### Discriminatory power
<Is there a meaningful gradient? Do different conditions produce different scores?>

### What's good
<What aspects of the task design are working well?>

### What needs fixing
<Specific issues found — scoring too strict/loose, no disruptor effect, etc.>

## Recommended next steps
<Concrete action items>
```

### 6. Report to user

Print a summary of the review findings directly in the conversation, and tell the user where the review file was saved.

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-kaggle-benchmarks-task-review \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = review markdown written to tasks/<task_name>/review/ and summary printed
- `failure` = kernel pull failed, notebook had no outputs, or review generation failed
- `abandoned` = user stopped early

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-kaggle](index.md)
