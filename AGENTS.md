# geno-tools — Agent-Agnostic Meta Package Manager for AI Coding Agents

`geno-tools` is an agent-agnostic meta package manager for AI coding agents. It discovers skills from open-source and private ecosystems, absorbs external skill systems (Vercel Labs Skills, Superpowers, Ralphy Loop plugins) into a unified framework, and manages their lifecycle across all supported agents (Claude Code, Gemini CLI, Codex, OpenCode, Cursor). A meta-harness layer evaluates and refines skill variations over time, while built-in auditing ensures capabilities evolve safely.

@./.geno/geno-specs/VISION.md
@./.geno/geno-specs/TENETS.md

## Skills

Skills are organized into 6 functional sub-skillsets under `skills/`. The full naming and layout convention is in `.geno/geno-docs/docs/skillsets/upstream-conventions.md`. The canonical machine-readable manifest is `skills.sh.json` at the repo root.

| Skill | Sub-skillset | Slash command |
|-------|--------------|---------------|
| geno-tools | — | — (umbrella) |
| geno-lifecycle | lifecycle | — (sub-umbrella) |
| geno-lifecycle-repo-create | lifecycle | /geno-lifecycle-repo-create |
| geno-lifecycle-skill-create | lifecycle | /geno-lifecycle-skill-create |
| geno-lifecycle-onboarding-public | lifecycle | /geno-lifecycle-onboarding-public |
| geno-lifecycle-onboarding-enterprise | lifecycle | /geno-lifecycle-onboarding-enterprise |
| geno-manager | manager | — (sub-umbrella) |
| geno-manager-install | manager | /geno-manager-install |
| geno-manager-status | manager | /geno-manager-status |
| geno-compliance | compliance | — (sub-umbrella) |
| geno-compliance-audit | compliance | /geno-compliance-audit |
| geno-self | self | — (sub-umbrella) |
| geno-self-update | self | /geno-self-update |
| geno-self-improve | self | /geno-self-improve |
| geno-assets | assets | — (sub-umbrella) |
| geno-assets-icons | assets | /geno-assets-icons |
| geno-config | config | — (sub-umbrella) |
| geno-config-alias | config | /geno-config-alias |

## Repo structure

The root surface mirrors `vendor/vercel-labs/agent-skills`: only AGENTS.md, CLAUDE.md, README.md, the manifest, and the per-ecosystem discovery files live at root. Everything else is folded under `.geno/<sub-namespace>/`.

```
geno-tools/
├── AGENTS.md                      # agent instructions (this file — source of truth)
├── CLAUDE.md                      # literal copy of AGENTS.md (CI-enforced sync)
├── README.md                      # human-facing readme
├── skills.sh.json                 # canonical skills manifest (mirrors Vercel schema)
├── LICENSE
├── package.json                   # npm metadata (OpenCode plugin entry)
├── gemini-extension.json          # Gemini CLI extension descriptor
├── GEMINI.md                      # context file referenced by gemini-extension.json
├── .gitignore
├── skills/                        # skill definitions + bash implementation
│   ├── geno-tools/                #   umbrella + shared bash lib
│   │   ├── SKILL.md
│   │   └── lib/                   #     paths.sh, common.sh, config.sh,
│   │                              #     registry.sh, discovery.sh, load.sh
│   ├── lifecycle/                 #   sub-skillset: skill & skillset authoring
│   │   ├── SKILL.md
│   │   └── skills/
│   │       ├── repo-create/       #     bootstrap a new geno-* repo (+ rules/)
│   │       ├── skill-create/
│   │       ├── onboarding-public/      #     public registry onboarding workflow
│   │       └── onboarding-enterprise/  #     resources/{discover,scan}.sh
│   ├── manager/                   #   sub-skillset: package management of installed skillsets
│   │   ├── SKILL.md
│   │   └── skills/
│   │       ├── install/           #     resources/{install,remove,ls,deps}.sh
│   │       └── status/            #     resources/status.sh
│   ├── compliance/                #   sub-skillset: audit gate
│   │   ├── SKILL.md
│   │   └── skills/
│   │       └── audit/             #     compliance auditor (+ rules/)
│   ├── self/                      #   sub-skillset: geno-tools self-mgmt
│   │   ├── SKILL.md
│   │   └── skills/
│   │       ├── update/            #     resources/update.sh
│   │       └── improve/           #     resources/trace-{emit,list,health,queue}.sh
│   ├── assets/                    #   sub-skillset: generated branding
│   │   ├── SKILL.md
│   │   └── skills/
│   │       └── icons/
│   └── config/                    #   sub-skillset: user personalization
│       ├── SKILL.md
│       └── skills/
│           └── alias/
├── .claude-plugin/plugin.json     # Claude Code plugin manifest
├── .codex-plugin/plugin.json      # Codex CLI plugin manifest
├── .cursor-plugin/plugin.json     # Cursor plugin manifest
├── .github/                       # CI workflows (incl. AGENTS↔CLAUDE drift check)
└── .geno/                         # all internal machinery, namespaced by skillset
    ├── geno-specs/
    │   ├── .specs/                #   draft GOALS / TENETS / VISION fragments
    │   ├── VISION.md
    │   └── TENETS.md
    ├── geno-docs/
    │   ├── mkdocs.yml
    │   └── docs/                  #   MkDocs Material content
    ├── geno-tools/
    │   ├── scripts/bootstrap.sh   #   seeds ~/.geno/config.yaml on session start
    │   ├── hooks/hooks.json       #   Claude Code SessionStart hook
    │   ├── config/defaults.yaml   #   reference config with aliases schema
    │   └── genotools.yaml         #   legacy install manifest (kept for compatibility)
    └── plugins/
        ├── opencode/              #   OpenCode plugin (was .opencode/)
        └── codex-agents/          #   Codex marketplace listing (was .agents/)
```

