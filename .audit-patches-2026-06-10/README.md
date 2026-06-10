# Audit Patches — 2026-06-10

These patches contain all compliance fixes found in the 2026-06-10 geno-ecosystem
audit run. Apply each to the corresponding repo with:

```bash
cd /path/to/repo
git checkout -b chore/geno-audit-compliance
git am < /path/to/.audit-patches-2026-06-10/<repo>.patch
git push -u origin chore/geno-audit-compliance
# then open a PR
```

## Patches

| File | Repo | Changes |
|------|------|---------|
| geno-iso.patch | 42euge/geno-iso | 4 FAIL fixed, 3 WARN fixed |
| geno-agents.patch | 42euge/geno-agents | 2 FAIL fixed, 1 WARN fixed |
| geno-mine.patch | 42euge/geno-mine | 3 WARN fixed |
| geno-notes.patch | 42euge/geno-notes | 4 sections fixed (10 sub-skill SKILL.md files created) |
| geno-dev.patch | 42euge/geno-dev | 4 FAIL fixed, 5 WARN fixed |
