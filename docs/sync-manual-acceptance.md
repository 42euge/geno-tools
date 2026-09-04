# Smoke-test installation sync

This is a short end-to-end test of `geno-tools sync` between this Mac and the
configured `z2` host. It updates the stable local skillset sources, installs
the same skillsets on `z2`, pushes portable configuration, and verifies that
the two installations converge.

## One-time installation

Run these commands from the geno-tools feature checkout. For the current test,
this setup has already been completed.

```zsh
pipx install --force --editable .
rehash
ssh z2 \
  'pipx install --force "git+https://github.com/42euge/geno-tools.git@feat/installation-sync"'
```

The editable pipx installation puts this checkout at
`~/.local/bin/geno-tools`, ahead of the Homebrew installation, so the normal
`geno-tools` command works without activating `.venv`.

Confirm that both machines expose the sync command:

```zsh
geno-tools --version
geno-tools sync --help
ssh z2 'geno-tools --version && geno-tools sync --help'
```

## Run the smoke test

### 1. Export both installations

```zsh
geno-tools sync export | python3 -m json.tool
ssh z2 'geno-tools sync export' | python3 -m json.tool
```

Pass if both commands print JSON with `"version": 1`, a machine name, and a
`skillsets` object.

### 2. See the current differences

```zsh
geno-tools sync status z2
```

Pass if the command reaches `z2` and reports the differences. With the current
installations, the report should include:

```text
z2:
  geno-dev: extra-here
  geno-tt: extra-here
```

Configuration differences may also be listed. `extra-here` means the skillset
exists on this Mac but not on `z2`.

### 3. Prepare cloneable source skillsets

Confirm that both stable managed worktrees are clean:

```zsh
git -C "$HOME/.geno-tools/geno-dev/main" status --short
git -C "$HOME/.geno-tools/geno-tt/main" status --short
```

Pass if neither command prints anything. Stop and resolve any reported changes
before continuing.

The current stable `geno-dev` installation records a Mac-local repository and
a feature branch. Point its stable copy at the canonical repository and switch
it to `main`, then update both stable skillsets to their branch tips:

```zsh
git -C "$HOME/.geno-tools/geno-dev/main" remote set-url origin \
  https://github.com/42euge/geno-dev.git
git -C "$HOME/.geno-tools/geno-dev/main" switch main
git -C "$HOME/.geno-tools/geno-dev/.git" symbolic-ref HEAD refs/heads/main
geno-tools update geno-dev
geno-tools update geno-tt
```

These commands change only the managed stable copies. They do not deactivate
the local geno-tools dev checkouts.

Verify that the exported sources are now portable:

```zsh
geno-tools sync export | python3 -m json.tool
```

Pass if both `geno-dev` and `geno-tt` use GitHub URLs and the `main` branch.

### 4. Remove the old remote runtime and preview the push

`z2` currently exposes `tt` through a standalone pipx installation. Remove it
so sync can install the managed `geno-tt` runtime without an executable-name
collision:

```zsh
ssh z2 'pipx uninstall geno-tt'
```

Now preview the complete reconciliation:

```zsh
geno-tools sync push z2 --dry-run
```

Pass if the plan includes:

```text
  would install geno-dev
  would install geno-tt
  would apply config
```

The order may differ. A dry run does not install, update, remove, or configure
anything.

### 5. Push the skillsets and configuration

```zsh
geno-tools sync push z2 --yes
```

Pass if the command exits zero and finishes with these actions:

```text
  install geno-dev
  install geno-tt
  apply config
```

Package installation and skill-registration output will appear before this
summary.

### 6. Verify convergence

```zsh
geno-tools sync status z2
ssh z2 'geno-tools status'
ssh z2 'command -v tt && tt --version'
geno-tools dev status
```

Pass if sync status reports `z2: in sync`, remote status lists `geno-dev` and
`geno-tt` as stable installed skillsets, and remote `tt` resolves successfully.
The final command must still show the Mac's existing dev activations.

## Restore the previous CLI

Only run this when testing is finished:

```zsh
pipx uninstall geno-tools
ssh z2 'pipx uninstall geno-tools'
rehash
```

The local `geno-tools` command will then resolve to the existing Homebrew
installation again.
