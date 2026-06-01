# Audit Checklist

Tiered checklist of every assertion the audit makes, grouped by domain. **Required** items must pass for the repo to be considered compliant; **Recommended** items produce warnings; **Info** items are advisory.

For the full prose specification of each rule, see [geno-convention.md](geno-convention.md) and [skillset-shape.md](skillset-shape.md).

Path-sensitive checks accept both layouts: **Legacy** (root: `genotools.yaml`, `GENO.md`, `VISION.md`, `mkdocs.yml`, `docs/`, `scripts/`, `hooks/`, `.opencode/`, `.agents/`) and **Namespaced** (root: `AGENTS.md`, `CLAUDE.md`, `skills.sh.json`, plus `.geno/geno-{tools,specs,docs}/...` and `.geno/plugins/{opencode,codex-agents}/`). A repo must commit to one layout — see `LV-1` below.

## Required (FAIL on miss)

| ID | Domain | Check |
| ---- | -------- | ------- |
| GC-1 | `.geno` convention | `.geno/.workspace/` (workspace state) is not tracked by git |
| GC-2 | `.geno` convention | `CLAUDE.local.md` is not tracked by git |
| LV-1 | layout | Exactly one layout in use — no duplicates between root and `.geno/<sub-namespace>/` for `genotools.yaml`, `VISION.md`, `TENETS.md`, `mkdocs.yml`, `docs/` |
| MF-1 | manifest | `genotools.yaml` exists at the layout-appropriate location (root **or** `.geno/geno-tools/genotools.yaml`) |
| MF-2 | manifest | `genotools.yaml` has a `name` field |
| MF-3 | manifest | `genotools.yaml` has a `version` field |
| MF-4 | manifest | `genotools.yaml` has a non-empty `description` field |
| SM-1 | skills manifest | `skills.sh.json` exists at repo root (required in namespaced layout) |
| SM-2 | skills manifest | Every leaf `SKILL.md` under `skills/` has a corresponding entry in `skills.sh.json` |
| SM-3 | skills manifest | Every entry in `skills.sh.json` resolves to an existing on-disk path |
| VR-1 | versioning | `genotools.yaml` `version` is valid semver |
| US-1 | umbrella | A skillset-root `SKILL.md` exists (root `SKILL.md` or `skills/{skillset}/SKILL.md`) |
| US-2 | umbrella | Umbrella `SKILL.md` has YAML frontmatter delimited by `---` |
| US-3 | umbrella | Frontmatter includes a `name` field |
| US-4 | umbrella | Frontmatter includes a non-empty `description` field |
| SN-1 | nomenclature | An umbrella skill exists at `skills/{skillset}/SKILL.md` |
| SN-2 | nomenclature | Every directory under `skills/` (any depth) contains a `SKILL.md` |
| SN-3 | nomenclature | No `commands/` directory exists at repo root |
| SN-4 | nomenclature | Monolithic CLI check: skillsets with ≥3 CLI subcommands have ≥1 sub-skill directory beyond the umbrella |
| AI-1 | agent files | A source-of-truth instruction file exists and is non-empty (`GENO.md` for Model A, `AGENTS.md` for Model B) |
| AI-2 | agent files | If Model B (no `GENO.md`, non-trivial `AGENTS.md`), `CLAUDE.md` exists and is byte-for-byte identical to `AGENTS.md` |
| IA-1 | installer assets | `bootstrap.sh` exists at the layout-appropriate location (`scripts/` legacy or `.geno/geno-tools/scripts/` namespaced) |
| IA-2 | installer assets | `hooks/hooks.json` exists at the layout-appropriate location |
| IA-3 | installer assets | `hooks/hooks.json` paths resolve — no broken `${CLAUDE_PLUGIN_ROOT}/...` references |
| CP-1 | prefix aliasing | No SKILL.md (root or nested) contains aliased prefixes like `/gt-` in `description` frontmatter or body |
| ST-1 | single source of truth | No file in the repo contains locally redefined ecosystem conventions |

## Recommended (WARN on miss)

