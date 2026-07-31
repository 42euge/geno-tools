# Install: name, URL, or ecosystem ref

Four ways to install, one pipeline:

```bash
geno-tools install geno-loops                        # registry name (trusted)
geno-tools install https://github.acme.com/x/y.git   # any git URL (untrusted)
geno-tools install skills:obra/superpowers           # skills-ecosystem ref (untrusted)
geno-tools dev geno-media ~/src/geno-media           # local checkout (yours)
```

## What happens

1. Resolve the source (registry → configured sources → URL)
2. Check trust; untrusted sources get the full [gate](trust-and-audit.md)
3. Clone into `~/.geno/skillsets/<name>/` (bare repo + `main` worktree)
4. Create the venv, link runtime scripts onto PATH
5. Register skills with the agents you enabled via `install-agent`
6. Resolve `requires:` dependencies recursively (cycles detected)

A trusted install is fast:

```console
$ geno-tools install geno-loops
installing geno-loops from https://github.com/42euge/geno-loops.git
  trust: registry (trusted) — conventions check · 9 OK
  creating venv: ~/.geno/skillsets/geno-loops/venvs/main
  installing 5 skill(s) via npx skills (all agents, global)
installed geno-loops
```

An untrusted one is gated:

```console
$ geno-tools install https://github.com/someone/sketchy-skills.git
installing sketchy-skills from https://github.com/someone/sketchy-skills.git
  trust: git URL (untrusted) — full audit
  audit: 1 FAIL · 2 WARN — required checks must pass to be installable
  quarantined: ~/.geno/quarantine/sketchy-skills
not installed  (review: geno-tools quarantine ls)
```

Audit results cache per commit SHA. Nothing is re-audited until its content
changes; `upgrade` re-audits only the diff.

## Managing what's installed

```bash
geno-tools status               # versions, drift vs remote
geno-tools upgrade [<name>]     # update one or all
geno-tools deps <name>          # dependency tree
geno-tools remove <name>        # uninstall (--keep-data preserves venvs + variants)
geno-tools doctor               # verify links, venvs, registrations
```
