# CLI Reference

All commands are invoked as `geno-tools <command> [options]`.

When geno-tools is installed as a coding agent plugin, the core commands are also available as slash commands: `/geno-tools install`, `/geno-tools remove`, `/geno-tools ls`, `/geno-tools update`. The command prefix is [user-configurable](skillsets/creating.md#command-prefix-aliasing).

## `ls`

List installed skillsets or the available registry. Slash command: `/geno-tools ls`.

```bash
geno-tools ls                # installed skillsets + active variant
geno-tools ls --available    # curated registry
```

**Options:**

| Flag | Description |
|------|-------------|
| `--available` | Show the registry instead of installed skillsets |

---

## `install`

Install a skillset from the registry, a git URL, or a local path. Slash command: `/geno-tools install`.

```bash
geno-tools install geno-<name>
geno-tools install https://github.com/someone/geno-custom.git
geno-tools install ./local-skillset
```

**Source resolution order:**

1. Registered repo name (e.g. `geno-<name>` -> git URL from registry; legacy bare slugs like `media` still resolve)
2. Local directory path
3. Git URL (`https://`, `git@`, or `*.git`)

**Options:**

| Flag | Description |
|------|-------------|
| `--here` | Materialize cwd alias symlinks for this skillset |

---

## `dev`

Symlink a local checkout as the main worktree. For active development on a skillset.

```bash
geno-tools dev geno-<name> ~/src/geno-<name>
```

If the skillset is already installed, it's removed first (configs preserved). The local path becomes a symlink target — edits take effect immediately.

**Arguments:**

| Arg | Description |
|-----|-------------|
| `name` | Full repo name (e.g. `geno-<name>`) |
| `path` | Path to local checkout |

---

## `fork`

Create a variant worktree branched off main. Use this to experiment without touching the primary install.

```bash
geno-tools fork geno-<name> exp-1
geno-tools fork geno-<name> exp-1 --isolated-venv
```

**Arguments:**

| Arg | Description |
|-----|-------------|
| `name` | Full repo name |
| `variant` | Variant ID (becomes the git branch and worktree directory name) |

**Options:**

| Flag | Description |
|------|-------------|
| `--isolated-venv` | Create a fresh venv for this variant instead of sharing |

---

## `use`

Switch the active variant for a skillset.

```bash
geno-tools use geno-<name>@exp-1          # global: repoint active symlink
geno-tools use geno-<name>@exp-1 --here   # cwd-only override
```

**Arguments:**

| Arg | Description |
|-----|-------------|
| `spec` | `<name>@<variant>` format (e.g. `geno-<name>@exp-1`) |

**Options:**

| Flag | Description |
|------|-------------|
| `--here` | Apply as a cwd-only override instead of globally |

---

## `promote`

Merge a variant back into main. Does not push upstream.

```bash
geno-tools promote geno-<name> exp-1
```

**Arguments:**

| Arg | Description |
|-----|-------------|
| `name` | Skillset name |
| `variant` | Variant to merge into main |

---

## `update`

Pull latest changes on the main worktree. Slash command: `/geno-tools update`.

```bash
geno-tools update geno-<name>    # update one
geno-tools update               # update all
```

Skips skillsets in `dev` mode (the source is already live).

**Arguments:**

| Arg | Description |
|-----|-------------|
| `name` | Skillset name (omit to update all) |

---

## `remove`

Uninstall a skillset. Replays the install in reverse — deterministic, no orphaned files. Slash command: `/geno-tools remove`.

```bash
geno-tools remove geno-<name>
geno-tools remove geno-<name> --keep-data
```

**Arguments:**

| Arg | Description |
|-----|-------------|
| `name` | Skillset name |

**Options:**

| Flag | Description |
|------|-------------|
| `--keep-data` | Preserve venvs and worktrees, only remove skill wiring |

---

## `doctor`

Verify that all symlinks, worktrees, and venvs are intact.

```bash
geno-tools doctor
```

Reports any broken links, missing repos, or inconsistent state.
