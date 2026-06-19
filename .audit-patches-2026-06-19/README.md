# Cross-Repo Audit Patches — 2026-06-19

This directory contains `git format-patch` output for each satellite repo audited on 2026-06-19. Patches were prepared but could not be pushed directly (no HTTPS/SSH credentials in the remote execution environment).

## Apply instructions

For each satellite repo, apply its patch on a `chore/geno-audit-compliance` branch:

```bash
# geno-iso
git clone https://github.com/42euge/geno-iso && cd geno-iso
git checkout -b chore/geno-audit-compliance
git am < /path/to/.audit-patches-2026-06-19/geno-iso.patch
git push -u origin chore/geno-audit-compliance
cd ..

# geno-mine
git clone https://github.com/42euge/geno-mine && cd geno-mine
git checkout -b chore/geno-audit-compliance
git am < /path/to/.audit-patches-2026-06-19/geno-mine.patch
git push -u origin chore/geno-audit-compliance
cd ..

# geno-agents
git clone https://github.com/42euge/geno-agents && cd geno-agents
git checkout -b chore/geno-audit-compliance
git am < /path/to/.audit-patches-2026-06-19/geno-agents.patch
git push -u origin chore/geno-audit-compliance
cd ..

# geno-dev
git clone https://github.com/42euge/geno-dev && cd geno-dev
git checkout -b chore/geno-audit-compliance
git am < /path/to/.audit-patches-2026-06-19/geno-dev.patch
git push -u origin chore/geno-audit-compliance
cd ..

# geno-notes
git clone https://github.com/42euge/geno-notes && cd geno-notes
git checkout -b chore/geno-audit-compliance
git am < /path/to/.audit-patches-2026-06-19/geno-notes.patch
git push -u origin chore/geno-audit-compliance
cd ..
```

Then open a PR on each repo from `chore/geno-audit-compliance` → `main`.

## Patch summary

| Repo | Findings fixed | Description |
|------|----------------|-------------|
| geno-iso | 7 (4 FAIL, 3 WARN) | Pointer files were full copies of GENO.md; removed SSOT violation sections |
| geno-mine | 5 (0 FAIL, 5 WARN) | Missing AGENTS.md, GEMINI.md, LICENSE; missing allowed-tools; no Conventions |
| geno-agents | 7 (5 FAIL, 2 WARN) | genotools.yaml name wrong; /gt-* aliases in SKILL.md descriptions/body |
| geno-dev | 3 (1 FAIL, 2 WARN) | /gt-pr alias in description; stale /geno-dev-loops-* skill refs; unregistered sessions-remote |
| geno-notes | 2 (1 FAIL, 1 WARN) | Version mismatch: genotools.yaml/pyproject.toml 0.1.0 vs __init__.py 0.2.0 |
