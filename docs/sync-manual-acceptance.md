# Smoke-test installation sync

This is a short, non-destructive test of `geno-tools sync` between this Mac and
the configured `z2` host. It verifies the real SSH transport and reconciliation
plan without changing installed skillsets.

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

### 3. Preview a push

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

### 4. Confirm that nothing changed

```zsh
geno-tools sync status z2
```

Pass if it reports the same differences as step 2.

Stop after the dry run. The current `geno-dev` installation records a
Mac-local repository path that `z2` cannot clone, so this smoke test does not
run `sync push --yes`.

## Restore the previous CLI

Only run this when testing is finished:

```zsh
pipx uninstall geno-tools
ssh z2 'pipx uninstall geno-tools'
rehash
```

The local `geno-tools` command will then resolve to the existing Homebrew
installation again.
