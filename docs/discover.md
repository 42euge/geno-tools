# Discover: finding skillsets

`discover` aggregates every source you configure into one installable list.
Four kinds of source:

| Kind | What it scans | Trust default |
|------|---------------|---------------|
| `registry` | The curated geno registry (public `geno-*` repos with a root `SKILL.md`) | trusted |
| `github` / `gitlab` / `bitbucket` / `gitea` | An org or group you name, matched by prefix | trusted |
| `skills-directory` | The open skills ecosystem (`npx skills`, agentskills format) | untrusted |
| any git URL | Passed directly to `install`; never listed, always resolvable | untrusted |

## Basic use

```console
$ geno-tools discover
geno-tools
── discover · 19 ───────────────────────────────
  Core Framework
    geno-audit     https://github.com/42euge/geno-audit.git
    geno-iso       https://github.com/42euge/geno-iso.git
  Developer Tools
    geno-loops     ✓ installed
    geno-dev       https://github.com/42euge/geno-dev.git
  ...
```

Results cache for 30 minutes; `--refresh` forces a rescan.

## Configuring sources

```yaml
# ~/.geno/config.yaml
discovery:
  sources:
    - kind: github
      org: 42euge              # public geno-* repos
    - kind: gitlab
      group: platform/skillsets
      base_url: https://gitlab.acme.com
      prefix: acme-            # private namespace
      auth_env: ACME_GITLAB_TOKEN
    - kind: skills-directory   # the open skills ecosystem
```

A repo qualifies when its name matches the source's prefix and it has a root
`SKILL.md`.

## The open skills ecosystem

geno-tools speaks the same `SKILL.md` convention as `npx skills`
(agentskills format), so anything published in that ecosystem installs here
too. With a `skills-directory` source configured:

```console
$ geno-tools discover --from skills
geno-tools
── skills directory · 2,140 ────────────────────
  anthropics/skills          412 ★   docx, pdf, xlsx, artifacts …
  obra/superpowers            34 skills
  vercel-labs/agent-skills    28 skills
  ...
```

Install by ecosystem ref:

```console
$ geno-tools install skills:obra/superpowers
installing ext-superpowers from skills:obra/superpowers
  trust: skills ref (untrusted) — full audit
  audit: compliant · 3 WARN
  installing 34 skill(s) via npx skills (all agents, global)
installed ext-superpowers
```

External packs are untrusted by default, so they get the full
[trust gate](trust-and-audit.md). Packs that need format conversion go
through [absorption](absorption.md) automatically; packs already in
agentskills format install as-is with a generated manifest shim.
