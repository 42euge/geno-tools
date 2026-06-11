# Satellite Repo Compliance Patches — 2026-06-11

Automated compliance audit via `geno-audit`. All 5 satellite repos audited against the 12-section spec in `skills/geno-audit/SKILL.md`. Apply each patch with:

```bash
git clone https://github.com/42euge/<repo>
cd <repo>
git am .audit-patches-2026-06-11/<repo>.patch
git push -u origin chore/geno-audit-compliance
# then open PR on GitHub
```

## Patch Summary

| Repo | Patch file | Changes |
|------|-----------|--------|
| geno-iso | geno-iso.patch | Convert CLAUDE/AGENTS/GEMINI.md from full copies to thin pointers; remove SSOT violations from GENO.md ("Agent instruction files" and "Adding a new skill" subsections) |
| geno-mine | geno-mine.patch | Add AGENTS.md, GEMINI.md, LICENSE; add Conventions section to GENO.md; fix "Claude Code" → "agent" language in SKILL.md and docs |
| geno-agents | geno-agents.patch | Untrack .geno-agents (add to .gitignore); fix /gt- → /geno- aliases in 5 SKILL.md files; fix genotools.yaml name from 'agents' to 'geno-agents'; add versioning guidance to GENO.md |
| geno-dev | geno-dev.patch | Remove /gt-pr alias from prs-check SKILL.md; remove 6 non-existent loop skills from root SKILL.md; add sessions-remote to GENO.md skills table; add versioning to Conventions |
| geno-notes | geno-notes.patch | Fix __version__ mismatch (0.2.0→0.1.0); create 10 sub-skillset SKILL.md files for monolithic CLI coverage (tasks, journal, search, scopes, admin); update umbrella SKILL.md |
