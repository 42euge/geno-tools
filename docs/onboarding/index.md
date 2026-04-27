# Onboarding

This section covers everything that happens **before** a skillset is trusted and installed — both on the public side (adding a repo to the geno registry) and on the enterprise side (admitting a skillset to a company's internal namespace).

A skillset can ship arbitrary `SKILL.md` content, slash commands, Python code, and runtime symlinks. The agent will read and act on all of it. Onboarding is the rigor that gates that trust.

## Who this is for

- **Authors** — you wrote a new `{prefix}-{slug}` repo and want it installable by short slug or by URL.
- **Maintainers** — you review PRs that add entries to `genotools/registry.py`.
- **Enterprise platform teams** — you decide which skillsets a company's developers can install internally, and you want a documented bar to check against.

## The two-track flow

| Track | Audience | Trust gate |
|-------|----------|-----------|
| **Public** | Anyone publishing under `geno-*` (or wanting their repo added to the registry) | PR review against the [audit checklist](audit.md) |
| **Enterprise** | Internal skillsets under a company namespace (e.g. `acme-*`) | The same audit checklist, run by the platform team before merging into the company's mirror or registry fork |

The checklist is the same. The reviewer changes.

## Onboarding a public skillset

1. **Author the repo.** Follow [Creating a Skillset](../skillsets/creating.md). Minimum viable: a root `SKILL.md` and a `commands/` directory.
2. **Self-test.** `geno-tools dev <slug> ~/src/<repo>` to install from a local checkout, then exercise every slash command.
3. **Push to a public git remote.** Anyone can already install it via direct URL at this point: `geno-tools install https://github.com/you/your-skillset.git`.
4. **Open a registry PR.** Add `"<slug>": "<git-url>"` to `genotools/registry.py` and the corresponding row to `docs/skillsets/index.md` and the README's existing-repos table.
5. **Pass the audit.** A maintainer runs through [the audit checklist](audit.md) and either approves, requests changes, or closes the PR.
6. **Ship.** Once merged, `geno-tools install <slug>` resolves to your repo for everyone.

## Onboarding an enterprise (private) skillset

The shape is identical, the boundary is internal:

1. **Pick the namespace.** Use your company slug as the prefix — `acme-incident-response`, `acme-finance`, etc. See the [Enterprise pattern](../../README.md#enterprise-private-skillsets-public-tooling) in the README.
2. **Author against the same skillset spec.** No fork of geno-tools needed; the on-disk format is identical to public skillsets.
3. **Host in your private remote.** GitHub Enterprise, GitLab, Bitbucket, internal mirror — anywhere git can clone from.
4. **Run the audit internally.** Use [the audit checklist](audit.md) as your platform team's review template. Treat the result as a sign-off artifact.
5. **Distribute.** Either:
    - **Direct URL** — developers run `geno-tools install git@github.acme.com:platform/acme-finance.git`, or
    - **Forked registry** — maintain an internal fork of `genotools/registry.py` (or a thin wrapper) that lists your approved internal slugs.

## What "onboarded" means in practice

A skillset is considered onboarded when:

- The audit checklist has been completed and signed off.
- The repo is reachable from the install path the audience uses (public registry / direct URL / internal mirror).
- The agent integrations have been verified end-to-end on at least one supported CLI (Claude Code, Codex, Cursor, Gemini CLI, OpenCode).
- A clear point of contact is listed in `SKILL.md` metadata.

Anything short of that is "experimental" — fine for `geno-tools dev` and direct-URL installs, not yet fit for the curated registry or an enterprise's approved list.
