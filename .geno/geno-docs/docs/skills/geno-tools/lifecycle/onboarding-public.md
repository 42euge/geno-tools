---
title: geno-lifecycle-onboarding-public
description: Discover existing `geno-*` repos under the user's GitHub account, or guide them through creating one, then admit it to the public registry.
---

# geno-lifecycle-onboarding-public

`/geno-lifecycle-onboarding-public`

> Onboard a user's `geno-*` repo into the curated public registry — either by discovering repos that already exist on their GitHub account, or by helping them bootstrap a new one from scratch.

For internal/private skillsets that live behind an enterprise git host, see [`onboarding-enterprise`](onboarding-enterprise.md).

## Two entry points

The skill opens by asking whether the user already has a `geno-*` repo or needs to start one.

### Branch A — Discover existing repos

Scans the user's GitHub account for `geno-*` repos and surfaces qualifying candidates.

1. Confirm the GitHub identity (default to `gh auth status`).
2. Add a public-GitHub discovery source pointed at the user's account with `prefix: geno-`.
3. Dry-run discovery (`discover.sh --dry-run`) and filter to qualifying repos.
4. Pick one to admit.

### Branch B — Create a new repo

Hands off to `/geno-lifecycle-repo-create` when the user has no qualifying repo yet.

1. Pick a slug.
2. Scaffold via `/geno-lifecycle-repo-create`.
3. Push to a public remote.
4. Continue with the admit flow.

## Admit flow

1. Verify repo shape — `SKILL.md` + `skills/` at root.
2. Self-test locally — `install.sh /path/to/local/checkout`.
3. Walk the audit checklist (`docs/onboarding/audit.md`).
4. Open the registry PR adding `"<repo-name>": "<git-url>"` to `skills/geno-tools/lib/registry.sh`.
5. Merge → `install.sh <repo-name>` works for everyone.

## See also

- Source: `skills/lifecycle/skills/onboarding-public/SKILL.md`
- Reviewer checklist: [audit checklist](../../../onboarding/audit.md)
- Full onboarding flow: [onboarding overview](../../../onboarding/index.md)
- Repo scaffold: `/geno-lifecycle-repo-create`
