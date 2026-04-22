# Variants & Worktrees

Variants let you experiment with a skillset without touching the primary install. They use git worktrees under the hood.

## Workflow

```
fork → use → (iterate) → promote or remove
```

### 1. Fork a variant

```bash
geno-tools fork media exp-1
```

This creates:

- A new git branch `exp-1` off `main`
- A worktree at `~/.geno-tools/geno-media/.worktrees/exp-1/`
- Shares the existing venv by default

Add `--isolated-venv` if the variant needs different Python dependencies:

```bash
geno-tools fork media exp-1 --isolated-venv
```

### 2. Activate the variant

```bash
geno-tools use media@exp-1
```

This repoints the `active` symlink from `main/` to `.worktrees/exp-1/`. The target adapter (Claude Code) picks up the change immediately — slash commands and SKILL.md now come from the variant.

#### Cwd-scoped overrides

```bash
geno-tools use media@exp-1 --here
```

With `--here`, the override only applies in the current working directory. Other projects keep using whatever variant was globally active. Useful for testing a variant in one project without disrupting others.

### 3. Iterate

Edit files in the worktree directly. If you used `dev` mode, edits to your local checkout flow through the symlinks automatically.

### 4. Promote or discard

When the variant is ready:

```bash
geno-tools promote media exp-1
```

This merges the `exp-1` branch into `main` locally (no upstream push). The variant worktree stays around until you explicitly remove it.

To discard:

```bash
geno-tools remove media    # removes everything
```

## Multiple variants

You can have multiple variants forked at once. Only one is `active` at a time (globally, or per-cwd with `--here`).

```bash
geno-tools fork media exp-1
geno-tools fork media exp-2
geno-tools use media@exp-2    # switch to exp-2
geno-tools use media@main     # switch back to main
```
