# geno-audit compliance patches — 2026-06-02

Patches from the full 12-section `geno-audit` checklist run against the 5 non-geno-tools repos.
Apply each patch to bring the corresponding repo into ecosystem compliance and open a PR.

## Apply a patch

```bash
for REPO in geno-iso geno-mine geno-agents geno-dev geno-notes; do
  git clone https://github.com/42euge/$REPO /tmp/$REPO
  cd /tmp/$REPO
  git checkout -b chore/geno-audit-compliance
  git am < /path/to/.audit-patches/$REPO.patch
  git push -u origin chore/geno-audit-compliance
done
```

Then open a PR on each repo:

```bash
# Requires gh CLI with repo access
for REPO in geno-iso geno-mine geno-agents geno-dev geno-notes; do
  gh pr create \
    --repo 42euge/$REPO \
    --head chore/geno-audit-compliance \
    --base main \
    --title "chore(geno-audit): bring $REPO into ecosystem compliance" \
    --body "Automated compliance audit via geno-audit (2026-06-02). See https://github.com/42euge/geno-tools/pull/51 for full report."
done
```

## Per-repo findings summary

### geno-iso — FAIL: 3 fixed, WARN: 1 fixed

| # | Section | Result | Fix |
|---|---------|--------|-----|
| S6 | Agent Instruction Files | WARN → fixed | Added Versioning subsection to GENO.md Conventions |
| S12 | Command Prefix Aliasing | WARN → fixed | `/gt-iso-containers-run` → `/geno-iso-containers-run` in GENO.md |
| S13 | Single Source of Truth | FAIL → fixed | Removed "Agent instruction files" section from GENO.md (prescribed full-copy pattern contradicting pointer convention) |
| S13 | Single Source of Truth | FAIL → fixed | Removed SKILL.md frontmatter format spec from "Adding a new skill" checklist |
| S13 | Single Source of Truth | FAIL → fixed | AGENTS.md, CLAUDE.md, GEMINI.md were full copies of GENO.md — reverted to thin pointer files |

**Files changed:** AGENTS.md, CLAUDE.md, GEMINI.md, GENO.md (8 insertions, 326 deletions)

---

### geno-mine — WARN: 5 fixed

| # | Section | Result | Fix |
|---|---------|--------|-----|
| S4 | Umbrella SKILL.md | WARN → fixed | Added `allowed-tools` field to root SKILL.md |
| S6 | Agent Instruction Files | WARN → fixed | Created GEMINI.md and AGENTS.md thin pointer files (were missing) |
| S6 | Agent Instruction Files | WARN → fixed | Added Conventions section to GENO.md (command prefix aliasing, versioning, skill creation guidance) |
| S8 | Repo Hygiene | WARN → fixed | Added MIT LICENSE file |
| S9 | Agent-Agnostic Language | WARN → fixed | Replaced "Claude Code session transcripts" with agent-neutral language in GENO.md, SKILL.md files, docs/getting-started.md, and geno-mine-extract/SKILL.md |
| S13 | Single Source of Truth | WARN → fixed | Removed SKILL.md frontmatter format spec from "Adding a new skill" in GENO.md |

**Files changed:** AGENTS.md (new), GEMINI.md (new), GENO.md, LICENSE (new), docs/getting-started.md, skills/geno-mine-extract/SKILL.md, skills/geno-mine/SKILL.md (60 insertions, 6 deletions)

---

### geno-agents — FAIL: 5 fixed

| # | Section | Result | Fix |
|---|---------|--------|-----|
| S2 | Manifest | FAIL → fixed | `genotools.yaml` `name: agents` → `name: geno-agents` |
| S3 | Versioning | FAIL → fixed | `geno_agents/__init__.py` was empty — added `__version__ = "0.1.0"` |
| S12 | Command Prefix Aliasing | FAIL × 4 → fixed | `/gt-supercharge` → `/geno-agents-supercharge` across SKILL.md, skills/geno-agents/SKILL.md, skills/geno-agents-supercharge/SKILL.md; `/gt-kaggle-benchmarks-task-review` and `/gt-kaggle-benchmarks-task-generate` → canonical `/geno-*` names; `/gt-tasks-start` → `/geno-agents-tasks-start` in skills/geno-agents-tasks-start/SKILL.md |
| S13 | Single Source of Truth | FAIL → fixed | GENO.md had 6-step "Adding a new skill" checklist (with frontmatter spec) + verbatim Versioning rule — replaced with pointers to geno-tools GENO.md |

