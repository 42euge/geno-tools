---
title: geno-career-applications-track
description: Track job applications through the pipeline
---

# geno-career-applications-track

`/geno-career-applications-track "[add|update|list|show|stats] [args...]"`

> Track job applications through the pipeline

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Subcommand + args:
- `add <company> <role> [--url <url>] [--status applied]` — Add new application
- `update <id-or-company> --status <status> [--notes "..."]` — Update status
- `list [--status <status>] [--active]` — List applications
- `show <id-or-company>` — Show full details for an application
- `stats` — Summary statistics across all applications
- (no args) — Show active applications (same as `list --active`)

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Data Format

Applications are stored in a YAML file at `data/applications.yaml` (repo root, gitignored):

```yaml
applications:
  - id: 1
    company: Stripe
    role: Senior Backend Engineer
    url: https://stripe.com/jobs/...
    status: technical
    applied_date: 2026-04-20
    status_history:
      - { status: applied, date: 2026-04-20 }
      - { status: phone-screen, date: 2026-04-23 }
      - { status: technical, date: 2026-04-25, notes: "Take-home due May 1" }
    resume_path: ~/Documents/career/resumes/resume-stripe-senior-backend.md
    cover_letter_path: ~/Documents/career/cover-letters/cover-letter-stripe-senior-backend.md
    contacts:
      - { name: "Jane Doe", role: "Hiring Manager", email: "jane@stripe.com" }
    salary_range: "$180k-$220k"
    notes: "Referral from Alex. Team works on payment processing infra."
    tags: [fintech, backend, distributed-systems]
```

## Workflow

### `add`

1. Create the tracker file if it doesn't exist
2. Auto-increment the ID
3. Set `applied_date` to today, `status` to the provided value (default: `applied`)
4. Initialize `status_history` with the first entry
5. If resume/cover-letter paths exist for this company in the output dirs, link them
6. Write to tracker file

### `update`

1. Find the application by ID or fuzzy-match on company name
2. If ambiguous, ask the user to clarify
3. Update the status field
4. Append to `status_history` with today's date and optional notes
5. Write to tracker file

### `list`

1. Read tracker file
2. Filter by `--status` if provided, or `--active` (excludes rejected/withdrawn/accepted)
3. Display as a clean table:

```
 ID | Company  | Role                    | Status       | Applied    | Days
----+----------+-------------------------+--------------+------------+------
  1 | Stripe   | Senior Backend Eng      | technical    | 2026-04-20 |    6
  3 | Vercel   | Staff Platform Eng      | phone-screen | 2026-04-22 |    4
  5 | Linear   | Senior Product Eng      | applied      | 2026-04-25 |    1
```

### `show`

Display full details for a single application including status history timeline,
linked documents, contacts, and notes.

### `stats`

Summary dashboard:
- Total applications, active, offers, rejections
- Average time in each stage
- Response rate (applications that progressed past "applied")
- Pipeline funnel visualization

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-career-applications-track \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = subcommand completed -- application added, updated, listed, shown, or stats displayed
- `failure` = tracker file malformed, application not found, or write failed
- `abandoned` = user stopped early or cancelled operation

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-career](index.md)
