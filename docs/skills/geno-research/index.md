---
title: geno-research
description: Wiki-based research, paper generation, repo documentation
---

# geno-research

Wiki-based research, paper generation, repo documentation

[:material-github: GitHub](https://github.com/42euge/geno-research){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-research-paper-generate](#geno-research-paper-generate) | `/geno-research-paper-generate` | Generate an academic paper (workshop / extended abstract style) from the current repository's benchmark results, code... |
| [geno-research-papers-generate](#geno-research-papers-generate) | `/geno-research-papers-generate` | Generate an academic paper (workshop / extended abstract style) from research findings |
| [geno-research-repo-docs](#geno-research-repo-docs) | `/geno-research-repo-docs` | Generate purpose-driven repository documentation that captures what we're trying to achieve, the reasoning behind des... |
| [geno-research-repos-document](#geno-research-repos-document) | `/geno-research-repos-document` | Generate purpose-driven documentation for a repository |
| [geno-research-wiki](#geno-research-wiki) | `/geno-research-wiki` | Build and maintain a wiki of linked markdown notes using the LLM Wiki pattern |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-research
    
    Research toolkit with wiki, paper generation, and repo documentation.
    
    ## Sub-skills
    
    | Skill | Slash command | Purpose |
    |-------|---------------|---------|
    | geno-research-wiki | /geno-research-wiki | Research a topic and build a wiki |
    | geno-research-paper-generate | /geno-research-paper-generate | Generate a paper from wiki pages |
    | geno-research-repo-docs | /geno-research-repo-docs | Generate documentation for a repo |

## geno-research-paper-generate

**Slash command:** `/geno-research-paper-generate`

> Generate an academic paper (workshop / extended abstract style) from the current repository's benchmark results, code...

??? info "Observability"

    success_signal: "paper/paper.md generated with data-backed sections and results tables" failure_signals: - "no results directory found or result JSON files unreadable" - "paper generated with placeholder data instead of actual numbers" - "write to paper/ directory failed" knowledge_reads: - "src/ (generate.py, benchmark.py, analyze.py) for methodology" - "results/ (.run.json files) for actual benchmark numbers" - "notebooks/ (kaggle_benchmark.ipynb) for evaluation setup" - "geno-notes (tasks, journal, plans) for development context" - "research/ folders (up to 3 parent dirs) for theoretical grounding" - "CLAUDE.md, README.md for project context" - "git log for development trajectory" knowledge_writes: - "paper/paper.md (the generated paper)" - "paper/figures/*.md (figure descriptions)"

??? example "Full skill definition (Level 4)"

    Generate a short academic paper (workshop / extended abstract style) about findings from the current repository's benchmark. The paper synthesizes code, results, lab notes, and development history into a coherent research narrative.
    
    ## Input
    
    `$ARGUMENTS` — Optional instructions (e.g., "focus on adversarial noise findings", "target NeurIPS workshop format", "max 4 pages"). If empty, generate a complete paper covering all findings.
    
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
    - `geno-tools/docs/` — existing documentation
    - `CLAUDE.md` — project context and track description
    - `README.md` — project overview
    
    **Research context:**
    - Walk up to 3 parent directories looking for `research/` folders
    - Check for `../../research/attention/` and `../../research/concepts/` (paths from CLAUDE.md)
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
    
    Write `paper/paper.md` following this structure:
    
    ```markdown
    # [Paper Title]
    [Short, specific, informative — not generic. Capture the key finding.]
    
    ## Abstract
    [150-250 words. State the problem, method, key finding, and implication.
    The abstract should make someone want to read the paper.]
    
    ## 1. Introduction
    [Motivate the problem: why does LLM attention matter? What's missing from current benchmarks?
    State the research question clearly. Preview the key finding.
    Cite relevant prior work if found in research notes.
    End with a paragraph summarizing contributions.]
    
    ## 2. Benchmark Design
    
    ### 2.1 Signal-in-Noise Titration (Selective Attention)
    [Describe the task: passages, questions, noise types, noise ratios.
    Explain WHY each design choice was made (not just what).
    Include the interleaving strategy and its rationale.
    Describe the three noise types and their purpose.]
    
    ### 2.2 Vigilance Decrement (Sustained Attention)
    [Describe the task: repeated subtasks, oddball variant.
    Explain what each measures and why it complements SIN.]
    
    ### 2.3 Dataset Construction
    [How data was generated. Contamination resistance.
    Key statistics: N items, noise ratio range, prompt sizes.
    Answer verification method.]
    
    ### 2.4 Evaluation Setup
    [Models tested (with rationale for selection).
    Kaggle Benchmarks platform. Runtime constraints.
    Any preprocessing (think-tag stripping, preamble handling).]
    
    ## 3. Results
    
    ### 3.1 Signal-in-Noise Results
    [Main accuracy table: model x noise_type x noise_ratio.
    Threshold table: the noise ratio where each model drops below 80%.
    Key observation: adversarial noise as the sole discriminator.
    The Gemma scaling ladder finding.]
    
    ### 3.2 Vigilance Results
    [Accuracy by model x task_type.
    Oddball detection results.
    Notable anomalies and their explanations.]
    
    ### 3.3 Cross-Dimensional Analysis
    [How selective and sustained attention correlate.
    Do models that handle noise well also maintain vigilance?]
    
    ## 4. Discussion
    
    ### 4.1 Adversarial Noise as Cognitive Discriminator
    [This is the paper's key insight. Develop it fully.
    Why does adversarial noise separate models when other noise types don't?
    What does this tell us about how LLMs process context?]
    
    ### 4.2 Scaling Laws for Attention
    [The Gemma 1b->4b->12b->27b progression.
    Does attention scale predictably with model size?]
    
    ### 4.3 Reasoning Models and Attention
    [DeepSeek R1's behavior: chain-of-thought doesn't prevent adversarial distraction.
    The preamble parsing discovery.]
    
    ### 4.4 Limitations
    [Ceiling effect at frontier. Small sample sizes.
    Vigilance task ambiguity (misspelling interpretation).
    Platform constraints. What we'd do differently.]
    
    ## 5. Related Work
    [Position relative to existing benchmarks (RULER, Needle-in-a-Haystack, etc.).
    How this differs from long-context benchmarks.
    Connection to cognitive science literature on attention.]
    
    ## 6. Conclusion
    [Restate key findings. Emphasize the novel contribution.
    Future directions: harder variants, more models, deeper analysis.]
    
    ## References
    [Cite papers mentioned in research notes and related work.
    Use numbered references.]
    
    ## Appendix
    [Full results tables if they're too large for the main text.
    Implementation details. Example prompts.]
    ```
    
    ### Step 4: Generate supporting materials
    
    - Extract or generate key figures as descriptions in `paper/figures/`:
      - `sin_accuracy_curve.md` — description of the accuracy vs noise ratio plot
      - `threshold_table.md` — the attention threshold comparison
      - Any other visualizations that support the narrative
    
    ### Step 5: Review and polish
    
    Re-read the paper and check:
    - [ ] Every claim is supported by data from the results
    - [ ] Tables contain actual numbers (not placeholders)
    - [ ] The narrative flows logically from problem -> method -> results -> insight
    - [ ] The writing is concise and precise (no filler)
    - [ ] Technical details are correct (noise ratios, model names, accuracy numbers)
    - [ ] The paper honestly addresses limitations
    - [ ] The contribution is clearly stated
    
    ### Step 6: Report
    
    Print a summary:
    ```
    Paper generated: paper/paper.md
    
    Sections: [list]
    Word count: ~N words
    Key findings highlighted:
    1. ...
    2. ...
    3. ...
    
    Gaps/TODOs:
    - [anything that needs user input or more data]
    ```
    
    ## Important Guidelines
    
    - **Data-driven**: Every claim must trace back to actual run results. Parse the JSON files — don't rely solely on lab notes summaries.
    - **Honest**: Report what we found, including surprises and failures. The bugs we found (think-tag parsing, preamble) are part of the story.
    - **Specific**: Use exact numbers, model names, and noise ratios. "Several models" is worse than "5 of 8 models".
    - **Novel framing**: Emphasize what's new — the adversarial noise finding, the separation of attention from reasoning, the scaling ladder.
    - **Concise**: Aim for 3,000-5,000 words. Workshop paper length, not a full conference paper.
    - **No fluff**: Every sentence should add information. Cut filler ruthlessly.
    - **Version awareness**: Use the latest results (highest version number). Note if earlier versions revealed important methodological lessons.
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-research-paper-generate \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = paper/paper.md generated with data-backed sections and actual results
    - `failure` = no results found, paper has placeholder data, or write failed
    - `abandoned` = user stopped early

## geno-research-papers-generate

**Slash command:** `/geno-research-papers-generate`

> Generate an academic paper (workshop / extended abstract style) from research findings

??? example "Full skill definition (Level 4)"

    Generate a short academic paper (workshop / extended abstract style) about findings from the current repository's benchmark. The paper synthesizes code, results, lab notes, and development history into a coherent research narrative.
    
    ## Input
    
    `$ARGUMENTS` — Optional instructions (e.g., "focus on adversarial noise findings", "target NeurIPS workshop format", "max 4 pages"). If empty, generate a complete paper covering all findings.
    
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

## geno-research-repo-docs

**Slash command:** `/geno-research-repo-docs`

> Generate purpose-driven repository documentation that captures what we're trying to achieve, the reasoning behind des...

??? info "Observability"

    success_signal: "docs directory populated with README.md, STRUCTURE.md, and CONTRIBUTING.md" failure_signals: - "repo has no source code or meaningful content to document" - "write to geno-tools/docs/ directory failed" - "generated docs contain only generic boilerplate without repo-specific content" knowledge_reads: - "CLAUDE.md, README.md for project context" - "src/, notebooks/, data/, tests/ for codebase understanding" - "requirements.txt / pyproject.toml / package.json for dependencies" - "geno-notes (tasks, journal, plans) for development history" - "research/ folders (up to 3 parent dirs) for research context" - "git log for development trajectory" knowledge_writes: - "geno-tools/docs/README.md (the story — main entry point)" - "geno-tools/docs/STRUCTURE.md (codebase map)" - "geno-tools/docs/CONTRIBUTING.md (how to work here)"

??? example "Full skill definition (Level 4)"

    Generate documentation about the current repository in `geno-tools/docs/`. This is NOT just a "how to run it" guide — it captures **what we're trying to achieve**, the reasoning behind design decisions, and how this repo fits into the broader research context.
    
    ## Input
    
    `$ARGUMENTS` — Optional focus area or instructions (e.g., "focus on the benchmark design", "update the architecture section"). If empty, generate/refresh the full documentation.
    
    ## Output Location
    
    All output goes into `geno-tools/docs/` in the current working directory.
    
    ## Workflow
    
    ### Step 1: Gather context
    
    Read these sources in parallel to build a complete picture:
    
    **Repo-level:**
    - `CLAUDE.md` — project instructions and context
    - `README.md` — existing readme if any
    - `requirements.txt` / `pyproject.toml` / `package.json` — dependencies
    - Browse `src/`, `notebooks/`, `data/`, `tests/` and other key directories
    - Project tasks and journal via `geno-notes` (defaults to project scope; falls back to global if none):
      - `geno-notes list --json` — all tasks with status, dates, tags
      - `geno-notes search <topic>` — find relevant journal entries + plans
      - `$(geno-notes path)/journal/` — timestamped development log (one .md + .jsonl per month)
      - `$(geno-notes path)/plans/` — per-task design plans
      - Use `--all` on `list` or `search` to include global-scope entries when synthesizing across projects
    - Recent git log (last 20-30 commits) for development trajectory
    
    **Research context (blend in from /gt-research outputs):**
    - Check for a `research/` folder in the repo OR in parent directories (walk up to 3 levels)
    - If found, read:
      - The root `Research Overview.md` for overall framing
      - Any sub-area L0 notes relevant to this repo's domain
      - Cross-cutting concept notes in `concepts/`
      - Key L2 idea notes that this repo might implement
      - Reference docs that provide deeper analysis
    - Also check `CLAUDE.md` for pointers to research directories (look for paths mentioning `research/`)
    
    **Parent project context:**
    - Walk up directories looking for parent `CLAUDE.md` files (up to 3 levels) to understand how this repo fits into a larger project
    
    ### Step 2: Synthesize the story
    
    Before writing any files, form a mental model of:
    
    1. **The Why** — What problem or question does this repo address? What would we learn from it?
    2. **The What** — What does it actually do? What are its components?
    3. **The How** — Key design decisions, algorithms, data pipelines
    4. **The Where** — How does it fit into the larger project/research?
    5. **The Status** — What's done, what's in progress, what's planned?
    
    ### Step 3: Create the documentation
    
    Create the following files in `geno-tools/docs/`:
    
    #### `README.md` — The Story (main entry point)
    
    This is the most important file. It tells the narrative:
    
    ```markdown
    # {Repo Name}
    
    ## Why This Exists
    
    {2-3 paragraphs explaining the motivation, research question, and what we hope to learn.
    Pull from research notes to ground this in the broader intellectual context.
    Reference specific papers or concepts from the research knowledge graph if available.}
    
    ## What It Does
    
    {Clear explanation of what the repo produces/measures/builds.
    Not a feature list — a conceptual explanation that someone unfamiliar could follow.}
    
    ## Key Concepts
    
    {Explain the domain-specific concepts that are central to this repo.
    Link to research notes where deeper exploration exists.
    Use analogies and intuitions, not just definitions.}
    
    ## Architecture
    
    {How the pieces fit together. Describe the flow from input to output.
    Include a simple ASCII diagram if helpful:}
    
    ```
    input -> [component A] -> [component B] -> output
    ```
    
    ## Design Decisions
    
    {Key choices made and WHY. These are the things that aren't obvious from reading the code.
    Format as decision records:}
    
    ### Decision: {title}
    - **Context:** {what situation led to this choice}
    - **Choice:** {what we chose}
    - **Reasoning:** {why}
    - **Trade-offs:** {what we gave up}
    
    ## How It Fits In
    
    {Where this repo sits in the larger project. What depends on it, what it depends on.
    Reference parent project context.}
    
    ## Current Status
    
    {What's working, what's in progress, what's planned. Pull from `geno-notes list --json` (by status) and recent journal entries.}
    ```
    
    #### `STRUCTURE.md` — Codebase Map
    
    ```markdown
    # Codebase Structure
    
    ## Directory Layout
    
    {Annotated tree showing what each directory/key file does.
    Not just file names — explain the PURPOSE of each.}
    
    ## Key Files
    
    {For each important file, 1-2 sentences on what it does and why it exists.
    Group by functional area, not alphabetically.}
    
    ## Data Flow
    
    {How data moves through the system. What generates what.
    Trace the path from raw inputs to final outputs.}
    
    ## Dependencies
    
    {Key external dependencies and WHY they're used (not just a list).}
    ```
    
    #### `CONTRIBUTING.md` — How to Work Here
    
    ```markdown
    # Working in This Repo
    
    ## Setup
    
    {How to get a working development environment. Step by step, tested.}
    
    ## Running
    
    {How to run the main workflows. Include actual commands.}
    
    ## Common Tasks
    
    {Patterns for common development tasks:
    - Adding a new [task/benchmark/feature]
    - Running tests
    - Updating data
    - Debugging common issues}
    
    ## Conventions
    
    {Code style, naming conventions, file organization patterns used in this repo.
    Only include conventions that aren't obvious from the code.}
    ```
    
    ### Step 4: Weave in research context
    
    Go back through the generated docs and enrich them:
    
    - Where a concept is explained, add references to research notes: `(see research: [[Note Name]])`
    - Where a design decision was informed by a paper, cite it
    - Where the repo implements an idea from the research graph, connect them explicitly
    - Add a "Research Background" section to README.md if there's substantial research context, with a brief reading path through the most relevant notes
    
    ### Step 5: Verify and report
    
    - List all files created/updated in `geno-tools/docs/`
    - Highlight any gaps (things you couldn't determine from the available context)
    - Suggest what documentation would benefit from the user's input (design rationale you couldn't infer, etc.)
    
    ## Important Guidelines
    
    - **Tell the story first** — always lead with WHY before WHAT or HOW
    - **Don't repeat the code** — documentation should add understanding that reading the code alone doesn't provide
    - **Be honest about gaps** — if you don't know why something was designed a certain way, say so and flag it for the user
    - **Research enrichment is key** — the research context is what makes this more than a generic README generator. Find the connections.
    - **Keep it maintainable** — write docs that can be updated incrementally, not a monolith that goes stale
    - **No fluff** — every sentence should add information. No "This is a very important project that..."
    - **Use concrete examples** — when explaining how something works, show a real example from the repo
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-research-repo-docs \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = docs directory populated with repo-specific README.md, STRUCTURE.md, and CONTRIBUTING.md
    - `failure` = repo had no meaningful content, writes failed, or docs are generic boilerplate
    - `abandoned` = user stopped early

## geno-research-repos-document

**Slash command:** `/geno-research-repos-document`

> Generate purpose-driven documentation for a repository

??? example "Full skill definition (Level 4)"

    Generate documentation about the current repository. This is NOT just a "how to run it" guide — it captures **what we're trying to achieve**, the reasoning behind design decisions, and how this repo fits into the broader research context.
    
    ## Input
    
    `$ARGUMENTS` — Optional focus area or instructions (e.g., "focus on the benchmark design", "update the architecture section"). If empty, generate/refresh the full documentation.
    
    ## Output Location
    
    All output goes into a `docs/` directory in the current working directory.
    
    ## Workflow
    
    ### Step 1: Gather context
    
    Read these sources in parallel to build a complete picture:
    
    **Repo-level:**
    - Agent instruction files — project instructions and context
    - `README.md` — existing readme if any
    - `requirements.txt` / `pyproject.toml` / `package.json` — dependencies
    - Browse `src/`, `notebooks/`, `data/`, `tests/` and other key directories
    - Project tasks and journal via `geno-notes` (defaults to project scope; falls back to global if none):
      - `geno-notes list --json` — all tasks with status, dates, tags
      - `geno-notes search <topic>` — find relevant journal entries + plans
      - `$(geno-notes path)/journal/` — timestamped development log
      - `$(geno-notes path)/plans/` — per-task design plans
      - Use `--all` on `list` or `search` to include global-scope entries when synthesizing across projects
    - Recent git log (last 20-30 commits) for development trajectory
    
    **Research context (blend in from /geno-research outputs):**
    - Check for a `research/` folder in the repo OR in parent directories (walk up to 3 levels)
    - If found, read relevant research notes for theoretical grounding
    
    **Parent project context:**
    - Walk up directories looking for parent instruction files (up to 3 levels) to understand how this repo fits into a larger project
    
    ### Step 2: Synthesize the story
    
    Before writing any files, form a mental model of:
    
    1. **The Why** — What problem or question does this repo address?
    2. **The What** — What does it actually do? What are its components?
    3. **The How** — Key design decisions, algorithms, data pipelines
    4. **The Where** — How does it fit into the larger project/research?
    5. **The Status** — What's done, what's in progress, what's planned?
    
    ### Step 3: Create the documentation
    
    Create the following files:
    
    #### `README.md` — The Story (main entry point)
    Tells the narrative: Why This Exists, What It Does, Key Concepts, Architecture, Design Decisions, How It Fits In, Current Status.
    
    #### `STRUCTURE.md` — Codebase Map
    Directory Layout, Key Files, Data Flow, Dependencies.
    
    #### `CONTRIBUTING.md` — How to Work Here
    Setup, Running, Common Tasks, Conventions.
    
    ### Step 4: Weave in research context
    
    Enrich the generated docs with references to research notes and connections to the broader research graph.
    
    ### Step 5: Verify and report
    
    - List all files created/updated
    - Highlight any gaps
    - Suggest what documentation would benefit from user input
    
    ## Important Guidelines
    
    - **Tell the story first** — always lead with WHY before WHAT or HOW
    - **Don't repeat the code** — documentation should add understanding that reading the code alone doesn't provide
    - **Be honest about gaps** — if you don't know why something was designed a certain way, say so
    - **Research enrichment is key** — the research context makes this more than a generic README generator
    - **Keep it maintainable** — write docs that can be updated incrementally
    - **No fluff** — every sentence should add information
    - **Use concrete examples** — when explaining how something works, show a real example from the repo

## geno-research-wiki

**Slash command:** `/geno-research-wiki`

> Build and maintain a wiki of linked markdown notes using the LLM Wiki pattern

??? info "Observability"

    success_signal: "wiki pages created or updated from research findings" failure_signals: - "web search returned no relevant results" - "wiki directory could not be created or written to" - "lint found issues but fixes corrupted or deleted pages" knowledge_reads: - "existing wiki pages in research/wiki/ for update-vs-create decisions" - "raw sources in research/raw/ for ingestion" - "research/index.md for current wiki structure" knowledge_writes: - "wiki pages in research/wiki/ (created, updated, or split)" - "raw source bookmarks in research/raw/" - "research/index.md (updated with new page links)"

??? example "Full skill definition (Level 4)"

    Research a topic and build a wiki of linked markdown notes. Based on the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — the LLM maintains an evolving, cross-referenced knowledge base rather than producing one-off summaries.
    
    ## Input
    
    `$ARGUMENTS` — A topic, URL, file path, or research question. Examples:
    - `"transformer architectures for long context"`
    - `"https://arxiv.org/abs/2401.12345"`
    - `lint`
    - `ingest paper.pdf`
    
    ## Wiki Location
    
    All output goes into `research/` in the current working directory.
    
    ```
    research/
    ├── index.md          # Entry point — links to all wiki pages
    ├── raw/              # Original sources (saved URLs, PDFs, notes)
    └── wiki/             # LLM-maintained pages with [[wikilinks]]
    ```
    
    If `research/` doesn't exist, create it along with `raw/`, `wiki/`, and a starter `index.md`.
    
    ## Operations
    
    ### Research (default)
    
    When given a topic or question:
    
    1. Create the wiki structure if it doesn't exist
    2. Web search the topic — find papers, articles, code, benchmarks, discussions
    3. For each significant finding, create or update wiki pages in `wiki/`
    4. Each page covers ONE concept, approach, paper, or idea
    5. Use `[[wikilinks]]` to cross-reference between pages
    6. Update `index.md` with links to all pages, loosely grouped by theme
    7. If wiki pages already exist on related topics, UPDATE them with new findings — don't just add new pages in isolation
    
    Launch multiple research agents in parallel when the topic has distinct sub-areas.
    
    ### Ingest
    
    When `$ARGUMENTS` starts with `ingest` followed by a URL or file path:
    
    1. Fetch the URL or read the file
    2. Save a reference in `raw/` (URL bookmark file, or copy the file)
    3. Extract knowledge and create/update wiki pages
    4. A single source often touches multiple pages — update all of them
    5. Update cross-references across affected pages
    6. Update `index.md`
    
    ### Lint
    
    When `$ARGUMENTS` is `lint`:
    
    1. Scan all wiki pages in `wiki/`
    2. Find broken `[[wikilinks]]` (link to pages that don't exist)
    3. Find orphaned pages (no incoming links from other pages)
    4. Find pages that should be split (covering multiple distinct concepts)
    5. Find stale or contradictory information across pages
    6. Report findings, then fix what's straightforward (create missing pages, add links, split oversized pages)
    
    ## Wiki Page Guidelines
    
    - **One concept per page** — if a page covers multiple distinct ideas, split it
    - **Link aggressively** — every concept that has or could have its own page gets a `[[wikilink]]`
    - **Concise but complete** — no artificial word limits, but don't ramble
    - **Sources matter** — cite papers (arXiv IDs), URLs, or other references
    - **No rigid format** — let the content dictate structure. A paper summary looks different from a concept explanation or a comparison table
    - **Human-readable filenames** — spaces OK, avoid special chars except dashes
    - **Obsidian-compatible** — standard markdown with `[[wikilinks]]` and optional `#tags`
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-research-wiki \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = wiki pages created/updated from research, ingestion, or lint
    - `failure` = web search failed, wiki directory unwritable, or lint fixes corrupted pages
    - `abandoned` = user stopped early
