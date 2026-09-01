# Skillset Compliance Specification

Version: **0.1.0**

Status: **Draft**

This document is the normative checklist for a healthy geno skillset
repository. Human reviews, `geno-tools audit check`, and audit PR agents should
all report the same rule IDs from this specification.

The specification checks ecosystem compatibility and maintainability. It does
not certify that a skillset's runtime code is correct or secure.

## Verdicts

- **PASS** — every required rule passes.
- **FAIL** — one or more required rules fail.
- **WARN** — required rules pass, but one or more recommended rules fail.
- **INFO** — an optional observation that does not affect compliance.

An audit is read-only. Fixing findings and opening a pull request are separate,
explicit actions.

## Canonical repository shape

```text
geno-<name>/
├── AGENTS.md
├── README.md
├── LICENSE
├── SKILL.md -> skills/geno-<name>/SKILL.md
├── genotools.yaml
├── skills/
│   ├── geno-<name>/
│   │   └── SKILL.md
│   └── <additional skill paths>/
│       └── SKILL.md
├── docs/
│   ├── index.md
│   └── getting-started.md
├── mkdocs.yml
└── pyproject.toml              # optional; required only for Python runtimes
```

Nested skill paths are allowed. A directory containing a `SKILL.md` is a leaf:
it must not contain another descendant `SKILL.md`, because the parent shadows
the child during skill discovery.

## Required rules

Any failed item makes the repository non-compliant.

- [ ] **GENO-001 Repository name** — The repository name uses the
  `{namespace}-{slug}` form. Public upstream skillsets use `geno-<slug>`.
- [ ] **GENO-002 Manifest present** — `genotools.yaml` exists at the repository
  root and contains a YAML mapping.
- [ ] **GENO-003 Manifest identity** — `genotools.yaml` contains non-empty
  `name`, `version`, and `description` fields; `name` matches the repository.
- [ ] **GENO-004 Manifest version** — `version` is valid semantic versioning in
  `MAJOR.MINOR.PATCH` form.
- [ ] **GENO-005 Dependencies** — If `requires` is present, it is a list of
  non-empty skillset names with no self-reference.
- [ ] **GENO-006 Manifest paths** — Every source path declared by `config`,
  `runtime`, or another materialized manifest entry exists in the repository.
- [ ] **GENO-007 Version agreement** — Project-level versions in packaging,
  runtime, or umbrella-skill metadata agree with `genotools.yaml`.
- [ ] **GENO-010 Skills present** — `skills/` contains at least one `SKILL.md`.
- [ ] **GENO-011 Valid skill contracts** — Every `SKILL.md` begins with valid
  YAML frontmatter containing non-empty `name` and `description` fields.
- [ ] **GENO-012 Unique skill names** — No two skill contracts declare the same
  `name`.
- [ ] **GENO-013 Umbrella skill** — `skills/<repository-name>/SKILL.md` exists
  and declares the repository name.
- [ ] **GENO-014 Root skill bridge** — Until discovery reads
  `genotools.yaml` directly, root `SKILL.md` is a symlink to the umbrella skill,
  not a divergent copy.
- [ ] **GENO-015 No shadowed skills** — A skill directory containing
  `SKILL.md` has no descendant skill contracts.
- [ ] **GENO-020 Agent instructions** — A non-empty `AGENTS.md` is the single
  repository-level instruction source. Retired `GENO.md`, `CLAUDE.md`, and
  `GEMINI.md` pointer files are absent.
- [ ] **GENO-021 Canonical commands** — Committed skill and documentation text
  uses canonical `/geno-...` command names, never installation-specific aliases
  such as `/gt-...`.
- [ ] **GENO-022 Local state excluded** — `.geno/` and `CLAUDE.local.md` are not
  tracked by Git.

## Recommended rules

Failed items produce warnings but do not make the repository uninstallable.

- [ ] **GENO-101 Trigger descriptions** — Skill descriptions state when the
  skill should be used rather than summarizing its workflow.
- [ ] **GENO-102 Least privilege** — `allowed-tools`, when present, is narrower
  than unrestricted wildcard access wherever practical.
- [ ] **GENO-103 Human documentation** — `README.md` and `LICENSE` exist.
- [ ] **GENO-104 Documentation site** — `docs/index.md`,
  `docs/getting-started.md`, and `mkdocs.yml` exist.
- [ ] **GENO-105 Canonical installation** — User documentation installs through
  `geno-tools install`; it does not instruct users to call `npx skills add`
  directly.
- [ ] **GENO-106 Agent-neutral language** — General descriptions say “coding
  agent” rather than presenting one supported agent as the only runtime.
- [ ] **GENO-107 Runtime tests** — Repositories containing executable code have
  automated tests and a documented way to run them.
- [ ] **GENO-108 CLI skill coverage** — A runtime exposing several distinct CLI
  capabilities provides focused skills rather than one monolithic umbrella
  workflow.
- [ ] **GENO-109 Repository-local guidance** — `AGENTS.md` describes this
  repository without copying ecosystem-wide rules owned by geno-tools.
- [ ] **GENO-110 Contract coherence** — The manifest, skill contracts,
  documentation, and runtime entry points describe the same capabilities and
  invocation model.

## Audit report contract

Every check result must include:

- the stable rule ID;
- `PASS`, `FAIL`, `WARN`, or `INFO` status;
- the affected path, when applicable;
- a concise explanation;
- a concrete remediation.

Machine-readable output must preserve those fields. Text and Rich output may
group findings, but must not change their meaning.

## Transitional rule

`GENO-014` exists because current remote discovery still probes root
`SKILL.md`. Root skill files interfere with ordinary recursive skill discovery,
so geno-tools intends to switch discovery to `genotools.yaml`. When that
migration is complete, this specification should remove `GENO-014` rather than
requiring an obsolete bridge forever.
