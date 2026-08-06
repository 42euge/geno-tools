# geno-tools — First-Run Walkthrough & Refinement Guide

**Purpose:** step into the shoes of a brand-new user installing geno-tools for
the first time, run the whole path end-to-end, and note every place it snags so
you can refine it. This is a *dogfooding script*, not a spec — follow it in
order, and after each step jot what was confusing, broken, or slower than it
should be in the **Refine** box.

The product is now a **control plane**: `resolve · scope · launch`.
`npx skills` does raw registration underneath; geno-tools adds dependency
resolution, variant pinning, MCP catalogs, and per-invocation isolated launches.
The journey below builds up to the payoff — `geno-tools launch <agent>
--profile <name>`.

> **Tip — isolate your test.** So you don't disturb your real `~/.geno` and
> `~/.geno-tools`, run the whole walkthrough under a throwaway HOME:
> ```bash
> export GENO_TEST_HOME=/tmp/geno-firstrun
> mkdir -p "$GENO_TEST_HOME"
> export HOME="$GENO_TEST_HOME"     # new shell; everything below writes here
> ```
> Open a fresh terminal for this so you can `exit` back to your real HOME when
> done. Anywhere below that says "check `~/.geno/...`" means this temp HOME.

---

## Prerequisites (pretend you have nothing)

- [ ] `git`, Python 3.11+, and **Docker** (needed for `launch`). Confirm:
  ```bash
  git --version && python3 --version && docker --version
  ```
- [ ] `npx` available (Node) — geno-tools shells out to `npx skills`:
  ```bash
  npx --version
  ```

> **Refine:** _Were the prereqs obvious before you started? Did anything fail
> here that the docs didn't warn about?_

---

## Step 1 — Install the CLI

The published path is Homebrew; for testing **this** merged build (0.7.0
control-plane), install the local checkout instead.

**Released (Homebrew):** the tap ships one umbrella formula named `geno` — NOT
`geno-tools`. `brew install 42euge/geno/geno-tools` fails with *"No available
formula … Did you mean 42euge/geno/geno?"* — that's expected. The correct
command is:
```bash
brew install 42euge/geno/geno      # pipx-installs geno-tools + the other geno CLIs
geno-tools --version
```
⚠️ Note: the `geno` formula is pinned to an **older `main`** commit, so it will
NOT give you the 0.7.0 control-plane build (profiles/launch). To test the
merged work, use the local dev build below.

**Local dev build (this repo — recommended for this walkthrough):**
```bash
pipx install --force git+file:///path/to/geno-tools   # or a path/URL to the repo
# or, in a throwaway venv: python3 -m venv /tmp/gt && /tmp/gt/bin/pip install -e /path/to/geno-tools
geno-tools --version        # expect 0.7.0
```

- [ ] `geno-tools --version` prints `0.7.0`.
- [ ] `geno-iso --version` works too (it ships in the same package now):
  ```bash
  geno-iso --help | head -3
  ```

> 🐞 **FOUND (2026-08-05) — `brew install geno` installs ONLY the `geno` go
> binary; every Python tool (`geno-tools`, `tt`, …) is missing.**
> The install prints success + caveats listing all commands, but
> `geno-tools: command not found`.
>
> **Root cause (verified against the formula source):** the formula runs
> `pipx install git+…/<tool>.git` for all six Python tools **inside `def
> install`** — which Homebrew executes in a **build sandbox with an isolated,
> throwaway `$HOME`/`$PIPX_HOME`**. pipx writes the venvs there and reports
> success, then the sandbox home is discarded when the build ends, so nothing
> persists to `~/.local/pipx`. Only the `geno` go binary survives, because it
> alone is written to the formula prefix (`bin/"geno"`), the one location brew
> keeps. The formula's `post_install` (which *does* run with the real HOME)
> does NOT install the tools — it only registers geno-tt and *assumes*
> `command -v geno-tools` already succeeds.
>
> This is NOT an error-swallowing / `|| true` bug (the tool-install loop has no
> `|| true`, and it would have aborted the build on failure). It is a
> **structural sandbox incompatibility: `pipx install` in `def install` can
> never persist.** As written, `brew install geno` can only ever deliver the
> go binary.
>
> **Severity: high — Step-1 blocker, fails silently at the front door.**
>
> **Fix for the formula:** move the per-tool `pipx install` calls from
> `def install` into **`post_install`** (runs outside the sandbox, real HOME),
> and verify each binary lands afterward (`command -v geno-tools`), `odie`-ing
> with a clear message if not. Or have the `geno` go binary bootstrap the
> Python tools on first run.
>
> **Workaround (until the formula is fixed):** install the tools by hand —
> ```bash
> for r in geno-tools geno-tt geno-vault geno-surf geno-pear geno-specs; do
>   pipx install --force "git+https://github.com/42euge/$r.git"
> done
> ```

