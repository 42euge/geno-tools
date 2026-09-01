---
name: geno-tools-meta-ecosystem-discover
description: >-
  Discover installable geno-* skillsets and write them to the geno-tools
  registry cache. Use when the user wants to find skillsets, when
  `geno-tools install <name>` reports a name isn't in the registry, or when
  `geno-tools discover` is empty. Read-only — finds repos, never installs.
allowed-tools: "Bash(curl *) Bash(python3 *) Bash(mkdir *) WebSearch Read(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.2.0"
---

# meta/ecosystem/discover — find skillsets, populate the registry

geno-tools is a **meta-ecosystem**: it does not ship a hardcoded list of
skillsets. This skill goes and finds them, then writes a cache the CLI reads.
It uses **only unauthenticated `curl` + web search** — no `gh`, no token, no
MCP — so it works on any machine. It is **read-only**: it discovers and caches,
it never clones or installs (that's `geno-tools install`).

## What to do

### 1. Find the org(s) to scan
Read `~/.geno/config.yaml` → `discovery.sources`; each `{kind: github, org: ...}`
gives an org (default `42euge`, prefix `geno-`).

### 2. List candidate repos (public GitHub API, unauthenticated)
```bash
curl -s "https://api.github.com/users/<org>/repos?per_page=100&type=public"
```
Parse the JSON; keep repos whose `name` starts with the prefix (`geno-`) and
that are not archived. (60 req/hr unauth is ample. If rate-limited, fall back to
**web search** of `github.com/<org>` to enumerate the repos.)

### 3. Keep only real skillsets (top-level SKILL.md)
For each candidate, confirm it exposes a root `SKILL.md`:
```bash
curl -s -o /dev/null -w '%{http_code}' \
  "https://raw.githubusercontent.com/<org>/<name>/HEAD/SKILL.md"
```
`200` → it's a skillset; keep it. Other → drop it.

### 4. Write the registry cache
Write `~/.geno/registry.json` mapping each kept repo to its clone URL:
```json
{
  "geno-loops": {
    "url": "https://github.com/<org>/geno-loops.git",
    "source": "github:<org>",
    "discovered": "<ISO-8601 timestamp>"
  }
}
```
Use the helper so the shape and path stay canonical:
```bash
python3 -c "from geno_tools.skills_manager import registry; registry.write_cache(<dict>)"
```
(or write the JSON directly to `~/.geno/registry.json`).

### 5. Report
Print how many skillsets were discovered and that the user can now
`geno-tools discover` / `geno-tools install <name>`.

## Boundaries
- **Public repos only.** Unauthenticated curl can't see private repos. Private
  skillsets are installed directly by git URL: `geno-tools install <git-url>`.
- **Never installs.** This skill only writes the cache. Installation is always a
  separate, explicit `geno-tools install`.
