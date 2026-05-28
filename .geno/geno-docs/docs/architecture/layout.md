# Disk Layout

All geno-tools state lives under `~/.geno-tools/`.

## Top-level structure

```
~/.geno-tools/
├── .state-hash                    # bumped on any state change
├── geno-bootstrap/                # meta-plugin geno-tools owns
└── geno-{name}/                   # one per installed skillset
    ├── .git/                      # bare repo
    ├── main/                      # primary worktree
    ├── .worktrees/<variant>/      # additional worktrees (via fork)
    ├── venvs/<venv-name>/         # isolated Python environments
    └── active -> main             # symlink; repointed by `use`
```

## Why repos sit under `.git/` + `main/`

Each skillset uses a bare git repo (`.git/`) with worktrees. The primary checkout lives at `main/`, not at the skillset root. This keeps worktrees, venvs, and configs cleanly separated from the source tree.

## The `active` symlink

The `active` symlink always points to the currently selected worktree. By default it points to `main/`. When you `geno-tools use media@exp-1`, it repoints to `.worktrees/exp-1/`.

Target adapters read from wherever `active` points, so switching variants takes effect immediately.

## Venvs

Venvs live at `geno-{name}/venvs/<venv-name>/`. By default, all worktrees share the same venv. Use `--isolated-venv` on `fork` to create a separate one for a variant.

## Config persistence

Copy-once configs live at `geno-{name}/configs/`. They're only created if missing — updates and reinstalls never overwrite user edits. `remove --keep-data` preserves this directory.

## State hash

The `.state-hash` file at the root is bumped whenever geno-tools modifies state. External tools can watch this file to detect changes without scanning the full tree.
