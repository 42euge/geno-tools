# Dependency support in `npx skills`

Verified against the official `skills` npm package at version **1.5.21**.

## Finding

The normal `npx skills add <source>` flow does **not** implement declarative or
transitive dependencies between skill repositories. A `SKILL.md` can mention
another skill as an instruction-level prerequisite, but the CLI does not install,
lock, validate, or update that prerequisite automatically.

Evidence from the official package:

- The documented `SKILL.md` contract requires only `name` and `description`;
  its only documented optional field is `metadata.internal`. There is no
  dependency field.
- The bundled parser reads `name`, `description`, and `metadata.internal`; it
  contains no handling for `dependencies`, `requires`, or equivalent fields.
- `skills add` resolves one source and selects one or more skills within that
  source. It does not recursively resolve other sources.
- `skills-lock.json` records independently installed skills and their source;
  it is a restoration/update lock, not a dependency graph.
- The well-known discovery schemas list skill artifacts but have no dependency
  relationship.

## Experimental npm path

`skills experimental_sync` scans already-installed top-level packages in
`node_modules` for `SKILL.md` files. Therefore an npm package can use normal npm
`dependencies` to bring another skill-bearing npm package into `node_modules`,
then sync both. Dependency resolution in that arrangement belongs to npm, not
to `skills add`, and the integration is explicitly experimental. It does not
make Git skill repositories transitively installable.

## Practical options

1. Put tightly coupled skills in the same repository and install them together.
2. Install independent repositories explicitly; project-scoped installs are
   recorded together in `skills-lock.json` for restoration.
3. Use a separate stack/bundle manifest and orchestrator when automatic
   cross-repository dependencies are genuinely required.
4. Keep runtime dependencies in their native package manager (`npm`, `uv`,
   `pipx`, Homebrew, and so on), rather than modeling them as skill dependencies.

## Primary sources

- [`skills` repository README — installation and `SKILL.md` format](https://github.com/vercel-labs/skills/blob/main/README.md)
- [`skills@1.5.21` npm artifact](https://www.npmjs.com/package/skills/v/1.5.21)
- Locally inspected official artifact:
  `/Users/eriveraramos/.npm/_npx/ac0ed6aa23b37c1e/node_modules/skills/README.md`
- Locally inspected bundled CLI implementation:
  `/Users/eriveraramos/.npm/_npx/ac0ed6aa23b37c1e/node_modules/skills/dist/cli.mjs`