> **Refine:** _Did `--version` match everywhere? Was it clear that `geno-iso`
> comes bundled and isn't a separate install anymore? Did brew's "success"
> match reality, or did you hit the silent partial-install above?_

---

## Step 2 — Register with your agents

```bash
geno-tools install-agent            # interactive picker
# or non-interactive:
geno-tools install-agent claude-code
```

- [ ] Your agent (e.g. Claude Code) now sees the geno skills. Verify inside the
  agent that `/geno-tools` slash commands appear.
- [ ] `~/.geno/config.yaml` was seeded (open it and skim the sections).

> **Refine:** _Did the picker explain what "register" does? Was it clear which
> agents were detected vs available? Did config.yaml look approachable?_

---

## Step 3 — Discover skillsets

```bash
geno-tools discover
```

- [ ] You see a categorized list with `✓ installed` markers.
- [ ] `geno-tools discover --refresh` forces a re-scan.

> **Refine:** _Were categories meaningful? Could you tell what each skillset
> does from the list, or did you have to guess?_

---

## Step 4 — Install a skillset (and watch the layers)

Use `geno-tt` (it ships the `tt` CLI, so you see the provisioning layer too):

```bash
geno-tools install geno-tt
```

Watch the output for the layered behavior:

- [ ] It clones into `~/.geno-tools/geno-tt/` (bare repo + `main/` worktree +
  `active -> main` symlink).
- [ ] It resolves `requires:` dependencies (installs them too).
- [ ] It creates a venv and symlinks the `tt` CLI onto your PATH.
- [ ] It hands **registration** to `npx skills add … --full-depth` — a
  **single** invocation over the whole skills tree.
- [ ] `geno-tools status` shows it with version + commit + drift state.

