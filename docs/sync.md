# Synchronize installations across computers

`geno-tools sync` reproduces Stable skillset installations, portable
configuration, and selected active Dev checkouts across hosts already
configured in geno-tt.

## Use it

```zsh
geno-tools sync status [host...]
geno-tools sync push HOST --dry-run
geno-tools sync push HOST --yes
geno-tools sync pull [HOST] --dry-run
geno-tools sync pull [HOST] --yes
```

`pull` without a host uses `sync.primary`:

```zsh
geno-tools config set sync.primary lab
```

Push and pull ask separately for each active Dev skillset. Choose its **Dev
snapshot**, its **Stable fallback**, Dev for all remaining, Stable for all
remaining, or Cancel. `--dev-source active|stable` makes the same choice
without prompts. Non-interactive commands must supply that option.

Dry runs make the choices and compare inventories but do not send snapshot
data or apply changes. `--yes` approves removals and transfers over 100 MiB;
without it, a large transfer gets its own confirmation.

## What is reproduced

- Stable repository URL, branch, version, runtime, and registered skills;
- selected Dev `HEAD`, including unpublished commits;
- staged changes, separate unstaged changes, tracked deletions, executable
  modes, safe symlinks, and non-ignored untracked files;
- the portable `aliases`, `discovery`, `autonomy`, and `mode` settings.

Ignored files and untracked common secret, venv, and cache paths are excluded,
as are Git administration data, credentials, endpoints, and machine-local
profiles. Snapshot paths differ between machines; status compares their
content fingerprints.

The receiving machine always installs the Stable fallback before activating a
Dev snapshot. Therefore:

```zsh
geno-tools dev deactivate NAME  # restore Stable
geno-tools dev rollback NAME    # restore the selection replaced by sync
```

A failed snapshot is validated before activation and leaves the current active
selection in place. Independent failures are reported together, and rerunning
the same sync is idempotent.

## Setup

Install `geno-tools` on both machines and configure the host once through tt:

```zsh
tt add-host lab buildbox.example.test --user developer
```

No manual Git remote changes, branch switching, worktree cleanup, directory
copying, or old pipx-runtime removal should be part of a normal sync. Managed
stable worktrees remain protected from local edits; dirty active Dev checkouts
are valid sync sources.

See the [z2 smoke test](sync-manual-acceptance.md) for the shortest end-to-end
acceptance flow.
