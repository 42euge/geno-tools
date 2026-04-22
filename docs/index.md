<div class="hero" markdown>

# geno-<span>tools</span>

The package manager for Claude Code skillsets.
Install, fork, experiment, promote — all from one CLI.

<div class="hero-buttons">
<a href="getting-started/" class="btn-primary">Get Started</a>
<a href="cli-reference/" class="btn-secondary">CLI Reference</a>
</div>

</div>

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
<span class="card-icon">:material-download:</span>

### Install in seconds

One `pipx install` and you're adding skillsets. Short names resolve from a curated registry.

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

Media, research, taxes, kaggle, agents — each a self-contained repo with a declarative manifest.

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

```bash
pipx install git+https://github.com/42euge/geno-tools

geno-tools ls --available        # see the registry
geno-tools install media         # install geno-media
geno-tools fork media exp-1      # branch a variant
geno-tools use media@exp-1       # activate it
geno-tools promote media exp-1   # merge back to main
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
:   Target adapters for Claude Code today. Codex and Gemini CLI next.
