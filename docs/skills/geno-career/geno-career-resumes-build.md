---
title: geno-career-resumes-build
description: Build or tailor a resume for a specific job posting
---

# geno-career-resumes-build

`/geno-career-resumes-build "<job-url-or-description> [--base path/to/resume.md] [--format md|pdf]"`

> Build or tailor a resume for a specific job posting

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Required. Either:
- A URL to a job posting
- A pasted job description
- A path to a file containing the job description

Optional flags:
- `--base <path>` — Path to base resume (overrides config)
- `--format <fmt>` — Output format: `md` (default), `pdf` (requires pandoc + LaTeX)
- `--output <path>` — Custom output path

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Load base resume and profile

Read from the `data/` directory at the repo root:
1. `--base` flag if provided
2. Otherwise `data/resumes/base.md` (the master resume)
3. Always also read `data/profile.yaml` for structured skills/education data
4. Check `data/source/` for variant notes that may inform tailoring strategy

If `data/resumes/base.md` doesn't exist, ask the user to provide a resume or run setup.

### 2. Extract job requirements

If `$ARGUMENTS` contains a URL, use `WebFetch` to retrieve the posting.
Parse and extract:
- **Required skills** — languages, frameworks, tools
- **Preferred skills** — nice-to-haves
- **Experience level** — years, seniority
- **Key responsibilities** — what the role does day-to-day
- **Company context** — domain, stage, team size

### 3. Analyze gaps and strengths

Compare the job requirements against the base resume:
- **Strong matches** — experience that directly maps to requirements
- **Reframeable experience** — adjacent skills that can be positioned to match
- **Gaps** — requirements not covered (flag but don't fabricate)

### 4. Generate tailored resume

Restructure the resume:
- Reorder sections to lead with most relevant experience
- Rewrite bullet points to use keywords from the posting
- Emphasize quantified achievements that map to responsibilities
- Adjust the summary/objective to target this specific role
- Keep it honest — never fabricate experience or skills

### 5. Write output

Save the tailored resume to:
1. `--output` path if provided
2. `data/generated/resumes/resume-{company}-{role-slug}.md`

Display a diff summary showing what changed from the base resume.

### 6. Offer next steps

- "Want me to generate a cover letter for this role?" → `/geno-career-letters-generate`
- "Want me to add this to your application tracker?" → `/geno-career-applications-track add`
- "Want me to export to PDF?" (if format was md)

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-career-resumes-build \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = tailored resume written to output path with diff summary displayed
- `failure` = base resume missing, job posting unreachable, or write failed
- `abandoned` = user stopped early or cancelled tailoring

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-career](index.md)
