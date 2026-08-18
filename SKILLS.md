# Skill nesting standard

How skills are laid out in a geno-* skillset repo.

## Layout

```
skills/
  <category>/
    <name>/
      SKILL.md
```

Categories are real directories and may nest **arbitrarily deep**:

```
skills/
  manager/
    install/SKILL.md            -> geno-tools-manager-install
    remove/SKILL.md
  meta/
    harness/
      fork/SKILL.md             -> geno-tools-meta-harness-fork
    ecosystem/
      discover/SKILL.md
```

A single-skill repo may keep a flat `skills/<name>/SKILL.md`, or just a root
`SKILL.md` (the umbrella).

## Rules

1. **Category-XOR-leaf.** Every directory under `skills/` is *either* a category
   (has child skill dirs, **no** `SKILL.md`) *or* a leaf (has `SKILL.md`, no skill
   children) — never both. A dir that is both shadows everything nested under it
   (see Discovery), silently dropping those skills. To give a category its own
   skill, add a leaf child (`vaults/SKILL.md` → `vaults/status/SKILL.md`).

2. **Name mirrors path.** A leaf's frontmatter `name:` is the fully-qualified,
   hyphen-joined path from the skillset name down through the categories to the
   leaf: `skills/meta/harness/fork/` in `geno-tools` →
   `name: geno-tools-meta-harness-fork`. The `name` must be **globally unique**;
   leaf dir names (`install`, `run`) may legitimately repeat across categories,
   the FQ name does not.

3. **Required frontmatter.** `name`, `description`, and a scoped `allowed-tools`
   (no unrestricted `Bash(*)`). Plus `license` + `metadata.{author,version}` per
   repo convention.

## Discovery (`--full-depth`)

geno-tools registers skills with every agent via:

```
npx skills add <skillset> --agent '*' --global --full-depth --yes
```

`npx skills` (vercel-labs) walks only **depth-2** by default
(`skills/<category>/<name>/`); `--full-depth` is required for deeper trees and is
always passed by `geno-tools skills install`/`update`. Discovery stops at the first
`SKILL.md` on a path — the **shadowing** rule that makes category-XOR-leaf
mandatory.

### Portability caveat

`--full-depth` is a vercel-labs `npx skills` feature. Claude Code's *native*
plugin loader reads only one level under a skills root, so a deeply-nested repo
loaded as a raw Claude Code plugin won't surface every skill. **geno-tools (via
`npx skills`) is the supported install path** for nested skillsets.

## Enforcement

`audit/run` (the `geno-tools-audit-run` skill) checks the category-XOR-leaf
invariant, name-mirrors-path, scoped tools, and the monolithic-CLI rule (a CLI
with ≥3 subcommands must expose them as separate skills, not one umbrella).
