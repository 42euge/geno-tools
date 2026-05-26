---
title: geno-career-jobs-search
description: Search for job postings across multiple boards (LinkedIn, Indeed, Glassdoor, Wellfound, YC)
---

# geno-career-jobs-search

`/geno-career-jobs-search "<query> [--remote] [--level senior] [--board linkedin] [--days 14]"`

> Search for job postings across multiple boards (LinkedIn, Indeed, Glassdoor, Wellfound, YC)

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Required. The search query plus optional filters:
- `<query>` — Job title, keywords, or company (e.g., "ML engineer", "senior backend at Stripe")
- `--remote` — Filter to remote positions
- `--level <level>` — Experience level: junior, mid, senior, staff, principal
- `--board <board>` — Specific board: linkedin, indeed, glassdoor, wellfound, ycombinator
- `--days <n>` — Posted within last N days (default: 30)
- `--location <loc>` — Location filter (e.g., "San Francisco", "US")

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Load config and profile

Read `config/defaults/career.yaml` for default search preferences and
`data/profile.yaml` for skills keywords (used to highlight strong matches).
Merge with any flags from `$ARGUMENTS` (flags override config).

### 2. Build search queries

For each target job board, construct a site-scoped web search query:
- LinkedIn: `site:linkedin.com/jobs "<query>" <location> <level>`
- Indeed: `site:indeed.com "<query>" <filters>`
- Glassdoor: `site:glassdoor.com/Job "<query>"`
- Wellfound: `site:wellfound.com/role "<query>"`
- Y Combinator: `site:workatastartup.com "<query>"` or `site:ycombinator.com/jobs "<query>"`

If `--board` is specified, only search that board. Otherwise search all configured boards.

### 3. Search and collect results

Use `WebSearch` for each board query. For the top results, use `WebFetch` to
extract key details:
- Job title
- Company name
- Location / Remote status
- Posted date
- Salary range (if listed)
- URL

### 4. Present results

Display results in a clean table, grouped by board. Include a summary count
and highlight strong matches based on the user's profile keywords from config.

### 5. Offer next steps

After presenting results, offer:
- "Want me to tailor your resume for any of these?" → `/geno-career-resumes-build`
- "Want me to write a cover letter?" → `/geno-career-letters-generate`
- "Want me to add any to your tracker?" → `/geno-career-applications-track add`

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-career-jobs-search \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = results table displayed with at least one matching posting
- `failure` = all search queries returned zero results, config missing, or tool calls failed
- `abandoned` = user stopped early or cancelled search

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-career](index.md)
