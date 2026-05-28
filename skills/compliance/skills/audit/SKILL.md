---
name: geno-compliance-audit
description: >-
  Audit a geno-ecosystem repo for compliance with skillset conventions.
  Use when user says /geno-compliance-audit, wants to check if a repo is
  a valid geno-* skillset, or needs to verify ecosystem compliance
  before publishing.
allowed-tools: "Bash(*) Read(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.2.0"
---

# geno-compliance-audit

Validates that a `geno-{name}` repo meets the conventions required for installation and management by `geno-tools`. Runs three tiers of checks: **required** (FAIL), **recommended** (WARN), **optional** (INFO). A repo passing all required checks is installable via `geno-tools install`.

## Rules

The substantive rules live in three sibling docs, loaded only when needed:

- [`rules/geno-convention.md`](rules/geno-convention.md) — the `~/.geno/` and `.geno/` directory convention plus its audit checks.
- [`rules/skillset-shape.md`](rules/skillset-shape.md) — manifest, versioning, umbrella, naming, agent files, docs, hygiene, agent-agnostic language, install compliance, prefix aliasing, single source of truth.
- [`rules/audit-checklist.md`](rules/audit-checklist.md) — the tiered checklist of every assertion, grouped by domain, with stable IDs.

When you need to verify a specific rule, read the matching `rules/*.md` file. When you need a one-pass overview of every assertion, read `rules/audit-checklist.md`.

## Procedure

1. **Resolve the target.** `$ARGUMENTS` accepts:
   - A skillset short name (e.g. `dev`, `media`) — resolve via the registry (`skills/geno-tools/lib/registry.sh` or `skills/lifecycle/skills/install/resources/ls.sh --available`)
   - A GitHub URL — use directly
   - A local path or empty — work in-place

2. **Clone into an isolated working copy.** Never operate on an existing workspace checkout — always clone to an isolated directory to avoid interfering with other agents:
   ```bash
   AUDIT_DIR="$(pwd)/.geno-audit/geno-{name}"
   git clone <url> "$AUDIT_DIR"
   cd "$AUDIT_DIR"
   ```
   Skip cloning if `$ARGUMENTS` is a local path.

3. **Detect the repo name.** Use the directory basename.

4. **Load rules and run checks.** Read [`rules/audit-checklist.md`](rules/audit-checklist.md) for the full tiered check list. For each check, determine PASS / FAIL / WARN / INFO and capture a short reason. When a check needs deeper context (e.g. what's in a valid `genotools.yaml`), consult [`rules/skillset-shape.md`](rules/skillset-shape.md) or [`rules/geno-convention.md`](rules/geno-convention.md).

5. **Parse YAML safely.** Use `yq`:
   ```bash
   yq -o=json '.' <file>
   ```
   For SKILL.md frontmatter, extract YAML between the first pair of `---`:
   ```bash
   awk 'BEGIN{c=0} /^---$/{c++; next} c==1' <file> | yq -o=json '.'
   ```

6. **Fix all auto-fixable items.** After running checks, address every FAIL, WARN, INFO that can be:
   - Create missing files (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `README.md`, `LICENSE`, `docs/`, `mkdocs.yml`) using the templates in `rules/skillset-shape.md`
   - Add missing fields to `genotools.yaml` or SKILL.md frontmatter
   - Generate `CLAUDE.md` / agent instruction files from `SKILL.md`, `genotools.yaml`, and code structure
   - Scaffold `docs/` (`index.md`, `getting-started.md`) and `mkdocs.yml` from the template
   - Generate `README.md` from the manifest description
   - Do **not** modify the project's `.gitignore` for `.geno/` or `CLAUDE.local.md` — those belong in the global gitignore only

7. **Open a PR with the fixes.**
   - Branch: `chore/geno-audit-compliance`
   - Commit message summarizes what was added/fixed
   - PR body uses the report format below
   ```bash
   gh pr create --title "chore(geno-audit): bring repo into ecosystem compliance" --body "$(cat <<'EOF'
   ## Audit Report: geno-{name}

   Automated compliance audit via /geno-compliance-audit.

   ### Summary
     PASS: NN    FAIL: NN fixed    WARN: NN fixed    INFO: NN fixed

   ### Changes
   - [list of files created or modified, grouped by audit domain]

   ### Remaining items
   - [items that could not be auto-fixed, with explanation]
   EOF
   )"
   ```

8. **Clean up.** Remove the cloned directory:
   ```bash
   rm -rf "$AUDIT_DIR"
   ```
   If `.geno-audit/` is now empty, remove it too.

9. **Report.** Print the PR URL and a summary of what was fixed vs. needs manual attention.

## Output format

The on-screen report uses the format documented in [`rules/audit-checklist.md`](rules/audit-checklist.md):

```
Audit: geno-{name}
  PASS: NN    FAIL: NN    WARN: NN    INFO: NN

REQUIRED:
  ✓ MF-1  manifest  genotools.yaml exists
  ✗ SN-2  nomenclature  skills/foo/ missing SKILL.md

RECOMMENDED:
  ⚠ AI-R1  agent files  CLAUDE.md contains content beyond `@./GENO.md`

INFO:
  ℹ EF-I1  freshness  install is 47 days behind origin/main
```

## Completion

When this skill finishes, emit a trace:

```bash
"$CLAUDE_PLUGIN_ROOT/skills/self/skills/improve/resources/trace-emit.sh" \
  --skill geno-compliance-audit \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```
