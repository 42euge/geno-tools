# `.geno` Directory Convention

Every project in the geno ecosystem uses a two-tier `.geno` directory structure for runtime state, configuration, and tooling data. Neither tier should ever be committed to git — they contain machine-local paths, user-specific config, and transient runtime state that would break on any other machine.

## Global — `~/.geno/`

The global `.geno` directory at `~/.geno/` is the ecosystem-wide root. It contains shared infrastructure and per-project state that persists across workspaces:

```
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

This is where `geno-tools install` clones repos, creates venvs, and materializes bin symlinks. Other ecosystem tools also keep state here — `geno-notes` stores the global task journal at `~/.geno/geno-notes/`, `geno-agents` stores registration data at `~/.geno/agents/`, etc.

## Local — `.geno/`

The local `.geno/` directory at the repo or workspace root holds per-workspace state. It has a fixed structure with a reserved `.workspace/` subdirectory for workspace metadata, and optional `{project-name}/` subdirectories for tools that need local state.

```
.geno/
├── .workspace/                    # workspace metadata (managed by geno-dev-workspaces-init)
│   ├── workspace.yaml             # slug, status, repos, color, ticket
│   └── worktrees/                 # local worktree checkouts
│       └── {repo}/{branch}/       # one per active worktree
└── {project-name}/                # per-tool local state (optional)
    └── ...                        # tool-specific files
```

**`.workspace/`** contains workspace metadata — the `workspace.yaml` (slug, status, repos, color assignment, source ticket) and any worktree checkouts created for repos in this workspace. This is always under `.workspace/` to keep it separate from tool state.

**`{project-name}/`** directories are created by individual tools when they need workspace-scoped state. For example, `geno-notes` may create `.geno/geno-notes/` to store project-scoped tasks and journal entries (as opposed to the global journal at `~/.geno/geno-notes/`). Not every workspace will have these — they appear only when a tool that needs local state is used in that workspace.

## Audit checks

**Required:**
- `.geno/` is not tracked by git (checked via `git ls-files`)
- `CLAUDE.local.md` is not tracked by git

**Recommended:**
- Global gitignore (`~/.config/git/ignore`) includes `.geno/` and `CLAUDE.local.md`. These entries belong in the global gitignore, not in any project's `.gitignore` — adding them to a project's `.gitignore` would leak geno ecosystem artifacts into committed files. The audit should check the global gitignore and suggest adding entries there if missing. Never modify a project's `.gitignore` for geno-specific patterns.
