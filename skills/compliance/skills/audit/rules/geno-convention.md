# `.geno` Directory Convention

The geno ecosystem uses **three** distinct `.geno` directory contexts. Two of them are runtime/workspace state and must never be committed to git; the third is the *namespaced repo layout* — checked-in source files organized under `.geno/<sub-namespace>/` so the repo root stays minimal and matches the upstream `vendor/vercel-labs/agent-skills` shape.

| Context | Path | Tracked by git? |
|---------|------|-----------------|
| Global runtime | `~/.geno/` | No (lives outside the repo entirely) |
| Workspace runtime | `.geno/.workspace/` (inside any repo or workspace dir) | No |
| Namespaced repo layout | `.geno/geno-tools/`, `.geno/geno-specs/`, `.geno/geno-docs/`, `.geno/plugins/` | **Yes** |

The first two are machine-local, user-specific, transient. The third is the canonical place a geno-* repo puts its source-controlled internal machinery.

## Global — `~/.geno/`

The global `.geno` directory at `~/.geno/` is the ecosystem-wide root. It contains shared infrastructure and per-project state that persists across workspaces:

```text
~/.geno/
├── config.yaml                    # ecosystem-wide settings
├── agents/                        # agent registration and presence
├── sessions/                      # session history
├── messages/                      # inter-agent messages
├── bin/                           # symlinked CLI binaries
├── venv/                          # shared Python environments
└── geno-{name}/                   # per-skillset state
    ├── .git/                      # bare repo
    ├── main/                      # primary worktree
    ├── .worktrees/<variant>/      # additional worktrees
    ├── venvs/<venv-name>/         # isolated Python envs
    └── active -> main             # symlink to active variant
```

This is where the install resource script clones repos, creates venvs, and materializes bin symlinks. Other ecosystem tools also keep state here — `geno-notes` stores the global task journal at `~/.geno/geno-notes/`, `geno-agents` stores registration data at `~/.geno/agents/`, etc.

## Workspace runtime — `.geno/.workspace/`

Per-workspace runtime state lives under `.geno/.workspace/` inside the workspace dir. This is **not committed**.

```text
.geno/.workspace/                  # workspace metadata (managed by geno-dev-workspaces-init)
├── workspace.yaml                 # slug, status, repos, color, ticket
└── worktrees/                     # local worktree checkouts
    └── {repo}/{branch}/           # one per active worktree
```

Tools may also create per-tool runtime state under `.geno/<tool>/` *inside a workspace dir* (not inside a repo) — for example `geno-notes` writes per-project tasks to a workspace's `.geno/geno-notes/`. Workspace-scoped tool state is also untracked.

## Namespaced repo layout — `.geno/<sub-namespace>/`

Inside a `geno-*` *repo* (not a workspace), the `.geno/` directory holds checked-in source files organized by sub-namespace. This keeps the repo root minimal and parallels `vendor/vercel-labs/agent-skills` so external consumers can find the canonical entry points (`AGENTS.md`, `CLAUDE.md`, `README.md`, `skills.sh.json`, `package.json`) without wading through internal machinery.

```text
geno-{name}/                       # repo root — vendor-style minimal surface
├── AGENTS.md                      #   source of truth (Codex reads this)
├── CLAUDE.md                      #   literal copy of AGENTS.md (CI-enforced)
├── GEMINI.md                      #   standalone Gemini context
├── README.md
├── LICENSE
├── skills.sh.json                 #   canonical Vercel-schema skills manifest
├── package.json
├── gemini-extension.json
├── skills/                        #   skill definitions + resource scripts
└── .geno/                         #   internal machinery, namespaced
    ├── geno-tools/                #     installer assets
    │   ├── genotools.yaml         #       install manifest
    │   ├── scripts/bootstrap.sh
    │   ├── hooks/hooks.json
    │   └── config/defaults.yaml
    ├── geno-specs/                #     strategic docs
    │   ├── VISION.md
    │   ├── TENETS.md
    │   └── .specs/                #       drafts, feature specs
    ├── geno-docs/                 #     mkdocs site
    │   ├── mkdocs.yml
    │   └── docs/
    └── plugins/                   #     vendor-specific plugin sources
        ├── opencode/              #       was .opencode/
        └── codex-agents/          #       was .agents/
```

Sub-namespace directories under `.geno/` ARE committed to git (unlike `.geno/.workspace/`). The audit treats `.geno/<sub-namespace>/` as repo source for every check that traverses `.geno/`.

A repo's `.gitignore` should ignore `.geno/.workspace/` specifically, not the entire `.geno/` directory — ignoring the whole `.geno/` would untrack the namespaced source files.

## Audit checks

**Required:**

- `.geno/.workspace/` is not tracked by git (checked via `git ls-files .geno/.workspace/`)
- `CLAUDE.local.md` is not tracked by git
- If a `.geno/` directory exists in the repo and contains anything other than `.workspace/`, those sub-namespace dirs (`geno-tools/`, `geno-specs/`, `geno-docs/`, `plugins/`) ARE tracked

**Recommended:**

- Project `.gitignore` ignores `.geno/.workspace/` (specific path), not the whole `.geno/`. Ignoring the whole directory would orphan the namespaced source files.
- Global gitignore (`~/.config/git/ignore`) includes `CLAUDE.local.md`. The global gitignore should NOT have a blanket `.geno/` rule — that would untrack the namespaced source files in every geno-* repo.
