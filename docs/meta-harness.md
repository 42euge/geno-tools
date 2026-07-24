# Meta-harness: fork, use, promote

Skills are prompts and code, and you improve them the way you improve code:
branch, try, measure, merge. But unlike code, a skill is *live in your agent*;
editing it in place means experimenting on the tool you're using to
experiment. The meta-harness gives every skillset a variant mechanism so you
can iterate in isolation and switch instantly, with health data deciding the
winner.

## The disk model

Each installed skillset is a bare repo with worktrees. The `active` symlink is
the single source of truth for which variant your agents see:

```
~/.geno/skillsets/geno-media/
├── .git/                      # bare repo
├── main/                      # primary worktree
├── .worktrees/
│   └── faster-tts/            # one worktree per variant
├── venvs/
│   └── main/                  # shared by default; per-variant if --isolated-venv
└── active -> main             # ← `use` repoints this
```

Because agents resolve skills through `active`, switching variants is one
atomic symlink flip. Nothing is reinstalled or re-registered, and rollback
is instant.

## The loop

### 1. Fork a variant

```console
$ geno-tools fork geno-media faster-tts
forking geno-media @ main → faster-tts
  creating worktree: ~/.geno/skillsets/geno-media/.worktrees/faster-tts
  branch: faster-tts (off main @ 94eba89)
  venv: shared with main (--isolated-venv to split)
forked geno-media faster-tts  (active: main)
```

`fork` never changes what's live. Options:

- `--isolated-venv` — give the variant its own venv; required when the
  experiment changes Python dependencies
- `--from <variant>` — branch off another variant instead of main

Edit the worktree directly, or point an agent session at it; the variant is
a normal git checkout.

### 2. Use it

```console
$ geno-tools use geno-media@faster-tts
  active: main → faster-tts
  installing 7 skill(s) via npx skills (all agents, global)
switched geno-media to faster-tts
```

From this moment every agent session runs the variant, and every skill trace
is tagged with `variant: faster-tts`. That tag is what makes evaluation
possible later.

- `geno-tools use geno-media@main` — instant rollback, same mechanism
- `--here` — activate the variant **for the current project only** (recorded
  in `./.geno/`, overriding the global symlink), so you can trial a risky
  variant on one repo while everything else stays on main

### 3. Evaluate

Work normally for a while. Then let the trace data speak:

```console
$ geno-trace health geno-media-audiobook-create --compare main faster-tts
geno-media-audiobook-create
                     main    faster-tts
  invocations:         41            18
  success rate:       71%           89%
  avg duration:       92s           64s
```

Evaluation reuses the health-card system, sliced by the variant tag.

### 4. Promote or discard

```console
$ geno-tools promote geno-media faster-tts
promoting faster-tts → main (fast-forward)
  active: faster-tts → main
  removed worktree: .worktrees/faster-tts
promoted geno-media faster-tts  (main @ 3f1c2ab)
```

`promote` merges the variant branch into main locally and never pushes.
In `mode: dev`, it offers to open an upstream PR with the health comparison in
the description. Options:

- `--keep` — merge but keep the variant worktree around
- Discarding instead: `geno-tools fork --rm geno-media faster-tts`

### `dev`: a checkout as a variant

`geno-tools dev` is the same mechanism with your own clone as the worktree:

```console
$ geno-tools dev geno-media ~/src/geno-media
linking geno-media dev → ~/src/geno-media
  active: main → dev
linked geno-media dev
```

Your working copy becomes what agents run, and `use geno-media@main`
detaches it instantly. This replaces manual symlinking into agent config
directories.

## Guardrails

- `fork`/`use`/`promote` are **local by design**; only a dev-mode PR ever
  leaves your machine, and only with confirmation.
- `promote` refuses to merge over uncommitted changes in main's worktree.
- `remove --keep-data` preserves `.worktrees/` and `venvs/`, so removing a
  skillset doesn't destroy in-flight experiments.
- If a variant changed dependency declarations, `promote` rebuilds the shared
  venv before flipping `active` back.
