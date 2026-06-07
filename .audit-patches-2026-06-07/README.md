# Ecosystem Compliance Patches — 2026-06-07

Format-patch files for 5 satellite repos audited against the geno-audit spec.
Apply with `git am` to bring each repo into compliance.

## Apply

```bash
for REPO in geno-iso geno-mine geno-agents geno-dev geno-notes; do
  cd ~/path/to/$REPO
  git checkout -b chore/geno-audit-compliance 2>/dev/null || git checkout chore/geno-audit-compliance
  git am < /path/to/.audit-patches-2026-06-07/${REPO}.patch
  git push -u origin chore/geno-audit-compliance
  gh pr create \
    --title "chore(geno-audit): bring ${REPO} into ecosystem compliance" \
    --body "Automated compliance audit via geno-audit (2026-06-07). See https://github.com/42euge/geno-tools/pull/54 for full report." \
    --base main
done
```

## Patches

| Repo | Commit | Changes |
|------|--------|--------|
| geno-iso | 28e2a07 | Remove SSoT violation from GENO.md; replace CLAUDE/AGENTS/GEMINI.md with thin pointers; add versioning guidance |
| geno-mine | f44457b | Add AGENTS.md, GEMINI.md, LICENSE; add allowed-tools to SKILL.md; add Conventions section to GENO.md |
| geno-agents | be5b676 | Fix /gt-supercharge and /gt-tasks-start aliased commands in 4 SKILL.md files; add versioning guidance |
| geno-dev | 8d50bec | Fix /gt-pr in prs-check SKILL.md; register sessions-remote in skills table; add versioning guidance |
| geno-notes | d28572d | Add geno-notes-init and vault-generate to SKILL.md tables; add versioning guidance |