> ✅ **FIXED (2026-08-05) — npx registration was invoked once per leaf skill.**
> Installing geno-tt (34 skills) previously looped `npx skills add` **34 times**
> — 34 ASCII banners, 34 "Installing to all 76 agents", and the same two
> per-agent failures (`Eve` / `PromptScript` don't support global install)
> repeated 34 times. `npx skills add <dir> --full-depth` already discovers the
> whole tree in one call, so `_install_skills_via_npx` now hands it the skills/
> root **once** (commands.py). Verified: 1 invocation, all 34 skills still
> registered in `~/.claude/skills` and `~/.agents/skills`.
>
> _(The `Eve` / `PromptScript` "does not support global skill installation"
> lines come from `npx skills` itself trying all 76 agents — harmless, but now
> shown once instead of N times. A future nicety: scope npx to the agents the
> user actually has.)_

> **Refine:** _Did the output make the "npx does registration, geno-tools does
> the rest" split legible? Was the venv/PATH step (`tt` on PATH) surprising?
> Did `status` drift language (`in-sync` / `behind`) make sense? Was
> registration now a single clean pass, not a wall of repeated banners?_

---

## Step 5 — Fork a variant (the evolve loop)

```bash
geno-tools fork geno-notes exp
geno-tools use geno-notes@exp        # flips the active symlink + re-registers
geno-tools status                    # note the active variant
geno-tools promote geno-notes exp    # ff-merge back to main (if you made changes)
```

- [ ] `fork` created `~/.geno-tools/geno-notes/.worktrees/exp/` on a new branch.
- [ ] `use` repointed `active` and re-registered skills.
- [ ] `promote` fast-forward-merged (or told you clearly why it couldn't).

> **Refine:** _Was it clear that `fork` doesn't activate, and `use` does? Did
> the reserved name / dirty-tree / ff-only guard messages read well?_

---

## Step 6 — Define a profile (scope)

This is where geno-tools stops looking like an installer.

```bash
geno-tools profile list                          # see the built-ins first
geno-tools profile create eng --agent claude-code
```

Edit `~/.geno/profiles/eng.yaml`:

```yaml
agents: [claude-code]
skills:
  - name: geno-notes
    variant: exp          # pin the variant you forked in step 5
mcp: [core]               # a catalog name — configured next
```

```bash
geno-tools profile show eng      # human-readable resolved view
geno-tools resolve eng           # the resolved plan as JSON
```

- [ ] `profile list` shows `bare / base / standard / full` as built-ins plus
  your new `eng`.
- [ ] `resolve eng` maps `geno-notes@exp` to its worktree path.
- [ ] If a referenced skill isn't installed, it appears under `missing` (try it:
  add a bogus skill name and re-run `resolve`).

> **Refine:** _Was the profile schema self-explanatory? Did `create` scaffold
> something you could actually fill in without reading docs? Did `resolve`'s
> JSON tell you what you needed?_

---

## Step 7 — Configure an MCP catalog

`mcp: [core]` in the profile needs a catalog that defines `core`. Use the
generic `file` provider for the walkthrough.

Create `~/.geno/mcp-catalog.yaml`:
```yaml
core:
  url: http://localhost:9000/core
  transport: http
```

Add the source to `~/.geno/config.yaml`:
```yaml
mcp_catalogs:
  sources:
    - kind: file
      path: ~/.geno/mcp-catalog.yaml
```

- [ ] `geno-tools resolve eng` now shows `core` (no error).
- [ ] Remove the source and re-run: `launch` should fail loudly naming the
  missing catalog (verify the error is clear, then put it back).

> **Refine:** _Was it discoverable that `mcp:` names need a catalog source? Did
> the "catalog name not found" error point you at the fix? Was the private-vs-
> generic provider distinction clear from the docs?_

---

## Step 8 — Launch a scoped session (the payoff)

```bash
geno-tools launch claude-code --profile eng . --dry-run
```

- [ ] The dry-run prints: container agent (`claude`), the workspace, the
  **bind-mount** of your `exp` worktree's `skills/`, the MCP servers, and the
  full `geno-iso run …` command.

Then for real (needs Docker running):
```bash
geno-tools launch claude-code --profile eng . --rm
```

- [ ] A container starts; inside it, only `eng`'s skills are present and the
  `.mcp.json` has only the `core` server.
- [ ] Confirm the session **cannot** see a skill you left out of the profile.
- [ ] Without Docker/geno-iso, `launch` refuses with install guidance (verify
  the hard-require message — there is no silent host fallback).

> **Refine:** _Did `--dry-run` give you enough confidence before running for
> real? Was the isolation obvious once inside? Did the "only these skills"
> promise actually hold? Was the Docker requirement surfaced early enough?_

---

## Step 9 — Govern

```bash
geno-tools status         # drift across everything
geno-tools upgrade        # pull latest for installed skillsets
geno-tools doctor         # (currently a stub — note if it misleads)
geno-tools remove geno-notes   # remove ONE skillset (unregisters via npx, cleans up)
```

- [ ] `remove` unregisters via npx and cleans up (unless `--keep-data`).

> **Refine:** _Did `doctor` being a stub confuse you? Did `remove` fully clean
> up one skillset, or leave stray state?_

---

## Step 10 — Uninstall (the exit must be as effortless as the entry)

Getting *out* is a first-class part of the experience. `uninstall` is the
faithful inverse of install — it knows every location install created, and it
**never** deletes your data.

**Always dry-run first** — read the plan, especially the KEPT list:
```bash
geno-tools uninstall --dry-run
```

- [ ] The plan lists what will be **removed**: skillsets under `~/.geno-tools`,
  agent skill registrations, bin symlinks, Claude Code plugin/marketplace clones.
- [ ] The **KEPT** section lists your data in `~/.geno` (recordings, tasks,
  vault, notes, any files you created) — confirm nothing precious is on the
  remove side.
- [ ] Only geno-managed bin symlinks are listed — unrelated tools on your PATH
  are left alone.

Then remove for real:
```bash
geno-tools uninstall              # prompts for confirmation
geno-tools uninstall --yes        # skip the prompt
geno-tools uninstall --purge-data # ALSO wipe geno's own config/registry/traces/health
                                  # (still never your recordings/tasks/vault)
```

Finally, remove the CLI package itself (a running process can't delete its own
interpreter — the command prints this reminder):
```bash
pipx uninstall geno-tools
# or, if you installed via Homebrew:
brew uninstall 42euge/geno/geno   # ⚠️ may cascade shared deps — run `brew uses --installed geno` first
```

Exit the throwaway HOME when done:
```bash
exit            # closes the sub-shell with the temp HOME
```

> **Refine:** _Was one `uninstall` command enough, or did stray state survive?
> Did the KEPT list give you confidence your data was safe? Was the "remove the
> package yourself" last step clear, or should the docs make it more prominent?
> Did the brew-cascade warning save you? (It exists because an early manual
> teardown removed `python@3.14` and broke unrelated tools — the whole reason
> this command exists.)_

---

## Refinement scorecard

After the run, rate each and capture the top issue for each:

| Area | 1–5 | Top thing to fix |
|------|-----|------------------|
| Install & version parity | | |
| Agent registration | | |
| Discover / install clarity | | |
| Variant loop (fork/use/promote) | | |
| Profile authoring | | |
| MCP catalog setup | | |
| Launch (dry-run + real) | | |
| Isolation actually enforced | | |
| Uninstall (effortless + data-safe) | | |
| Error messages point at the fix | | |
| Docs matched reality | | |

**The single highest-friction moment was:** _______________________

**The one sentence I'd want the landing page to say:** _______________________

---

## Where the docs live (to fix as you go)

- Landing / tagline: `docs/index.md`, `mkdocs.yml` (`site_description`)
- The journey you just did: `docs/getting-started.md`
- Concept map: `docs/how-it-works.md`
- The payoff layer: `docs/profiles-and-launch.md`
- Control model & precedence: `docs/control-surface.md`
- Why the resolver exists: `docs/npx-skills-dependencies.md`

Preview the site locally while you edit:
```bash
mkdocs serve        # http://127.0.0.1:8000
```
