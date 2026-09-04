# Synchronize installations across computers

`geno-tools sync` compares and reconciles the skillsets installed on computers
already named in geno-tt's host registry. It synchronizes installation intent,
not files: every receiving computer clones or fast-forwards each repository and
then uses the normal geno-tools lifecycle to build its own native runtime,
console links, and agent registrations.

## Prerequisites

Install `geno-tools` and `tt` on the computer initiating sync. Install
`geno-tools` separately on every remote host once; sync cannot bootstrap a
missing remote CLI because its remote half is `geno-tools sync export|apply`.

Configure hosts through tt rather than editing a second host list:

```bash
tt add-host local localhost --default --no-ssh
tt add-host lab buildbox.example.test --user developer
```

Choose the installation authority independently from tt's default execution
host:

```bash
geno-tools config set sync.primary lab
```

The value names an alias in `~/.geno/tt/config.toml`. A bare `sync pull` reads
`sync.primary`; an explicit host argument overrides it.

## Inspect drift

```bash
geno-tools sync status             # every configured non-local host
geno-tools sync status lab other   # selected hosts
geno-tools sync export             # this machine's JSON lockfile
```

Status reports skillsets missing on either side, different repository/branch/
version/SHA metadata as `version-skew`, and portable configuration differences.
An unreachable host is `offline`; other requested hosts are still checked.

The generated schema-version-1 lockfile lives in the command stream, not as a
hand-edited source file. It describes each stable managed skillset's URL,
branch, advisory SHA, and version plus portable configuration. The SHA helps
explain drift, but reconciliation follows the branch tip and never checks out a
detached commit.

## Pull from the primary

Preview before changing anything:

```bash
geno-tools sync pull --dry-run
geno-tools sync pull --yes
geno-tools sync pull other --yes
```

Pull installs missing skillsets, fast-forwards skewed skillsets, preserves
transitive dependencies, removes extras, and applies portable configuration.
Removals are listed and require confirmation unless `--yes` is supplied.
Python skillsets rebuild their editable venv by default; `--no-rebuild` skips
that cost but may leave installed CLIs stale.

Every managed stable worktree is checked before mutation. Any dirty or
unreadable worktree aborts the whole operation and is named in the error. Local
dev-mode checkouts are never copied or selected by sync.

## Push to another host

```bash
geno-tools sync push lab --dry-run
geno-tools sync push lab --yes
```

Push serializes this machine's lockfile and pipes it over one outbound SSH
connection to `geno-tools sync apply -`. The remote host never connects back.
Because stdin carries the lockfile, a push that would remove skillsets refuses
at end-of-input unless `--yes` was supplied explicitly.

`sync apply -` is public plumbing for debugging or automation:

```bash
geno-tools sync export | ssh buildbox 'geno-tools sync apply - --dry-run'
```

## What syncs

- installed skillset repository URL, branch, advisory SHA, and version;
- `aliases`, `discovery`, `autonomy`, and `mode` configuration keys.

## What remains machine-local

- credentials, endpoints, profiles, and absolute paths;
- uncommitted files and local development checkouts;
- venv contents and console-script files;
- the set of detected coding agents and their machine-specific registrations.

If a step fails, successful independent steps remain applied and failures are
listed. There is no rollback. Correct the named dirty branch, network, or
installation problem and run the same pull/push again; reconciliation is
idempotent.

Use the [sync smoke test](sync-manual-acceptance.md) for an end-to-end
reconciliation against a second computer.
