# Audit Checklist

Tiered checklist of every assertion the audit makes, grouped by domain. **Required** items must pass for the repo to be considered compliant; **Recommended** items produce warnings; **Info** items are advisory.

For the full prose specification of each rule, see [geno-convention.md](geno-convention.md) and [skillset-shape.md](skillset-shape.md).

## Required (FAIL on miss)

| ID | Domain | Check |
|----|--------|-------|
| GC-1 | `.geno` convention | `.geno/` is not tracked by git |
| GC-2 | `.geno` convention | `CLAUDE.local.md` is not tracked by git |
| MF-1 | manifest | `genotools.yaml` exists at repo root |
| MF-2 | manifest | `genotools.yaml` has a `name` field |
| MF-3 | manifest | `genotools.yaml` has a `version` field |
| MF-4 | manifest | `genotools.yaml` has a non-empty `description` field |
| VR-1 | versioning | `genotools.yaml` `version` is valid semver |
| US-1 | umbrella | `SKILL.md` exists at repo root |
| US-2 | umbrella | `SKILL.md` has YAML frontmatter delimited by `---` |
| US-3 | umbrella | Frontmatter includes a `name` field |
| US-4 | umbrella | Frontmatter includes a non-empty `description` field |
| SN-1 | nomenclature | An umbrella skill exists at `skills/{skillset}/SKILL.md` |
| SN-2 | nomenclature | Every directory under `skills/` (any depth) contains a `SKILL.md` |
| SN-3 | nomenclature | No `commands/` directory exists at repo root |
| SN-4 | nomenclature | Monolithic CLI check: skillsets with ≥3 CLI subcommands have ≥1 sub-skill directory beyond the umbrella |
| AI-1 | agent files | `GENO.md` exists at repo root and is non-empty |
| CP-1 | prefix aliasing | No SKILL.md (root or nested) contains aliased prefixes like `/gt-` in `description` frontmatter or body |
| ST-1 | single source of truth | No file in the repo contains locally redefined ecosystem conventions |

## Recommended (WARN on miss)

| ID | Domain | Check |
|----|--------|-------|
| GC-R1 | `.geno` convention | Global gitignore (`~/.config/git/ignore`) includes `.geno/` and `CLAUDE.local.md` |
| MF-R1 | manifest | `name` matches the repo directory name (with or without `geno-` prefix) |
| VR-R1 | versioning | If `pyproject.toml` has `project.version`, it matches `genotools.yaml` |
| VR-R2 | versioning | If `package.json` has `version`, it matches `genotools.yaml` |
| VR-R3 | versioning | If root `SKILL.md` has `metadata.version`, it matches `genotools.yaml` |
| VR-R4 | versioning | Python `__init__.py` `__version__` matches `genotools.yaml` |
| US-R1 | umbrella | `name` in frontmatter matches the repo name |
| US-R2 | umbrella | Frontmatter includes `allowed-tools` |
| SN-R1 | nomenclature | Skill names follow `{skillset}-{sub-skillset}-{skill}` pattern (in frontmatter `name:`) |
| SN-R2 | nomenclature | Sub-skillset segment is a pluralized noun |
| SN-R3 | nomenclature | Skill segment is an action verb |
| SN-R4 | nomenclature | Umbrella skill's `description` lists all available sub-skill commands |
| SN-R5 | nomenclature | No skill directories exist outside `skills/` |
| AI-R1 | agent files | `CLAUDE.md` contains only `@./GENO.md` |
| AI-R2 | agent files | `GEMINI.md` contains only `@./GENO.md` |
| AI-R3 | agent files | `AGENTS.md` contains only `@import GENO.md` |
| AI-R4 | agent files | `gemini-extension.json` `contextFileName` is `GEMINI.md` |
| AI-R5 | agent files | No agent instruction content duplicated across files |
| AI-R6 | agent files | `GENO.md` Conventions section mentions command prefix aliasing |
| AI-R7 | agent files | `GENO.md` Conventions section includes skill creation guidance |
| AI-R8 | agent files | `GENO.md` skills table uses canonical `/geno-{name}-*` slash commands |
| AI-R9 | agent files | `GENO.md` Conventions section includes versioning guidance |
| DC-R1 | docs | `docs/` directory exists |
| DC-R2 | docs | `docs/index.md` exists |
| DC-R3 | docs | `docs/getting-started.md` exists |
| DC-R4 | docs | `mkdocs.yml` exists at repo root |
| DC-R5 | docs | `mkdocs.yml` uses `material` theme |
| RH-R1 | hygiene | `README.md` exists |
| RH-R2 | hygiene | `LICENSE` file exists |
| RH-R3 | hygiene | Repo directory name matches `geno-*` convention |
| AL-R1 | agent-agnostic | Body text uses agent-neutral phrasing (no "Claude Code only" framing) |
| AL-R2 | agent-agnostic | Prerequisites list supported CLIs generically |
| IC-R1 | install compliance | No file contains `npx skills add` as a user-facing install instruction |
| IC-R2 | install compliance | Install instructions use `geno-tools install geno-{name}` form |
| EF-R1 | freshness | Installed copy is on latest main |
| EF-R2 | freshness | `main` worktree has clean working tree |
| CP-R1 | prefix aliasing | No file contains aliased slash command references in body content |

## Info (advisory)

| ID | Domain | Check |
|----|--------|-------|
| VR-I1 | versioning | Skills added/removed since last git tag — version bump may be warranted |
| MF-I1 | manifest | If `pyproject.toml` exists, `project.name` matches the manifest name |
| EF-I1 | freshness | Current installed revision and date of last main commit (stale > 30 days noted) |
| DC-I1 | docs | `docs/assets/icon.png` exists |
| DC-I2 | docs | `docs/cli-reference.md` exists (if CLI present) |
| DC-I3 | docs | `mkdocs.yml` has `site_url` and `repo_url` configured |
| US-I1 | umbrella | Frontmatter includes `metadata` with `author` and `version` |

## Output format

For each repo audited, emit a summary line then a table grouped by tier:

```
Audit: geno-{name}
  PASS: NN    FAIL: NN    WARN: NN    INFO: NN

REQUIRED:
  ✓ MF-1  manifest  genotools.yaml exists
  ✗ SN-2  nomenclature  skills/foo/ missing SKILL.md
  ...

RECOMMENDED:
  ⚠ AI-R1  agent files  CLAUDE.md contains content beyond `@./GENO.md`
  ...

INFO:
  ℹ EF-I1  freshness  install is 47 days behind origin/main
  ...
```

A repo with **zero FAILs** is installable. A repo with FAILs must be fixed before it can pass through `geno-tools install`.