| ID | Domain | Check |
| ---- | -------- | ------- |
| GC-R1 | `.geno` convention | Global gitignore (`~/.config/git/ignore`) includes `.geno/.workspace/` and `CLAUDE.local.md` |
| GC-R2 | `.geno` convention | Sub-namespaced dirs (`.geno/geno-{tools,specs,docs}/`, `.geno/plugins/`) ARE tracked by git when present |
| MF-R1 | manifest | `name` matches the repo directory name (with or without `geno-` prefix) |
| SM-R1 | skills manifest | `skills.sh.json` regenerated from current SKILL.md inventory (no drift) |
| SM-R2 | skills manifest | Versions in `skills.sh.json` match `genotools.yaml` and per-skill `metadata.version` |
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
| AI-R1 | agent files (Model A) | `CLAUDE.md` contains only `@./GENO.md` |
| AI-R2 | agent files (Model A) | `GEMINI.md` contains only `@./GENO.md` |
| AI-R3 | agent files (Model A) | `AGENTS.md` contains only `@import GENO.md` |
| AI-R4 | agent files | `gemini-extension.json` `contextFileName` points to `GEMINI.md` |
| AI-R5 | agent files | No agent instruction content duplicated across files (all substance lives in the source-of-truth file) |
| AI-R6 | agent files | Source instruction file Conventions section mentions command prefix aliasing |
| AI-R7 | agent files | Source instruction file Conventions section includes skill creation guidance |
| AI-R8 | agent files | Source instruction file's skills table uses canonical `/geno-{name}-*` slash commands |
| AI-R9 | agent files | Source instruction file Conventions section includes versioning guidance |
| AI-R10 | agent files (Model B) | `.github/workflows/check-claude-md.yml` exists and diffs `AGENTS.md` against `CLAUDE.md` on push |
| VS-R1 | vision/tenets | `VISION.md` exists at the layout-appropriate location and is non-empty |
| VS-R2 | vision/tenets | `TENETS.md` exists at the layout-appropriate location and is non-empty |
| DC-R1 | docs | `docs/` directory exists at the layout-appropriate location |
| DC-R2 | docs | `docs/index.md` exists |
| DC-R3 | docs | `docs/getting-started.md` exists |
| DC-R4 | docs | `mkdocs.yml` exists at the layout-appropriate location |
| DC-R5 | docs | `mkdocs.yml` uses `material` theme |
| IA-R1 | installer assets | Plugin manifests (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `gemini-extension.json`) reference layout-appropriate asset paths |
| IA-R2 | installer assets | OpenCode plugin lives at the layout-appropriate location (`.opencode/` legacy or `.geno/plugins/opencode/` namespaced) |
| IA-R3 | installer assets | Codex marketplace listing lives at the layout-appropriate location (`.agents/` legacy or `.geno/plugins/codex-agents/` namespaced) |
| RH-R1 | hygiene | `README.md` exists |
| RH-R2 | hygiene | `LICENSE` file exists |
| RH-R3 | hygiene | Repo directory name matches `geno-*` convention |
| AL-R1 | agent-agnostic | Body text uses agent-neutral phrasing (no "Claude Code only" framing) |
| AL-R2 | agent-agnostic | Prerequisites list supported CLIs generically |
| IC-R1 | install compliance | No file contains `npx skills add` as a user-facing install instruction |
| IC-R2 | install compliance | Install instructions reference the canonical install resource-script path |
| EF-R1 | freshness | Installed copy is on latest main |
| EF-R2 | freshness | `main` worktree has clean working tree |
| CP-R1 | prefix aliasing | No file contains aliased slash command references in body content |

## Info (advisory)

| ID | Domain | Check |
| ---- | -------- | ------- |
| LV-I1 | layout | Layout in use (legacy / namespaced) — surfaced in the report header |
| VR-I1 | versioning | Skills added/removed since last git tag — version bump may be warranted |
| MF-I1 | manifest | If `pyproject.toml` exists, `project.name` matches the manifest name |
| SM-I1 | skills manifest | `skills.sh.json` would change if regenerated — drift detected even if all entries map |
| EF-I1 | freshness | Current installed revision and date of last main commit (stale > 30 days noted) |
| DC-I1 | docs | `docs/assets/icon.png` exists |
| DC-I2 | docs | `docs/cli-reference.md` exists (if CLI present) |
| DC-I3 | docs | `mkdocs.yml` has `site_url` and `repo_url` configured |
| US-I1 | umbrella | Frontmatter includes `metadata` with `author` and `version` |

## Output format

For each repo audited, emit a summary line then a table grouped by tier:

```text
Audit: geno-{name}    Layout: namespaced
  PASS: NN    FAIL: NN    WARN: NN    INFO: NN

REQUIRED:
  ✓ MF-1  manifest  .geno/geno-tools/genotools.yaml exists
  ✓ AI-2  agent files  CLAUDE.md matches AGENTS.md byte-for-byte
  ✗ SN-2  nomenclature  skills/foo/ missing SKILL.md
  ✗ SM-2  skills manifest  skills/foo/SKILL.md not present in skills.sh.json
  ...

RECOMMENDED:
  ⚠ AI-R10  agent files  .github/workflows/check-claude-md.yml missing
  ...

INFO:
  ℹ LV-I1  layout  namespaced layout in use
  ℹ EF-I1  freshness  install is 47 days behind origin/main
  ...
```

A repo with **zero FAILs** is installable. A repo with FAILs must be fixed before it can pass through the install resource script.
