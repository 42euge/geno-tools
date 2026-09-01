# Development

## Run the CLI from this checkout

A Homebrew installation normally resolves to `/opt/homebrew/bin/geno-tools`.
For development, install this checkout in editable mode so source changes are
used without rebuilding the Homebrew formula.

### Repository-scoped override

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

### Persistent editable override

To select this checkout in new shells without activating its virtual
environment each time, install it with pipx:

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
