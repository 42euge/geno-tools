---
title: geno-kaggle
description: Kaggle benchmarking, notebook upload, discussion scraping
---

# geno-kaggle

Kaggle benchmarking, notebook upload, discussion scraping

[:material-github: GitHub](https://github.com/42euge/geno-kaggle){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-create-benchmark-kaggle](#geno-create-benchmark-kaggle) | `/geno-create-benchmark-kaggle` | "Create Kaggle Benchmark Notebook" |
| [geno-kaggle-benchmarks-task-generate](#geno-kaggle-benchmarks-task-generate) | `/geno-kaggle-benchmarks-task-generate` | "Generate Kaggle Benchmark Task Structure" |
| [geno-kaggle-benchmarks-task-review](#geno-kaggle-benchmarks-task-review) | `/geno-kaggle-benchmarks-task-review` | "Review Kaggle Benchmark Task Results" |
| [geno-kaggle-discussion](#geno-kaggle-discussion) | `/geno-kaggle-discussion` | "Kaggle Discussion Scraper" |
| [geno-run-kaggle-bench](#geno-run-kaggle-bench) | `/geno-run-kaggle-bench` | "Run Kaggle Benchmark" |
| [geno-upload-kaggle](#geno-upload-kaggle) | `/geno-upload-kaggle` | "Upload Notebook to Kaggle" |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-kaggle
    
    Kaggle benchmarking skills for AI coding agents. Provides workflows for creating, deploying,
    running, and reviewing benchmark tasks on the Kaggle platform.
    
    ## Skills
    
    | Skill | Description |
    |-------|-------------|
    | `/geno-create-benchmark-kaggle <desc>` | Create a self-contained benchmark notebook for Kaggle |
    | `/geno-kaggle-benchmarks-task-generate <name>` | Scaffold a new benchmark task folder structure |
    | `/geno-kaggle-benchmarks-task-review <task>` | Pull and review results from a Kaggle benchmark run |
    | `/geno-run-kaggle-bench <notebook>` | Push, run, monitor, and debug a notebook on Kaggle |
    | `/geno-upload-kaggle <notebook>` | Upload a notebook to Kaggle |
    | `/geno-kaggle-discussion` | Scrape competition discussions and generate insights |

## geno-create-benchmark-kaggle

**Slash command:** `/geno-create-benchmark-kaggle`

> "Create Kaggle Benchmark Notebook"

??? info "Observability"

    success_signal: "Valid .ipynb notebook created, passes all 10 validation checks, and next-step instructions printed" failure_signals: - "Generated notebook fails JSON validation or nbformat checks" - "Missing required elements (no @kbench.task, no kbench.llm usage, no llm parameter)" - "Output path not writable or parent directory does not exist" knowledge_reads: - "User-provided benchmark specification (track, cognitive ability, task design)" - "Kaggle Benchmark environment constraints" knowledge_writes: - "Generated .ipynb notebook file at specified output path"

??? example "Full skill definition (Level 4)"

    Generate a self-contained Jupyter notebook (.ipynb) for a Kaggle Benchmark task that can be uploaded and run against multiple models via the Kaggle UI.
    
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

## geno-kaggle-benchmarks-task-generate

**Slash command:** `/geno-kaggle-benchmarks-task-generate`

> "Generate Kaggle Benchmark Task Structure"

??? info "Observability"

    success_signal: "tasks/<task_name>/ directory created with .ipynb notebook, docs/, results/, and review/ subdirectories" failure_signals: - "Task name validation fails (not snake_case)" - "tasks/ directory does not exist or is not writable" - "Generated notebook is invalid JSON or missing required cells" knowledge_reads: - "User-provided task name and description" - "CLAUDE.md for notebook conventions" knowledge_writes: - "tasks/<task_name>/<task_name>.ipynb (benchmark notebook template)" - "tasks/<task_name>/docs/<task_name>.md (task documentation)" - "tasks/<task_name>/results/.gitkeep" - "tasks/<task_name>/review/.gitkeep"

??? example "Full skill definition (Level 4)"

    Scaffold a new benchmark task with the standard folder structure and notebook template.
    
    ## Input
    
    `$ARGUMENTS` — Task name in snake_case (e.g., `selective_attention`). Optional — if not provided, ask the user for a name and brief description of what the task tests.
    
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

## geno-kaggle-benchmarks-task-review

**Slash command:** `/geno-kaggle-benchmarks-task-review`

> "Review Kaggle Benchmark Task Results"

??? info "Observability"

    success_signal: "Review markdown written to tasks/<task_name>/review/review_<date>.md and summary printed" failure_signals: - "Kaggle kernel pull fails (slug not found, auth error)" - "Version mismatch between local and Kaggle notebook timestamps" - "Pulled notebook has no cell outputs (run did not complete)" knowledge_reads: - "~/.kaggle/kaggle.json (API credentials)" - "tasks/<task_name>/*.ipynb (local notebook for version comparison)" - "Pulled notebook cell outputs from Kaggle" knowledge_writes: - "tasks/<task_name>/results/latest_run.md (raw extracted outputs)" - "tasks/<task_name>/review/review_<date>.md (analysis and recommendations)"

??? example "Full skill definition (Level 4)"

    Pull the latest run from Kaggle for a benchmark task, verify it matches the last pushed version, analyze the results, and write a review.
    
    ## Input
    
    `$ARGUMENTS` — Task name (e.g., `change_blindness`). Must match a folder under `tasks/`.
    
    If no arguments provided, list available tasks in `tasks/` and ask the user which one to review.
    
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

## geno-kaggle-discussion

**Slash command:** `/geno-kaggle-discussion`

> "Kaggle Discussion Scraper"

??? info "Observability"

    success_signal: "index.yaml and per-track insight markdown files generated under competition-info/kaggle-discussions/" failure_signals: - "Kaggle Search API returns auth error or empty results" - "WebFetch fails on discussion thread URLs (rate-limited or 404)" - "YAML serialization error when saving thread files" knowledge_reads: - "~/.kaggle/kaggle.json (API credentials)" - "Existing thread YAML files for incremental update comparison" knowledge_writes: - "competition-info/kaggle-discussions/threads/*.yaml (per-thread data)" - "competition-info/kaggle-discussions/index.yaml (master index)" - "competition-info/kaggle-discussions/insights/*.md (per-track insight summaries)"

??? example "Full skill definition (Level 4)"

    Scrape all discussion threads from the kaggle-measuring-agi competition, save each thread as a YAML file with its comments, and generate per-track insight summaries.
    
    ## Input
    
    `$ARGUMENTS` — Optional. Can be:
    - (empty) — scrape all discussions and generate insights
    - `scrape` — only scrape discussions, skip insight generation
    - `insights` — only regenerate insights from existing YAML files
    - A track name (e.g., `learning`, `metacognition`) — regenerate insights for one track
    
    ## Output Location
    
    All output goes under:
    ```
    competition-info/kaggle-discussions/
    ├── threads/                          # Individual thread YAML files
    │   ├── 682012-welcome-to-measuring-progress.yaml
    │   ├── 681731-kaggle-benchmarks-product-feedback.yaml
    │   └── ...
    ├── index.yaml                        # Master index of all threads
    └── insights/                         # Per-track insight summaries
        ├── learning.md
        ├── metacognition.md
        ├── attention.md
        ├── executive-functions.md
        ├── social-cognition.md
        └── general.md                    # Cross-track / competition-wide insights
    ```
    
    ## Workflow
    
    ### Step 1: Scrape all discussion topics
    
    Use the Kaggle Search API to fetch all discussion topics for the competition:
    
    ```python
    import requests, json
    
    with open(os.path.expanduser('~/.kaggle/kaggle.json')) as f:
        creds = json.load(f)
    
    session = requests.Session()
    session.auth = (creds['username'], creds['key'])
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'kaggle-api/v1.7.0'
    })
    
    # Fetch topics (DocumentType.TOPIC = 8)
    all_topics = []
    page_token = ''
    while True:
        payload = {
            'filters': {
                'documentTypes': [8],
                'discussionFilters': {'sourceType': 1},  # COMPETITION
                'query': 'kaggle-measuring-agi',
            },
            'pageSize': 50,
        }
        if page_token:
            payload['pageToken'] = page_token
    
        resp = session.post(
            'https://api.kaggle.com/v1/search.SearchApiService/ListEntities',
            json=payload
        )
        data = resp.json()
        docs = data.get('documents', [])
        all_topics.extend(docs)
        page_token = data.get('nextPageToken', '')
        if not page_token or not docs:
            break
    ```
    
    ### Step 2: Scrape all comments
    
    Fetch all comments using the same API with DocumentType.COMMENT = 6:
    
    ```python
    all_comments = []
    page_token = ''
    while True:
        payload = {
            'filters': {
                'documentTypes': [6],
                'discussionFilters': {'sourceType': 1},
                'query': 'kaggle-measuring-agi',
            },
            'pageSize': 50,
        }
        if page_token:
            payload['pageToken'] = page_token
    
        resp = session.post(
            'https://api.kaggle.com/v1/search.SearchApiService/ListEntities',
            json=payload
        )
        data = resp.json()
        docs = data.get('documents', [])
        all_comments.extend(docs)
        page_token = data.get('nextPageToken', '')
        if not page_token or not docs:
            break
    ```
    
    ### Step 3: For each topic, fetch its full thread via WebFetch
    
    The Search API may not return all comments. For each topic, also fetch the full thread page to capture any missing comments:
    
    ```
    https://www.kaggle.com/competitions/kaggle-measuring-agi/discussion/{topic_id}
    ```
    
    Use `WebFetch` on each discussion URL with a prompt to extract ALL comments including author, date, content, and votes. Merge with API comments (deduplicate by comment ID from `newCommentUrl`).
    
    ### Step 4: Group comments by topic
    
    Each comment's `discussionDocument.newCommentUrl` contains the parent topic ID:
    ```
    /competitions/kaggle-measuring-agi/discussion/{topic_id}#{comment_id}
    ```
    
    Extract the topic_id from the URL path and group comments under their parent topic.
    
    ### Step 5: Save each thread as YAML
    
    For each topic, create a YAML file named `{topic_id}-{slugified-title}.yaml`:
    
    ```yaml
    id: 682012
    title: "Welcome to Measuring Progress Toward AGI - Cognitive Abilities"
    url: "https://www.kaggle.com/competitions/kaggle-measuring-agi/discussion/682012"
    author:
      username: "nicholaskanggoog"
      display_name: "Nicholas Kang"
      tier: "STAFF"
    created: "2026-03-17T20:33:36Z"
    updated: "2026-03-25T15:50:38Z"
    votes: 12
    tags: []  # inferred track tags, e.g. [metacognition, attention]
    
    post:
      markdown: |
        Hi team,
    
        I'm Nick, Product Manager for Kaggle Benchmarks...
      stripped: "Hi team, I'm Nick..."
    
    comments:
      - id: 3422608
        author:
          username: "someuser"
          display_name: "Some User"
          tier: "CONTRIBUTOR"
        created: "2026-03-18T10:00:00Z"
        votes: 2
        markdown: |
          Great initiative! Looking forward to this.
        stripped: "Great initiative! Looking forward to this."
      - id: 3422700
        # ... more comments
    ```
    
    ### Step 6: Auto-tag threads by track
    
    Classify each thread into one or more tracks based on title and content analysis:
    
    - **learning** — mentions learning, knowledge acquisition, few-shot, in-context learning, training data
    - **metacognition** — mentions metacognition, calibration, confidence, self-awareness, knowing what it knows
    - **attention** — mentions attention, focus, distraction, selective attention, filtering
    - **executive-functions** — mentions planning, inhibition, cognitive flexibility, task switching, working memory
    - **social-cognition** — mentions social cognition, theory of mind, empathy, social situations, perspective-taking
    - **general** — competition logistics, SDK issues, getting started, feedback, rules
    
    A thread can have multiple tags. Include the tags in both the YAML file and the index.
    
    ### Step 7: Build the master index
    
    Create `index.yaml` with a summary of all threads:
    
    ```yaml
    scraped_at: "2026-03-25T12:00:00Z"
    competition: "kaggle-measuring-agi"
    total_threads: 25
    total_comments: 42
    
    threads:
      - id: 682012
        title: "Welcome to Measuring Progress Toward AGI - Cognitive Abilities"
        author: "nicholaskanggoog"
        created: "2026-03-17T20:33:36Z"
        votes: 12
        comment_count: 7
        tags: [general]
        file: "682012-welcome-to-measuring-progress.yaml"
      # ... sorted by votes descending
    
    by_track:
      learning:
        thread_count: 3
        threads: [681993, ...]
      metacognition:
        thread_count: 5
        threads: [682752, 682023, ...]
      attention:
        thread_count: 2
        threads: [683736, ...]
      executive-functions:
        thread_count: 2
        threads: [683411, ...]
      social-cognition:
        thread_count: 2
        threads: [684117, ...]
      general:
        thread_count: 15
        threads: [682012, 681731, ...]
    ```
    
    ### Step 8: Generate per-track insights
    
    For each track, read all threads tagged with that track and generate an insight summary as a markdown file. Each insight file should include:
    
    ```markdown
    # {Track Name} — Discussion Insights
    
    *Generated: 2026-03-25 | Threads analyzed: N | Comments analyzed: N*
    
    ## Key Themes
    
    1. **Theme name** — Brief description of the recurring theme
       - Supporting evidence from threads [link to thread YAML]
    
    ## Notable Benchmarks Shared
    
    | Benchmark | Author | Key Finding | Thread |
    |-----------|--------|-------------|--------|
    | META-COG  | user   | AI scores 8.33% on self-awareness | 682752 |
    
    ## Community Concerns & Feedback
    
    - Bullet points of concerns raised and any resolutions
    
    ## Ideas & Opportunities
    
    - Ideas from discussions that could inform benchmark design
    
    ## Organizer Announcements
    
    - Official announcements and clarifications relevant to this track
    
    ## Open Questions
    
    - Unresolved questions from the community
    ```
    
    For the `general.md` file, focus on:
    - Competition logistics and rule changes
    - SDK/platform issues and workarounds
    - Cross-track observations
    - Community sentiment and participation trends
    
    ### Step 9: Report results
    
    Print a summary:
    - Total threads scraped
    - Total comments captured
    - Threads per track
    - Any threads that failed to scrape (with error details)
    - Path to the output directory
    
    ## Important Notes
    
    - **API endpoint**: `https://api.kaggle.com/v1/search.SearchApiService/ListEntities` (POST)
    - **Auth**: Basic auth from `~/.kaggle/kaggle.json` (username + key)
    - **Rate limiting**: Add a 1-second delay between WebFetch calls to avoid rate limiting
    - **Idempotent**: If thread YAML files already exist, compare and update only if content has changed. Log which threads were new/updated/unchanged.
    - **Comment ordering**: Sort comments by `created` timestamp (ascending) within each thread
    - **YAML formatting**: Use block scalars (`|`) for markdown content to preserve formatting
    - **Track classification**: Use the thread's title + post markdown + comment content for classification. Weight the title most heavily.
    - **Parallel fetching**: Use up to 3 parallel Agents for WebFetch calls to speed up scraping, but respect rate limits.
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-kaggle-discussion \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = index.yaml written and at least one insight markdown generated
    - `failure` = API scrape returned no threads, or YAML/insight generation failed
    - `abandoned` = user stopped early

## geno-run-kaggle-bench

**Slash command:** `/geno-run-kaggle-bench`

> "Run Kaggle Benchmark"

??? info "Observability"

    success_signal: "Notebook pushed, executed on Kaggle, results retrieved to /tmp/kaggle-output/ and saved to results/" failure_signals: - "Compatibility checks fail (missing SDK import, git clone in notebook, etc.)" - "kaggle kernels push fails (slug not found, auth error, never saved in UI)" - "Notebook execution errors on Kaggle (PapermillExecutionError, protobuf conflict)" knowledge_reads: - "~/.kaggle/kaggle.json (API credentials)" - "Target .ipynb notebook file" - "Git remote URL and repo visibility" - "Kaggle kernel status and output logs" knowledge_writes: - "results/<run_label>/ (raw logs, .run.json, plots)" - "geno-notes journal entry (milestone or bug)" - "Git commits (if uncommitted changes are staged and pushed)"

??? example "Full skill definition (Level 4)"

    Validate, push, run, monitor, and debug a Jupyter notebook on the Kaggle Benchmarks platform. Retrieves results and logs progress to lab notes.
    
    ## Input
    
    `$ARGUMENTS` — Path to the `.ipynb` file to run, optionally followed by a benchmark task slug.
    
    Examples:
    - `notebooks/kaggle_benchmark.ipynb` — push and run, auto-detect or ask for task slug
    - `notebooks/kaggle_benchmark.ipynb <your-kaggle-username>/new-benchmark-task-0def0` — push to specific task
    - (empty) — search for `.ipynb` files and present options
    
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

## geno-upload-kaggle

**Slash command:** `/geno-upload-kaggle`

> "Upload Notebook to Kaggle"

??? info "Observability"

    success_signal: "Notebook uploaded to Kaggle via API push or manual instructions provided with valid GitHub URL" failure_signals: - "Notebook file not found or invalid JSON" - "kaggle kernels push fails (auth error, metadata error)" - "Repo cannot be made public and notebook references it" knowledge_reads: - "~/.kaggle/kaggle.json (API credentials)" - "Target .ipynb notebook file" - "Git remote URL and repo visibility" knowledge_writes: - "kernel-metadata.json (Kaggle kernel metadata for API push)" - "Git commits (if uncommitted notebook changes are staged)"

??? example "Full skill definition (Level 4)"

    Prepare and upload a Jupyter notebook to Kaggle for running with the kaggle-benchmarks SDK.
    
    ## Input
    
    `$ARGUMENTS` — Path to the `.ipynb` file to upload. Can be absolute or relative to the current working directory.
    
    If no arguments provided, search for `.ipynb` files in the current project and ask the user which one to upload.
    
    ## Workflow
    
    ### 1. Resolve the notebook
    
    - If `$ARGUMENTS` is provided, resolve it to an absolute path
    - If not provided, glob for `**/*.ipynb` (excluding `.venv/`, `node_modules/`, `.ipynb_checkpoints/`) and prompt the user to select one
    - Verify the file exists and is valid JSON (valid notebook format)
    
    ### 2. Ensure the repo is public
    
    The notebook clones the repo on Kaggle, so it must be publicly accessible.
    
    - Detect the GitHub remote URL from `git remote -v`
    - Check repo visibility using `gh repo view --json visibility`
    - If private, ask the user for confirmation, then make it public with `gh repo edit --visibility public --accept-visibility-change-consequences`
    - If no remote, warn the user that the notebook may not work on Kaggle without a public repo
    
    ### 3. Ensure the notebook is committed and pushed
    
    - Check `git status` for uncommitted changes to the notebook or any files it depends on (e.g., `src/`, `data/`)
    - If there are uncommitted changes, commit and push them
    - Verify the push succeeded
    
    ### 4. Verify notebook setup cell
    
    Read the notebook and check whether its first code cell:
    - Handles cloning the repo (e.g., `!git clone` or `subprocess.run(["git", "clone", ...])`)
    - Adds `src/` to `sys.path`
    - Generates data if missing
    
    If the notebook doesn't handle setup, warn the user that it may not run on Kaggle without modifications.
    
    ### 5. Provide Kaggle instructions
    
    Print instructions for uploading to Kaggle:
    
    1. **New benchmark task:** Go to `https://www.kaggle.com/benchmarks/tasks/new`
    2. **New notebook:** Go to `https://www.kaggle.com/code/new` → File → Upload Notebook → select the `.ipynb` file
    3. **From GitHub (easiest):** The notebook can be imported directly from the public repo URL
    
    Also provide the direct GitHub raw URL for the notebook:
    `https://github.com/<owner>/<repo>/blob/main/<path-to-notebook>`
    
    ### 6. Optional: Upload via Kaggle API
    
    If the user has the Kaggle API configured (`~/.kaggle/kaggle.json` exists):
    
    - Ask if they want to push via the API using `kaggle kernels push`
    - If yes, create/update `kernel-metadata.json` in the notebook's directory:
      ```json
      {
        "id": "<username>/attention-bench",
        "title": "AttentionBench",
        "code_file": "<notebook-filename>",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": true,
        "enable_gpu": false,
        "enable_internet": true,
        "competition_sources": [],
        "dataset_sources": [],
        "kernel_sources": []
      }
      ```
    - Run `kaggle kernels push -p <notebook-directory>`
    - Report the kernel URL on success
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-upload-kaggle \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = notebook uploaded via API push or manual upload instructions provided with valid URLs
    - `failure` = notebook not found, invalid format, or kaggle kernels push failed
    - `abandoned` = user stopped early
