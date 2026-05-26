---
title: geno-career-letters-generate
description: Generate a tailored cover letter for a specific job posting
---

# geno-career-letters-generate

`/geno-career-letters-generate "<job-url-or-description> [--tone professional|conversational|enthusiastic] [--resume path]"`

> Generate a tailored cover letter for a specific job posting

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Required. Either:
- A URL to a job posting
- A pasted job description
- A company name + role (e.g., "Stripe senior backend engineer")

Optional flags:
- `--tone <tone>` — Writing style: `professional` (default), `conversational`, `enthusiastic`
- `--resume <path>` — Path to tailored resume (for consistency)
- `--output <path>` — Custom output path

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Load context

Read from the `data/` directory at the repo root:
- `data/profile.yaml` for contact info and skills inventory
- `data/resumes/base.md` for experience context
- Config `config/defaults/career.yaml` for tone preference

If `--resume` provided, read that instead of the base resume.

### 2. Extract job details

If URL provided, `WebFetch` the posting. Extract:
- Role title and team
- Key responsibilities
- Required and preferred qualifications
- Company mission/values (from posting or company page)

### 3. Research company (optional)

Use `WebSearch` to gather:
- Recent company news, funding, product launches
- Company culture signals (blog posts, engineering blog)
- Notable projects or tech stack

Keep this brief — 2-3 relevant facts max for the letter.

### 4. Generate cover letter

Write a cover letter that:
- Opens with genuine interest in the specific role (not generic)
- Connects 2-3 pieces of the user's experience to key requirements
- References something specific about the company (from research)
- Demonstrates understanding of the role's challenges
- Closes with enthusiasm and a clear call to action
- Matches the requested tone
- Stays under one page (~300-400 words)

**Rules:**
- Never use filler phrases ("I am writing to express my interest...")
- Never claim skills or experience the user doesn't have
- Be specific — generic letters are worse than no letter
- Match the company's communication style (startup casual vs. enterprise formal)

### 5. Write output

Save to:
1. `--output` path if provided
2. `data/generated/cover-letters/cover-letter-{company}-{role-slug}.md`

### 6. Offer next steps

- "Want me to adjust the tone or emphasis?"
- "Want me to add this to your application tracker?" → `/geno-career-applications-track add`

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-career-letters-generate \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = cover letter written to output path and displayed to user
- `failure` = job posting unreachable, profile/resume missing, or write failed
- `abandoned` = user stopped early or cancelled generation

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-career](index.md)
