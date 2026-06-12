# Satellite Repo Compliance Patches — 2026-06-12

Automated compliance audit via `geno-audit`. All 5 satellite repos audited against the full
12-section spec in `skills/geno-audit/SKILL.md`. Apply each patch with:

```bash
git clone https://github.com/42euge/<repo>
cd <repo>
git checkout -b chore/geno-audit-compliance
git am .audit-patches-2026-06-12/<repo>.patch
git push -u origin chore/geno-audit-compliance
# then open PR on GitHub
```

## Audit Summary

| Repo | PASS | FAIL | WARN | INFO | Key fixes |
|------|------|------|------|------|-----------|
| geno-iso | 34 | 0 | 5 fixed | 1 | CLAUDE/AGENTS/GEMINI.md → thin pointers; GENO.md SSOT violations removed; /gt- prefix fixed; versioning subsection added |
| geno-mine | 9 | 0 | 11 fixed | 1 | AGENTS.md + GEMINI.md + LICENSE created; Conventions section added to GENO.md; agent-agnostic language; geno-mine-backfill SKILL.md created |
| geno-agents | 8 | 3 fixed | 4 fixed | 1 | .geno-agents untracked; genotools.yaml name "agents"→"geno-agents"; /gt- aliases fixed in 5 SKILL.md files; versioning guidance added |
| geno-dev | 9 | 1 fixed | 8 (4 fixed) | 1 | /gt-pr alias removed; stale loop skills removed from SKILL.md; sessions-remote added to GENO.md + SKILL.md + README; versioning added; .geno-agents untracked |
| geno-notes | 9 | 2 fixed | 2 (1 fixed) | 1 | __version__ synced 0.2.0→0.1.0; 4 sub-skillset SKILL.md dirs created (tasks, inbox, search, workspace); GENO.md + SKILL.md updated; versioning guidance added |

## Patch Details

| Repo | Patch file | Lines |
|------|-----------|-------|
| geno-iso | geno-iso.patch | 402 |
| geno-mine | geno-mine.patch | 276 |
| geno-agents | geno-agents.patch | 167 (2 commits) |
| geno-dev | geno-dev.patch | 187 (2 commits) |
| geno-notes | geno-notes.patch | 450 |

## Unfixable items (require manual action)

- **All repos — Section 1 INFO**: Global gitignore (`~/.config/git/ignore`) does not exist on this machine. Add `.geno/` and `CLAUDE.local.md` there:
  ```bash
  git config --global core.excludesFile ~/.config/git/ignore
  printf '.geno/\nCLAUDE.local.md\n' >> ~/.config/git/ignore
  ```
  Per audit spec, these must NOT be added to any project's `.gitignore`.

- **geno-dev — Section 1 WARN**: Same global gitignore issue as above.

- **geno-dev — Section 5 INFO**: geno-dev-sessions-remote is now in GENO.md/SKILL.md/README but the
  umbrella `skills/geno-dev/SKILL.md` commands list was not updated (intentionally curated scope).

- **geno-notes — Section 7 INFO**: `docs/assets/icon.png` missing (has `logo.svg` only). Generate
  via `/geno-icons` when needed.
