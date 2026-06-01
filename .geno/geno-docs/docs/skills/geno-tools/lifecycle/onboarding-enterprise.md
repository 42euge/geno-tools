---
title: geno-lifecycle-onboarding-enterprise
description: Discover existing `{company-slug}-*` enterprise prefixes already in use, or guide a platform team through picking a new prefix and bootstrapping the first repo.
---

# geno-lifecycle-onboarding-enterprise

`/geno-lifecycle-onboarding-enterprise`

> Onboard an enterprise namespace into geno-tools — either by discovering `{company-slug}-*` prefixes already configured or detectable on the enterprise git host, or by guiding a platform team through picking a brand-new prefix and bootstrapping the first repo. Supports GitHub Enterprise / GitLab / Bitbucket / Gitea.

For public-registry onboarding for an individual user, see [`onboarding-public`](onboarding-public.md).

## Two entry points

The skill opens by asking whether a `{slug}-*` namespace already exists at the company.

### Branch A — Discover existing prefixes

Read-only check that surfaces what's already wired up.

1. List every `discovery.sources` entry already in `~/.geno/config.yaml` and the prefixes they declare.
2. Dry-run `discover.sh --dry-run` against each source — group output by prefix.
3. If nothing is configured, scan a tentative source with `prefix: ""` to surface common `{slug}-*` patterns the company is already using.
4. Confirm the prefix and lock it into `discovery.sources`.

### Branch B — Create a new prefix

Stand up a brand-new namespace from scratch.

1. Pick a `{company-slug}-` prefix — lowercase, hyphen-separated, unique to the company. Avoid generic words like `corp-` / `internal-`.
2. Pick the host (GitHub Enterprise / GitLab / Bitbucket / Gitea).
3. Scaffold the first repo via `/geno-lifecycle-repo-create`.
4. Configure `discovery.sources` in `~/.geno/config.yaml` with the new `prefix:`, `org:` / `group:`, `base_url:`, and `auth_env:`.
5. Document the prefix, host, and audit owner in the platform-team runbook.

## Discovery configuration

```yaml
discovery:
  sources:
    - kind: github
      org: acme-corp
      base_url: https://github.acme.com/api/v3
      prefix: acme-
      auth_env: ACME_GITHUB_TOKEN
```

- `kind` — provider (`github`, `gitlab`, `gitea`, `bitbucket`)
- `prefix` — only repos whose name starts with this prefix are candidates
- `base_url` — for self-hosted instances; omit for public github.com / gitlab.com
- `auth_env` — environment variable name holding a token; never paste the token itself

## Resource scripts

- `resources/discover.sh` — list candidate skillset repos from configured discovery sources
- `resources/scan.sh` — scan discovery sources and queue uninstalled candidates

## See also

- Source: `skills/lifecycle/skills/onboarding-enterprise/SKILL.md`
- Reviewer checklist: [audit checklist](../../../onboarding/audit.md)
- Full onboarding flow: [onboarding overview](../../../onboarding/index.md)
- Pluggable provider layer: `skills/geno-tools/lib/discovery.sh`
- Repo scaffold: `/geno-lifecycle-repo-create`