**Files changed:** GENO.md, SKILL.md, geno_agents/__init__.py, genotools.yaml, skills/geno-agents-supercharge/SKILL.md, skills/geno-agents-tasks-start/SKILL.md, skills/geno-agents/SKILL.md (14 insertions, 16 deletions)

---

### geno-dev — FAIL: 1 fixed, WARN: 4 fixed

| # | Section | Result | Fix |
|---|---------|--------|-----|
| S5 | Skill Nomenclature | WARN → fixed | `geno-dev-sessions-remote` skill was undocumented — added to GENO.md skills table, repo structure, and both umbrella SKILL.md files |
| S6 | Agent Instruction Files | WARN → fixed | Added `### Command prefix aliasing` subsection to GENO.md Conventions |
| S6 | Agent Instruction Files | WARN → fixed | Added `### Versioning` subsection to GENO.md Conventions |
| S9 | Agent-Agnostic Language | WARN → fixed | `skills/geno-dev-sessions-remote/SKILL.md` description was Claude Code-specific — reworded to agent-neutral language |
| S12 | Command Prefix Aliasing | FAIL → fixed | `skills/geno-dev-prs-check/SKILL.md` description had `or /gt-pr` — removed; `skills/geno-dev-branches-audit/SKILL.md` example branch `feat/gt-snooze` renamed to `feat/geno-dev-scheduling-snooze` |

**Files changed:** GENO.md, SKILL.md, skills/geno-dev-branches-audit/SKILL.md, skills/geno-dev-prs-check/SKILL.md, skills/geno-dev-sessions-remote/SKILL.md, skills/geno-dev/SKILL.md (21 insertions, 13 deletions)

---

### geno-notes — FAIL: 1 fixed, WARN: 3 fixed

| # | Section | Result | Fix |
|---|---------|--------|-----|
| S3 | Versioning | WARN → fixed | `geno_notes/__init__.py` `__version__` was `"0.2.0"` instead of `"0.1.0"` (canonical: `genotools.yaml`) — corrected |
| S5 | Skill Nomenclature | FAIL → fixed | 18 CLI subcommands but only 5 skill dirs had SKILL.md — created SKILL.md for all remaining dirs (10 new files covering inbox, items, notes, knowledge, site, workspaces sub-skillsets) |
| S6 | Agent Instruction Files | WARN → fixed | GENO.md skills table and repo structure expanded to list all 24 skills |
| S9 | Agent-Agnostic Language | WARN → fixed | `install.sh` hardcoded `~/.claude/` paths — removed and replaced with `npx skills add` (agent-agnostic skill registration) |

**Files changed:** GENO.md, SKILL.md, geno_notes/__init__.py, install.sh, package.json, skills/geno-notes/SKILL.md, 18 new sub-skillset SKILL.md files (1100 insertions, 41 deletions)

---

## Remaining items (all repos, cannot auto-fix)

- **Global gitignore** — `~/.config/git/ignore` should include `.geno/` and `CLAUDE.local.md`. Must NOT go in any project's `.gitignore`.
- **`docs/assets/icon.png`** — missing from all repos. Run `/geno-icons` per-repo to generate icons.
- **Git tags** — no repos have version tags. Consider tagging `v0.1.0` once compliance PRs merge.
- **geno-dev `allowed-tools`** — root SKILL.md and `skills/geno-dev/SKILL.md` still missing `allowed-tools` field (pure markdown skillset, tool set depends on sub-skills). Low priority.
- **S1 WARN (global gitignore)** — add `.geno/` and `CLAUDE.local.md` to `~/.config/git/ignore` on each developer machine.