`CLAUDE.md` is a literal copy of `AGENTS.md`. After editing `AGENTS.md`, run
`cp AGENTS.md CLAUDE.md`. CI enforces sync via `.github/workflows/check-claude-md.yml`.

## Implementation

geno-tools has no Python runtime and no unified CLI binary. Each capability is a
standalone bash script under the relevant sub-skillset's `resources/` directory.
Shared bash helpers (paths, config, registry, discovery providers) live at
`skills/geno-tools/lib/` and are sourced via `lib/load.sh`.

| Capability | Resource script |
|------------|-----------------|
| list installed / available | `skills/manager/skills/install/resources/ls.sh` |
| install | `skills/manager/skills/install/resources/install.sh` |
| remove | `skills/manager/skills/install/resources/remove.sh` |
| dependency tree | `skills/manager/skills/install/resources/deps.sh` |
| update | `skills/self/skills/update/resources/update.sh` |
| status / doctor | `skills/manager/skills/status/resources/status.sh` |
| discover candidates | `skills/lifecycle/skills/onboarding-enterprise/resources/discover.sh` |
| scan into queue | `skills/lifecycle/skills/onboarding-enterprise/resources/scan.sh` |
| trace emit / list / health / queue | `skills/self/skills/improve/resources/trace-*.sh` |

Traces are append-only JSONL at `~/.geno/traces/YYYY/YYYY-MM.jsonl`. Health
cards are aggregated per-skill at `~/.geno/health/<skill>.json`.

## Dependency management

Skillsets declare dependencies via `requires:` in `.geno/geno-tools/genotools.yaml`
(or any `genotools.yaml` at the root of an installed skillset):

```yaml
name: geno-career
requires:
  - geno-notes
  - geno-specs
```

During an install, dependencies are resolved from the registry and installed
recursively before the target skillset. Already-installed deps are skipped.
Circular dependencies are detected and reported.

## Source resolution

`<name|url|path>` resolves in this order:

1. **Registered repo name** — git URL from `skills/geno-tools/lib/registry.sh` (queries `gh` for the `42euge` org with a hardcoded fallback list). Bare slugs (the part after `geno-`) are also accepted.
2. **Existing local directory** — installed from disk.
3. **Git URL** (`http(s)://`, `git@`, or `*.git`) — cloned.
4. **Discovery sources** (`skills/geno-tools/lib/discovery.sh`) — repos found in `~/.geno/config.yaml` `discovery.sources` that match the configured prefix and have a top-level `SKILL.md`.

## Install flow

```
install.sh media
    ├── resolve_source("media")          # registry -> git URL
    ├── clone_and_worktree()             # bare clone + main worktree
    ├── install_requires() (recursive)   # walk genotools.yaml requires:
    ├── create_venv_if_needed()          # venv + pip install deps + editable install
    ├── materialize_bin_symlinks()       # ~/.local/bin/ symlinks to venv binaries
    ├── active -> main symlink
    └── install_skills_via_npx()         # npx skills add (all agents, global)
```

## Per-skillset layout

