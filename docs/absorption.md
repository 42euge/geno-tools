# Absorption: one format for every skill system

The agent-skills world is fragmented: [vercel-labs/skills](https://github.com/vercel-labs/skills)
repos, [obra/superpowers](https://github.com/obra/superpowers) packs, Ralphy
Loop plugins, ad-hoc `.claude/skills/` folders. Each has its own layout,
metadata, and install story, and none of them get venvs, health tracking,
variants, or an audit gate.

**Absorption** converts any of them into a normal geno skillset. After
absorption they are ordinary skillsets: the same install, gate, harness,
and removal.

## Absorbing a repo

```console
$ geno-tools absorb https://github.com/obra/superpowers
absorbing ext-superpowers from https://github.com/obra/superpowers
  format: superpowers pack (34 skills)
  converting: 34 SKILL.md files (frontmatter normalized)
  writing: genotools.yaml (provenance block), AGENTS.md (skills table)
  audit: compliant · 3 WARN
  installing 34 skill(s) via npx skills (all agents, global)
installed ext-superpowers  (absorbed from obra/superpowers @ 8c41f2d)
```

What happens:

1. **Detect** — format adapters probe the repo (superpowers pack, vercel
   skills repo, Ralphy Loop plugin, bare `.claude/skills/` folder). Adapters
   are pluggable the same way discovery providers are.
2. **Convert** — a shim repo is generated: every skill normalized to a
   `SKILL.md` with standard frontmatter, plus `genotools.yaml` and `AGENTS.md`.
   Upstream files are vendored unmodified; normalization lives alongside,
   so upstream diffs stay reviewable.
3. **Gate** — the converted repo goes through the full
   [trust & audit gate](trust-and-audit.md). Absorbed code is the *least*
   trusted input in the system; it gets the strictest scan.
4. **Install** — from here it is an ordinary skillset under
   `~/.geno/skillsets/`.

## Provenance

The conversion is recorded in the manifest, so an absorbed skillset always
knows where it came from:

```yaml
# genotools.yaml (generated)
name: ext-superpowers
version: 2024.11.0
absorbed:
  from: https://github.com/obra/superpowers
  format: superpowers
  commit: 8c41f2d
  adapter: 0.3.0
```

That block is what makes updates work: `geno-tools upgrade ext-superpowers`
fetches upstream, re-runs the same conversion, re-audits the diff, and
applies it, so upstream changes flow through the gate like any normal
skillset update. If the adapter can no longer convert cleanly (upstream
restructured), the upgrade stops and says so instead of guessing.

## Your controls

| Control | Effect |
|---------|--------|
| `--dry-run` | Print the full mapping report (every source file → target skill, every frontmatter transformation) and write nothing |
| `--prefix <p>` | Namespace for absorbed skillsets (default `ext-`); keeps them visually distinct from native `geno-*` / `acme-*` repos |
| `--skills a,b` | Absorb a subset instead of the whole pack |
| `policy.gate` | Absorbed repos obey the same [gate policy](trust-and-audit.md#your-policy); there is no absorb-specific bypass |
| `geno-tools remove ext-superpowers` | Absorption adds no removal special-cases |

Because absorbed skillsets are normal skillsets, everything else composes for
free: fork a variant of an absorbed pack, trial it with `use --here`, track
its health cards, and `promote` your fixes. Your edits sit next to the
vendored files rather than tangled into them, so you can send fixes
upstream in the original format.
