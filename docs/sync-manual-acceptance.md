# Manual acceptance test for installation sync

Use this runbook to exercise `geno-tools sync` between two computers before a
release. It covers inspection, pull, push, safety checks, configuration
portability, and transport failures.

## Safety boundary

Run this test with disposable OS users, disposable machines, or restorable VM
snapshots. The acceptance cases intentionally remove managed skillsets, change
`~/.geno/geno-tools/config.yaml`, and move a managed Git worktree to an older
commit. Do not run the mutation cases against a normal working installation.

Use these roles throughout the runbook:

- **source** — the installation whose state should win;
- **target** — the installation that is deliberately made different and then
  reconciled;
- **controller** — whichever machine runs a command. Pull commands run on the
  target; push commands run on the source.

Record the source and target hostnames, the geno-tools build under test, and
the starting Git SHA before continuing.

## Prerequisites

On both machines:

1. Install the same geno-tools build under test. When testing a checkout, use
   the process in [development.md](development.md#develop-geno-tools-itself).
2. Confirm that `geno-tools` is available to a non-interactive SSH session.
   An activated shell-only virtual environment is not sufficient because sync
   invokes the literal command `geno-tools` remotely.
3. Install `tt` and ensure public-key SSH works without an interactive password
   or host-key prompt.
4. Use a disposable `~/.geno-tools` installation and host registry.

From the target, verify the source:

```zsh
ssh testuser@source.example.test \
  'command -v geno-tools && geno-tools sync export'
```

From the source, verify the target:

```zsh
ssh testuser@target.example.test \
  'command -v geno-tools && geno-tools sync export'
```

Both commands must print a command path followed by a JSON lockfile. If the
remote command is missing, install the build where the remote non-interactive
shell can find it before continuing.

Configure reciprocal aliases. Run the first command on the target and the
second on the source:

```zsh
# target
tt add-host source testuser@source.example.test --no-ssh
geno-tools config set sync.primary source

# source
tt add-host target testuser@target.example.test --no-ssh
```

The geno-tools `sync.primary` setting is intentionally independent of tt's
default host. The registry value is passed directly to `ssh`, so these examples
store the remote username as part of the destination. The earlier SSH checks
replace the key-setup step skipped by `--no-ssh`.

## Prepare controlled drift

Choose three non-production skillset repositories:

| Variable | Requirement |
| --- | --- |
| `COMMON_URL` / `COMMON_NAME` | Python skillset with at least two commits; the newest commit must not change `pyproject.toml` |
| `SOURCE_ONLY_URL` / `SOURCE_ONLY_NAME` | Skillset with no dependency on the target-only fixture |
| `TARGET_ONLY_URL` / `TARGET_ONLY_NAME` | Skillset that is not a dependency of either source fixture |

Set the six values in each shell. All names must use the full repository name,
such as `geno-sync-common`.

Install the common and source-only fixtures on the source:

```zsh
geno-tools install "$COMMON_URL"
geno-tools install "$SOURCE_ONLY_URL"
geno-tools config set mode sync-source
geno-tools config set local_test.marker source-only
```

Install the common and target-only fixtures on the target, then move the common
fixture back one commit. This `reset --hard` is restricted to the disposable
fixture named by `COMMON_NAME`.

```zsh
geno-tools install "$COMMON_URL"
geno-tools install "$TARGET_ONLY_URL"
geno-tools config set mode sync-target
geno-tools config set sync.primary source
geno-tools config set local_test.marker target-only
git -C "$HOME/.geno-tools/$COMMON_NAME/main" reset --hard HEAD^
git -C "$HOME/.geno-tools/$COMMON_NAME/main" status --short
```

Pass if the final command prints nothing. The target now has all four kinds of
drift used below:

- `$SOURCE_ONLY_NAME` is missing on the target;
- `$TARGET_ONLY_NAME` is extra on the target;
- `$COMMON_NAME` has version skew;
- `mode` is different while `sync.primary` and `local_test.marker` are
  target-local values that must survive reconciliation.

## 1. Export a lockfile

Run on each machine:

```zsh
geno-tools sync export | python3 -m json.tool
```

Pass if each command exits zero and prints a schema-version-1 object containing
`machine`, `generated`, `skillsets`, and `config`. Each fixture entry must
contain `url`, `branch`, `sha`, and `version`.

The `config` object must include `mode`. It must not contain `sync` or
`local_test`; those keys are machine-local.

## 2. Report directional drift

Run on the target:

```zsh
geno-tools sync status source
```

Pass if the report includes the following lines, using the fixture names:

```text
source:
  geno-sync-common: version-skew
  geno-sync-source-only: missing-here
  geno-sync-target-only: extra-here
  config mode: 'sync-target' -> 'sync-source'
```

The order may differ. Replace the example names with the selected fixture
names. No files should change.

Also run `geno-tools sync status` with no host argument. Pass if it checks every
configured non-local host and includes `source`.

## 3. Refuse a dirty managed worktree

Run on the target:

```zsh
touch "$HOME/.geno-tools/$COMMON_NAME/main/.sync-manual-test-dirty"
geno-tools sync pull --dry-run
```

Pass if pull exits nonzero, names `$COMMON_NAME`, and reports that it is
refusing to sync dirty or unreadable skillsets. The source-only fixture must
remain uninstalled and the target-only fixture must remain installed.

Remove only the marker created above and confirm the worktree is clean:

```zsh
rm -- "$HOME/.geno-tools/$COMMON_NAME/main/.sync-manual-test-dirty"
git -C "$HOME/.geno-tools/$COMMON_NAME/main" status --short
```

## 4. Preview every reconciliation action

Run on the target:

```zsh
geno-tools sync pull --dry-run
```

Pass if the output contains one action of each kind:

```text
  would install geno-sync-source-only
  would update geno-sync-common
  would remove geno-sync-target-only
  would apply config
```

The command must not prompt for confirmation. Run `geno-tools sync status
source` again and pass if all original drift remains.

## 5. Guard removals, then pull

Run on the target without `--yes`:

```zsh
geno-tools sync pull
```

Pass if the command lists `$TARGET_ONLY_NAME` and asks `Continue? [y/N]`.
Answer `n`. It must exit nonzero with `sync cancelled; no changes made`, and a
status check must show all original drift.

Now authorize the removal:

```zsh
geno-tools sync pull --yes
geno-tools sync status source
geno-tools sync pull --yes
```

Pass if the first pull installs the source-only fixture, updates the common
fixture, removes the target-only fixture, and applies config. Status must print
`in sync`. The second pull must print `already in sync`.

Inspect the target configuration:

```zsh
geno-tools config show
sed -n '1,240p' "$HOME/.geno/geno-tools/config.yaml"
```

Pass if `mode` is `sync-source`, `sync.primary` is still `source`, and
the raw config file shows `local_test.marker` is still `target-only`.
`geno-tools config show` omits unknown local-only keys, which is why the raw
file is inspected too. This demonstrates that portable configuration changed
while machine-local configuration survived.

## 6. Push with dry-run and removal protection

Recreate target-only drift by reinstalling the target-only fixture on the
target:

```zsh
geno-tools install "$TARGET_ONLY_URL"
```

Run the remaining commands in this section on the source:

```zsh
geno-tools sync push target --dry-run
```

Pass if the output includes `would remove` for `$TARGET_ONLY_NAME`, does not
prompt, and the fixture remains installed on the target.

Next omit `--yes`:

```zsh
geno-tools sync push target
```

Pass if push exits nonzero and reports `sync cancelled; no changes made`. A
push cannot open an interactive removal prompt because standard input carries
the lockfile, so destructive pushes require explicit `--yes`.

Apply the push and verify from the target:

```zsh
# source
geno-tools sync push target --yes

# target
geno-tools sync status source
```

Pass if push removes the target-only fixture and status prints `in sync`.

## 7. Compare default rebuild with `--no-rebuild`

Run these commands on the target. The common fixture's newest commit must not
change `pyproject.toml`, as required during setup.

```zsh
git -C "$HOME/.geno-tools/$COMMON_NAME/main" reset --hard HEAD^
geno-tools sync pull source --yes --no-rebuild 2>&1 | tee /tmp/sync-no-rebuild.log
```

Pass if pull updates `$COMMON_NAME` and the log does not contain `rebuilding
venv`.

Create the same skew once more and use the default behavior:

```zsh
git -C "$HOME/.geno-tools/$COMMON_NAME/main" reset --hard HEAD^
geno-tools sync pull source --yes 2>&1 | tee /tmp/sync-rebuild.log
```

Pass if pull updates `$COMMON_NAME` and the log includes `rebuilding venv for
$COMMON_NAME`. Finish by confirming `geno-tools sync status source` prints `in
sync`.

## 8. Handle malformed input without mutation

Run on the target:

```zsh
printf 'not json\n' | geno-tools sync apply - --dry-run
```

Pass if the command exits nonzero with `lockfile is not valid JSON`. Status
must still report `in sync`.

## 9. Distinguish missing, malformed, and offline remotes

Run this section on the target. These cases change its disposable tt host
registry. Save the registry's starting state so the aliases can be removed
afterward:

```zsh
cp "$HOME/.geno/tt/config.toml" "$HOME/.geno/tt/config.toml.sync-test-backup"
tt add-host simulated localhost --no-ssh
tt add-host offline does-not-exist.invalid --no-ssh
```

Simulate a missing remote CLI without changing the real executable:

```zsh
REAL_GENO_TOOLS="$(command -v geno-tools)"
STUB_DIR="$(mktemp -d)"
printf '#!/bin/sh\nexit 127\n' > "$STUB_DIR/geno-tools"
chmod +x "$STUB_DIR/geno-tools"
PATH="$STUB_DIR:$PATH" "$REAL_GENO_TOOLS" sync status simulated
```

Pass if status exits nonzero and prints `geno-tools is not installed`.

Replace the stub with malformed lockfile output:

```zsh
printf '#!/bin/sh\nprintf "not-json\\n"\n' > "$STUB_DIR/geno-tools"
chmod +x "$STUB_DIR/geno-tools"
PATH="$STUB_DIR:$PATH" "$REAL_GENO_TOOLS" sync status simulated
```

Pass if status exits nonzero and prints `invalid lockfile: lockfile is not
valid JSON`.

Finally test an unreachable host while allowing another host to succeed:

```zsh
geno-tools sync status offline source
```

Pass if `offline` is reported as offline, `source` is still checked, and the
overall command exits zero because at least one host succeeded. Running
`geno-tools sync status offline` alone must exit nonzero.

Remove the stub and restore the disposable registry:

```zsh
rm -r -- "$STUB_DIR"
mv "$HOME/.geno/tt/config.toml.sync-test-backup" \
  "$HOME/.geno/tt/config.toml"
```

## Cleanup

On both machines, uninstall any fixture that was not removed by reconciliation:

```zsh
geno-tools uninstall "$COMMON_NAME"
geno-tools uninstall "$SOURCE_ONLY_NAME"
geno-tools uninstall "$TARGET_ONLY_NAME"
```

`not installed` is acceptable during cleanup. Remove `/tmp/sync-no-rebuild.log`
and `/tmp/sync-rebuild.log`, then discard the test users or restore the machine
snapshots.

The feature passes manual acceptance when every required case above passes,
both installations finish in sync before cleanup, and no non-fixture skillset
or machine-local configuration was changed.
