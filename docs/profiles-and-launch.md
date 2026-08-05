# Profiles & Launch

A **profile** is a named bundle that scopes **one launched session**: which
skills (at which variant), which MCP servers, and which agents it may target.
`geno-tools launch <agent> --profile <name>` materializes exactly that bundle
into an isolated container — the session sees those skills and MCP servers and
nothing else.

This is the payoff layer. Discovery, install, variants, and MCP catalogs all
feed into it.

## The profile file

Profiles live at `~/.geno/profiles/<name>.yaml`:

```yaml
# ~/.geno/profiles/eng.yaml
agents: [claude-code, codex]     # which CLIs this profile may target
skills:
  - name: geno-notes
    variant: wiki-v2             # pin a forked variant (see Meta-Harness)
  - name: geno-dev               # bare name → the main worktree
mcp: [core, gitlab]              # MCP catalog names (resolved by the adapter)
autonomy: 1                      # optional per-session config override
```

Four **built-in bundles** are available as profiles without a file on disk —
`bare` (nothing but the agent CLI), `base`, `standard`, and `full`. A
same-named file on disk overrides the built-in.

## Working with profiles

```bash
geno-tools profile list                 # built-ins + your on-disk profiles
geno-tools profile create eng --agent claude-code --agent codex
geno-tools profile show eng             # human-readable resolved view
geno-tools resolve eng                  # the resolved plan as JSON (inspection seam)
```

`resolve` is the seam between "what you declared" and "what will be mounted".
It maps each skill to its variant's worktree path and lists the MCP catalog
names to be turned into server specs — with anything not installed collected
under `missing`:

```console
$ geno-tools resolve eng
{
  "name": "eng",
  "agents": ["claude-code", "codex"],
  "skills": [
    {"name": "geno-notes", "variant": "wiki-v2",
     "worktree": "~/.geno-tools/geno-notes/.worktrees/wiki-v2",
     "worktree_exists": true}
  ],
  "mcp": ["core", "gitlab"],
  "missing": []
}
```

## Launch

```bash
geno-tools launch claude-code --profile eng .        # persistent container
geno-tools launch claude-code --profile eng . --rm   # one-shot, removed on exit
geno-tools launch claude-code --profile eng --dry-run
```

`launch` composes the whole stack:

1. **Resolve** the profile → skills at pinned variants + MCP catalog names.
2. **Generate** an `.mcp.json` from the resolved MCP server specs.
3. **Run** a [geno-iso](control-surface.md) container (`--profile bare`), with
   each pinned-variant worktree's `skills/` **bind-mounted** into the
   container's skills path and the generated MCP config injected.

```console
$ geno-tools launch claude-code --profile eng . --dry-run
launch · eng → claude-code
──────────────────────────────────────────────
  container agent  claude
  workspace        .
  mount            …/geno-notes/.worktrees/wiki-v2/skills -> /home/agent/.claude/skills/geno-notes
  mcp servers      core, gitlab
  $ geno-iso run --agent claude --profile bare . --mcp-config …/.mcp.json
```

The subset is **enforced, not hidden**: the container is mounted with only the
profile's skills, so the session cannot see or run anything the profile leaves
out. `launch` hard-requires the container runtime — there is no unenforced host
fallback.

## The MCP catalog adapter

Profiles reference MCP servers by **catalog name** (`core`, `gitlab`, …). The
adapter resolves those names to concrete server specs through pluggable
providers configured under `mcp_catalogs.sources` in `~/.geno/config.yaml`:

```yaml
mcp_catalogs:
  sources:
    - kind: file                 # a local YAML catalog
      path: ~/.geno/mcp-catalog.yaml
    # - kind: bluegt             # a private catalog, provided by a skillset
```

The public tool ships only generic providers (`file`, `env`). A **proprietary
catalog** (private server URLs, auth) never lives in geno-tools: it
self-registers by dropping an `mcp_provider.py` in an installed skillset's
`active/` directory, which `geno-tools` imports on demand. No proprietary
detail touches this repo.

## Variants, restated

A profile pins a skill to a **variant** — a git worktree created with the
[meta-harness](meta-harness.md):

```bash
geno-tools fork geno-notes wiki-v2       # create the variant worktree
geno-tools use geno-notes@wiki-v2        # activate it for normal (non-launch) use
geno-tools promote geno-notes wiki-v2    # ff-merge it back into main
```

When a profile names `geno-notes@wiki-v2`, `launch` bind-mounts *that
worktree* — so a local, even unpushed, variant is exactly what the launched
session runs.
