---
title: geno-kaggle-benchmarks-task-generate
description: "Generate Kaggle Benchmark Task Structure"
---

# geno-kaggle-benchmarks-task-generate

`/geno-kaggle-benchmarks-task-generate`

> "Generate Kaggle Benchmark Task Structure"

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Task name in snake_case (e.g., `selective_attention`). Optional — if not provided, ask the user for a name and brief description of what the task tests.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Resolve task name

- If `$ARGUMENTS` is provided, use it as the task name
- If not provided, ask the user for the task name and a one-line description
- Validate: must be snake_case, no spaces, no hyphens

### 2. Create folder structure

Create the following under `tasks/`:

```
tasks/<task_name>/
├── <task_name>.ipynb    # The benchmark notebook
├── docs/
│   ├── .gitkeep
│   └── <task_name>.md   # Task documentation (what to expect)
├── results/
│   └── .gitkeep
└── review/
    └── .gitkeep
```

### 3. Generate the notebook

Create `tasks/<task_name>/<task_name>.ipynb` with this cell structure:

1. **Markdown: Title** — `# <Task Name>` with `> **Task name:** \`<Task Name>\`` and Track: Attention header
2. **Code: Setup** — must start with `# Last updated: YYYY-MM-DD HH:MM UTC` timestamp, then imports (kaggle_benchmarks, pandas, numpy, json, re, random) and print available models
3. **Code: Helpers** — `strip_thinking()` and any parsing helpers
4. **Code: Data generation** — placeholder with `random.seed()`, data list, and DataFrame creation
5. **Code: Dataset overview** — prints readable summary of the generated data
6. **Markdown: Task Definition**
7. **Code: Task** — `@kbench.task()` decorated function returning `bool` or `tuple[int, int]`
8. **Markdown: Run Evaluation**
9. **Code: Evaluate** — `.evaluate(llm=[kbench.llm], evaluation_data=df)` call
10. **Markdown: Results & Analysis**
11. **Code: Analysis** — summary statistics and metrics
12. **Code: Plot** — matplotlib visualization

Key requirements:
- Self-contained: all data generated inline with fixed seed
- `llm` must be passed as a list: `llm=[kbench.llm]`
- Include `strip_thinking()` for reasoning model compatibility
- No external dependencies or shared code

### 4. Generate the docs file

Create `tasks/<task_name>/docs/<task_name>.md` with sections:
- What it tests
- The setup (passage/stimulus structure)
- What to expect when you run it (expected output, what good results look like)
- Design (factorial structure, total items)

### 5. Report

Tell the user:
- What was created
- Next steps: fill in the data generation and task function, then push to GitHub and link from Kaggle

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-kaggle-benchmarks-task-generate \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = tasks/<task_name>/ directory created with notebook, docs, results, and review subdirectories
- `failure` = task name invalid, directory creation failed, or notebook template generation failed
- `abandoned` = user stopped early

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-kaggle](index.md)
