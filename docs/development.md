# Development

## Develop an installed skillset

An installed command such as `tt` normally points into the skillset's stable
runtime under `~/.geno-tools`. Running it from another checkout requires more
than changing directories: source, runtime commands, and registered agent
skills must all select the same checkout.

Use managed dev mode:

```zsh
geno-tools dev activate /absolute/path/to/geno-tt
rehash
geno-tools dev status geno-tt
command -v tt
tt --version
```

geno-tools validates that the checkout belongs to an installed skillset,
creates an isolated editable runtime under that skillset's managed `venvs/`
directory, and switches the active source, console scripts, and agent skill
registrations as one transaction. The checkout does not need a `.venv`, and
you do not need to activate Python in the shell.

After testing, restore the installed stable source and runtime:

```zsh
geno-tools dev deactivate geno-tt
rehash
```

`geno-tools dev status` lists all stable/dev selections. A `DRIFT` result means
the saved selection, active source, or console-script links disagree; activation
and deactivation also roll back their changes if registration fails.

When installation sync replaces a selection, it keeps one rollback slot:

```zsh
geno-tools dev rollback geno-tt
```

`dev status` shows the Stable fallback that `deactivate` restores. A Dev
snapshot received through sync also records its source machine and content
fingerprint. Dirty development checkouts can be pushed or pulled without
cleaning, committing, or publishing them; see [sync.md](sync.md).

## Develop geno-tools itself

### Run the CLI from this checkout

A Homebrew installation normally resolves to `/opt/homebrew/bin/geno-tools`.
For development, install this checkout in editable mode so source changes are
used without rebuilding the Homebrew formula.

#### Repository-scoped test environment

Create the virtual environment once, install the project and test dependencies,
then activate it:

```zsh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
source .venv/bin/activate
rehash
```

The activated environment puts this checkout ahead of Homebrew for the current
shell. Verify the selected executable and version before testing changes:

```zsh
command -v geno-tools
geno-tools --version
geno-tools
```

`command -v` should report a path ending in `.venv/bin/geno-tools`. Run
`deactivate` to return to the Homebrew installation.

#### Install the checkout as the normal command

For manual and remote testing, install this checkout with pipx so no virtual
environment activation is needed:

```zsh
pipx install --force --editable .
rehash
type -a geno-tools
```

This works when `~/.local/bin` appears before `/opt/homebrew/bin` in `PATH`.
`type -a` should list the pipx executable first and the Homebrew executable
after it. The Homebrew installation remains installed as a fallback.

Remove the persistent override with:

```zsh
pipx uninstall geno-tools
rehash
```

## Run the tests

```zsh
pytest -q
```
