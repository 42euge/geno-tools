# Test installation sync with z2

Run this from the `geno-tools` feature checkout. It installs the branch as the
normal `geno-tools` command on both machines; no virtualenv activation, Git
remote changes, checkout cleanup, or old-runtime removal is required.

## Install and verify

```zsh
pipx install --force --editable .
rehash
ssh z2 \
  'pipx install --force "git+https://github.com/42euge/geno-tools.git@feat/installation-sync"'
geno-tools --version
ssh z2 'geno-tools --version'
```

Both version commands must succeed.

## Run the three checks

```zsh
geno-tools sync push z2 --dry-run
```

For the first active skillset, use the arrow keys to choose **Dev for all
remaining**. The preview should list the Stable installs or updates and
`would activate-dev` for the active skillsets. Nothing is transferred or
changed during the preview.

```zsh
geno-tools sync push z2 --yes
```

Choose **Dev for all remaining** again. The command sends each selected dirty
Dev snapshot, installs its Stable fallback, rebuilds the remote runtime, and
activates the snapshot. It should exit successfully.

```zsh
geno-tools sync status z2
```

Pass when the final output is:

```text
z2:
  in sync
```

If a prompt is not wanted, add `--dev-source active` to either push command.