```
~/.geno-tools/
├── .state-hash                    # bumped on state changes
├── geno-bootstrap/                # meta-plugin geno-tools owns
└── geno-{name}/
    ├── .git/                      # bare repo
    ├── main/                      # primary worktree
    ├── .worktrees/<variant>/      # additional worktrees (via fork)
    ├── venvs/<venv-name>/         # isolated Python env(s)
    └── active -> main             # symlink (variant switching is manual)
```

## Conventions

### Command prefix aliasing

Slash commands in this repo always use the canonical `geno-` prefix (e.g., `/geno-tools-update`, `/geno-audit`). The prefix users actually type at runtime (`/gt-`, `/geno-`, or bare `/`) is a user preference configured in `~/.geno/config.yaml`:

```yaml
aliases:
  command_prefix: "gt"   # gt-install, gt-media-audiobook-create, etc.
```

The prefix is applied at install time by the install script when materializing skills via `npx skills add`. Never hardcode an aliased prefix like `gt-` in SKILL.md descriptions, AGENTS.md, or any committed file. See `.geno/geno-tools/config/defaults.yaml` for the full schema.

### Versioning

The canonical version lives in `.geno/geno-tools/genotools.yaml` (`version` field). The same value must appear in `package.json` (`version`). Bump the version whenever skills are added, removed, or behavior changes. Keep both files in sync.

### Adding a new skill

This repo uses the nested skill tree layout — see `.geno/geno-docs/docs/skillsets/upstream-conventions.md` § Nested skill trees for the rules.

1. Pick a sub-skillset for the new skill (`lifecycle`, `compliance`, `self`, `assets`, `config`) or create a new one. Create a directory under `skills/{sub-skillset}/skills/{leaf}/` named with a bare noun/verb (no `geno-` prefix).
2. Write a `SKILL.md` inside the leaf directory. Frontmatter `name:` is the **fully qualified** name (e.g. `name: geno-self-foo`) — this is the registered skill name regardless of directory shape.
3. Update the parent sub-skillset's umbrella `SKILL.md` (`skills/{sub-skillset}/SKILL.md`) to list the new leaf.
4. Add a row to the skills table in this file.
5. Add the new skill name to the appropriate grouping in `skills.sh.json`.
6. If the skill needs docs, add a page under `.geno/geno-docs/docs/skills/geno-tools/{sub-skillset}/`.
7. Bump the version in `.geno/geno-tools/genotools.yaml` and `package.json`.
8. Run `cp AGENTS.md CLAUDE.md` so the two stay in sync.

### What a skillset repo needs to provide

Minimum viable `geno-{name}` skillset:

```
geno-{name}/
├── AGENTS.md               # agent instructions (source of truth)
├── CLAUDE.md               # literal copy of AGENTS.md
├── README.md
├── skills.sh.json          # canonical skills manifest
├── skills/
│   └── {name}/SKILL.md     # umbrella skill definition
└── .geno/geno-tools/genotools.yaml   # install manifest (name, version, description)
```

### Skill observability contract

Skills may declare an optional `observability` section in SKILL.md frontmatter:

```yaml
observability:
  success_signal: "description of what success looks like"
  failure_signals:
    - "condition that indicates failure"
  knowledge_reads:
    - "what knowledge this skill consumes"
  knowledge_writes:
    - "what knowledge this skill produces"
```

Skills that declare observability should also include a `## Completion` section at the end of their workflow that emits a trace via `skills/self/skills/improve/resources/trace-emit.sh`. This feeds the self-improvement loop (health cards, retro, mining).

## Plugin structure

geno-tools ships platform-specific plugin manifests so it can be installed as a native plugin on each supported CLI. Skills are platform-agnostic; each CLI-specific manifest points at the shared `skills/` directory. Hook discovery uses an explicit `hooks` field in each plugin manifest pointing to `.geno/geno-tools/hooks/hooks.json`.

Skill registration uses `npx skills add <active-worktree> --agent '*' --global --skill '*' --yes`. Uninstall enumerates skills by walking the `skills/` tree at any depth (the bash `walk_skill_dirs` helper in `skills/geno-tools/lib/common.sh`) and calls `npx skills remove` with the frontmatter `name:` of each registered skill.

This absorption layer is what makes geno-tools a meta-harness rather than just a wrapper — external skill systems (Superpowers conventions, Vercel Labs Skills backend) are normalized into the same `SKILL.md` + `skills.sh.json` contract.
