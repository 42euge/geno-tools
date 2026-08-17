# geno-tools — what it does, and how

> Review doc. Answers two questions: *if `npx skills` installs skills, what is
> this repo for?* and *how does it actually handle everything else?*
> Written 2026-08-17 against branch `merge-geno-iso` (v0.7.0).

---

## The one-line answer

**`npx skills` registers skill *files*. geno-tools manages everything that isn't a file.**

`npx skills` is a **dependency, not a competitor** — geno-tools calls it for the
registration step and owns the layer above it.

```
npx skills  →  registers SKILL.md into agent dirs (all ~76 agents)
geno-tools  →  resolve (deps, variants, MCP) · scope (profiles) · launch (containers)
geno-iso    →  the enforcement runtime (folded into geno_tools/iso/)
```

---

## Part 1 — What geno-tools does that `npx skills` cannot

Verified against `skills@1.5.21` (see `docs/npx-skills-dependencies.md`).

| # | Capability | Why npx can't | Strength |
|---|---|---|---|
| 1 | **Provisions shipped code** — venv + CLI binaries on PATH | npx only copies/symlinks `SKILL.md`; never creates venvs or PATH entries | **Strongest.** Structural. |
| 2 | **Profiles + launch** — per-invocation scoped container | No per-CLI notion, no per-invocation notion, no MCP concept | **Strongest.** The new capability. |
| 3 | **Dependency resolution** — transitive `requires:` | No dependency field in its parser; `skills-lock.json` is a restore lock, not a dep graph | Solid |
| 4 | **Variant pinning** — fork/use/promote | No equivalent | Solid |
| 5 | **MCP catalog resolution** — names → server specs | No MCP concept at all | Solid |
| 6 | **Version + drift tracking** | No pinning or drift concept | Thin |
| 7 | **Audit / authoring / uninstall** | Validates frontmatter only | Thin |

