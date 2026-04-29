---
name: geno-audit
description: >-
  Ecosystem compliance auditor for geno-* repos. Runs naming, structure,
  and security checks against a skillset before registry admission or
  periodic re-audit. Use when the user wants to audit a skillset for compliance.
allowed-tools: "Bash(git *) Bash(find *) Bash(grep *) Read"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-audit — Ecosystem Compliance Auditor

Audits a `geno-*` repo against the full compliance checklist before it's admitted to the registry or re-audited after a major update. Covers identity, SKILL.md content, slash commands, code, network, filesystem, multi-agent integration, documentation, and skill nomenclature.

See `docs/onboarding/audit.md` for the full reviewer checklist; this skill drives the agent-assisted workflow on top of it.

## When to invoke

- User says "audit this skillset" / "run the compliance check on geno-X".
- A new skillset is being onboarded to the public registry.
- A major version bump touched `SKILL.md`, `commands/`, or `pyproject.toml`.
- Maintainer has changed or a periodic re-audit is due.

## Audit workflow

1. **Identify the target** — resolve the repo name or URL; clone at the exact ref being audited (not `main` if the PR pins a tag).
2. **Run each section** — walk the checklist top to bottom. Flag failures inline with file + line reference.
3. **Capture findings** — write a summary: pass / fail / n/a / accepted-with-mitigation for every item.
4. **Sign off or reject** — no open red flags may remain. Accepted-with-mitigation items need a written rationale.

---

## Skill Nomenclature

Skills must follow the `{skillset}-{sub-skillset}-{skill-slug}` naming hierarchy defined in `docs/skillsets/nomenclature.md`.

| Term | Definition | Example |
|------|-----------|---------|
| Skillset | The `geno-*` repo | `geno-dev` |
| Sub-skillset | Pluralized-noun grouping within a skillset | `tasks`, `commits` |
| Skill | Action-verb capability within a sub-skillset | `start`, `rewrite` |

### Audit checks

- [ ] **Required** — All skill names under `skills/` (excluding the umbrella) match `{skillset}-{sub-skillset}-{skill-slug}` exactly. No bare two-segment names like `geno-notes-add`.
- [ ] **Required** — Sub-skillset segment is a **pluralized noun** (`tasks` not `task`, `benchmarks` not `benchmark`, `commits` not `commit`).
- [ ] **Required** — Skill slug is an **action verb** (`start`, `scaffold`, `run`, `rewrite`, `scrape`). Nouns and adjectives are not acceptable slugs.
- [ ] **Required** — Exactly one umbrella skill directory exists, named `{skillset}`, containing `skills/{skillset}/SKILL.md`. Its frontmatter `name` field equals the repo name.
- [ ] **Required** — Command files in `commands/` use the full canonical skill name as the filename (e.g. `geno-dev-tasks-start.md` not `tasks-start.md`).
- [ ] **Required** — **Monolithic CLI check**: if the skillset has a CLI backend — indicated by a `[project.scripts]` entry in `pyproject.toml` or a standalone bin script — with multiple subcommands, it must expose at least one sub-skillset skill directory under `skills/` beyond the umbrella. To check: (a) inspect the CLI entry point for `add_parser` / `add_command` calls (argparse, click, typer) to count subcommands; (b) count `skills/*/SKILL.md` files and subtract 1 for the umbrella. A skillset with ≥ 3 CLI subcommands and zero sub-skillset skills **fails**. A `CLAUDE.md` declaration like "single-skill skillset" does not exempt the repo from this check. **Correct pattern**: geno-dev (9 sub-skills — `geno-dev-tasks-start`, `geno-dev-commits-rewrite`, `geno-dev-loops-cruise`, `geno-dev-sessions-fork`, etc.). **Failure example**: geno-notes (18 CLI subcommands — add, start, done, abandon, note, inbox, triage, list, show, search, promote, reindex, compile, lint, site, path, scope, init — but only the umbrella `geno-notes/` skill, no sub-skillset skills).
