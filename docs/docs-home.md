<div class="hero" markdown>

# geno-<span>tools</span>

The package manager for AI coding agent skillsets.
Install, fork, experiment, promote — as a Claude Code plugin or standalone CLI.

<div class="hero-buttons">
<a href="getting-started/" class="btn-primary">Get Started</a>
<a href="cli-reference/" class="btn-secondary">CLI Reference</a>
</div>

</div>

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
<span class="card-icon">:material-download:</span>

### Install in seconds

Install as a Claude Code plugin or via `pipx`. Short names resolve from a curated registry.

[Get started :material-arrow-right:](getting-started.md)
</div>

<div class="feature-card" markdown>
<span class="card-icon">:material-console:</span>

### Full CLI

`ls`, `install`, `dev`, `fork`, `use`, `promote`, `update`, `remove`, `doctor` — everything you need.

[CLI Reference :material-arrow-right:](cli-reference.md)
</div>

<div class="feature-card" markdown>
<span class="card-icon">:material-puzzle:</span>

### Skillset ecosystem

Media, research, kaggle, agents — each a self-contained repo with a declarative manifest.

[Browse skillsets :material-arrow-right:](skillsets/index.md)
</div>

<div class="feature-card" markdown>
<span class="card-icon">:material-source-branch:</span>

### Variant worktrees

Fork a skillset, experiment in isolation, promote back to main. Git worktrees under the hood.

[Learn more :material-arrow-right:](architecture/variants.md)
</div>

</div>

<div class="quick-taste" markdown>

## Quick taste

=== "Claude Code plugin"

    ```bash
    claude /plugin install 42euge/geno-tools
    pipx install git+https://github.com/42euge/geno-tools

    /gt-ls --available                       # see the registry
    /gt-install geno-<name>                  # install a skillset
    geno-tools fork geno-<name> exp-1        # branch a variant
    geno-tools use geno-<name>@exp-1         # activate it
    geno-tools promote geno-<name> exp-1     # merge back to main
    ```

=== "CLI only"

    ```bash
    pipx install git+https://github.com/42euge/geno-tools

    geno-tools ls --available                # see the registry
    geno-tools install geno-<name>           # install a skillset
    geno-tools fork geno-<name> exp-1        # branch a variant
    geno-tools use geno-<name>@exp-1         # activate it
    geno-tools promote geno-<name> exp-1     # merge back to main
    ```

</div>

## Design principles

:material-file-document-outline: **One manifest**
:   Each skillset declares everything in `genotools.yaml` — deps, scripts, configs.

:material-shield-lock-outline: **Isolated by default**
:   Per-skillset venvs. Git worktrees for variants. Nothing leaks.

:material-undo: **Exact removal**
:   Uninstall replays install in reverse. No orphaned files, ever.

:material-puzzle-outline: **Agent-agnostic**
:   Target adapters for Claude Code, geno-cli, Codex, and Gemini CLI.