**Concrete example (#1):** `geno-tt` ships a real CLI (`tt`).
`geno-tools install geno-tt` → clone, venv, `tt` on PATH, *then* hands
registration to npx. `npx skills add` alone leaves it half-installed.

---

## Part 2 — How each piece works

### Install / provisioning — `commands.py:325` (`_install_one`)

Ordered pipeline:

1. **Clone** bare → `~/.geno-tools/geno-<name>/.git`, then a `main/` worktree
2. **Recurse `requires:`** from `genotools.yaml` — deps first, circular-dep detection
3. **Create venv** from the skillset's own `pyproject.toml` → `venvs/default/`
4. **Symlink console scripts** into `~/.local/bin` — skips if target exists (won't clobber)
5. **Flip `active -> main`**
6. **Hand registration to `npx skills`** — ONE `--full-depth` call over the skills tree

**Rollback:** any exception → the whole skillset dir is `rmtree`'d. No half-installs.

### On-disk layout — `paths.py` (66 lines)

```
~/.geno-tools/geno-<name>/
├── .git/              bare repo
├── main/              primary worktree
├── .worktrees/<v>/    variant worktrees
├── venvs/<name>/      per-skillset (or per-variant) venv
└── active -> main     what's live; `use` repoints this
```

All path construction is centralized here — no other module hardcodes paths.
That's *why* `uninstall` could enumerate the full footprint reliably.

### Variants — worktree + one symlink

- `fork` → `git worktree add -b <variant>`; `--isolated-venv` for separate deps
- `use` → unlink/relink `active`, then re-register. npx reads *through* `active`,
  so the symlink flip alone surfaces the variant's skills
- `promote` → `git merge --ff-only`, guarded on a dirty tree

### Profiles → launch — `profiles.py` + `mcp.py` + `iso/`

`resolve(name)` lowers a profile to a concrete plan:
- each skill → its **variant's worktree path**
- uninstalled skillsets → collected under `missing`
- MCP catalog names → passed through for `mcp.py` to turn into specs

`launch` then: generate `.mcp.json` → `geno-iso run --profile bare` →
**bind-mount each variant worktree** into the container's skills path.
Hard-requires the container runtime; **no host fallback**.

### MCP catalogs — `mcp.py` (168 lines)

Provider registry mirroring `discovery.py`. Public repo ships **generic
providers only** (`file`, `env`). A private catalog self-registers by dropping
`mcp_provider.py` into an installed skillset's `active/` dir, which `mcp.py`
imports on demand — so proprietary URLs/auth never enter this repo.
**Enforced by a CI grep test** (no `blue`/`leap`/`okta` in `geno_tools/**`).

### Discovery — `registry.py` + `discovery.py`

- `registry.py` (162) — unauthenticated GitHub API scan of `42euge`, cached to
  `~/.geno/registry.json`, 30-min staleness
- `discovery.py` (529) — pluggable providers: github / gitlab / bitbucket /
  gitea / community, plus confluence / gitlab-wiki; `prefix` + `auth_env` for
  private orgs

### Observability — `trace.py` (426, separate `geno-trace` binary)

Append-only JSONL → `~/.geno/traces/YYYY/YYYY-MM.jsonl`, aggregated into
per-skill health cards; unhealthy skills land in a retro queue. Driven by a
SessionStart hook.

### Config — `config.py` (175)

`~/.geno/config.yaml`, shallow-merged against `_DEFAULTS`. **Secrets never live
there** — `llm.token` routes to `~/.geno/settings.json`.

> ⚠️ Gotcha: `load()` **silently drops unknown top-level keys**. Adding
> `profiles` / `mcp_catalogs` required editing `_DEFAULTS` too, or they vanish.

### The rest

| Module | Role |
|---|---|
| `audit.py` (126) | FAIL/WARN/INFO compliance: version parity, nesting standard, umbrella, monolithic-CLI rule |
| `docs.py` (548) + `scripts/compile_skill_docs.py` (1186) | SKILL.md → MkDocs pages |
| `llm.py` (260) | Model benchmarking; `llm suggest` feeds `tt name -i` (stdout contract: bare name, **no newline**) |
| `install-agent` | Writes plugin manifests / drives native plugin CLIs per agent |
| `iso/` (990) | Container runtime: docker lifecycle, credentials, bundled Dockerfiles |

---

## Part 3 — Where it's genuinely weak

Ordered by how much I'd worry about them.

| Issue | Detail |
|---|---|
| **`doctor` is a stub** | Returns `_todo`. The one command meant to verify install health does nothing — a real gap given how much on-disk state exists (symlinks, worktrees, venvs, bin links). |
| **`commands.py` is 1984 lines** | Dispatch + every handler in one file. The obvious refactor target. |
| **Two discovery systems** | `registry.py` vs `discovery.py` with overlapping jobs, plus two `discover` skills. Should be one. |
| **Two docs compilers** | `docs.py` (548) duplicates `scripts/compile_skill_docs.py` (1186). |
| **Shared-venv limitation** | Variants share `venvs/default` unless `--isolated-venv`; bin symlinks always point at `default`. A variant with different deps can clobber main. |
| **`dev` is a stub** | Symlink-a-local-checkout never implemented. |
| **Profiles/launch is lightly exercised** | Newly built, unit-tested, dry-run verified — but no real `launch` against Docker has been run yet. |
| **Per-agent MCP writers unvalidated** | Only claude-code's path is proven; codex (TOML) / cursor (JSON) are best-effort, others stubbed-with-warning. |

### The existential caveat

**If geno skillsets were ever prompt-only** (no shipped binaries), capability #1
evaporates and `npx skills` alone would *nearly* suffice — leaving only
profiles/launch as the justification. **The provisioning layer is what makes
geno-tools necessary rather than merely convenient.**

---

## Part 4 — Open items (from this session's dogfooding)

| Item | State |
|---|---|
| Branch `merge-geno-iso` not pushed | brew/pipx-from-GitHub still resolves 0.6.0, not 0.7.0 |
| `42euge/homebrew-geno` tap ships the **old broken formula** | The rewritten `packaging/geno-tools.rb` lives only in this repo; tap needs syncing |
| npx tries all ~76 agents | `Eve` / `PromptScript` "does not support global install" noise. Fix: scope `--agent` to installed agents |
| 2 pre-existing test failures | `test_session_start_hook_script_exists`, `test_init_script_seeds_config` — reference missing `init-geno-dir.sh` / hook scripts; fail on a clean tree too |
| Theming work | Parked in fork `99de84de`, scoped to geno-tools + geno-tt |

**Test/audit state:** 223 pass, 2 pre-existing failures. Audit: compliant.
Versions aligned at 0.7.0 across all six manifests.
