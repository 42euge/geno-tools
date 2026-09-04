# Remote Mirrors manual acceptance

Artifact: Geno Tools TT Workspaces `0.3.6`, branch `wt/remote-dispatch`.

Environment: VS Code on macOS with the editable `geno-tt` CLI and the existing
`geno-dev.2026.q3` mirror on `z2`.

## Preconditions and safety

- `genoTools.ttPath` points to the remote-dispatch editable CLI.
- Local and z2 registries contain `explore.geno.geno-dev.2026.q3`.
- Steps 1–5 are read-only. The retirement section must use a disposable mirror;
  it creates a local ZIP and moves only that remote copy to its graveyard.

## Steps

1. Run **Developer: Reload Window** from the VS Code Command Palette.
   - Expected: the Geno Tools view description reports `v0.3.6`.
2. Open the Geno Tools activity-bar view.
   - Expected: the sections are **Current Workspace**, **Remote Mirrors**, then
     **All Workspaces**.
   - Expected: **All Workspaces** starts collapsed.
3. Inspect **Remote Mirrors**.
   - Expected for `geno-dev.2026.q3`: it opens automatically and a `z2` row
     appears with `1 repos`.
   - Expected for a workspace without a mirror: it starts collapsed.
4. Hover over the `z2` row.
   - Expected: the tooltip identifies
     `/home/eriveraramos/code/explore/geno/geno-dev.2026.q3`.
5. Select the `z2` row.
   - Expected: VS Code opens the remote mirror in a new Remote SSH window.
   - Expected: Geno Tools is still present in that window without installing
     the VSIX into z2's extension server.

## Back up and retire a disposable mirror

1. From VS Code, create or open a disposable local TT workspace and use its
   **Mirror Workspace to Host** action to mirror it to z2.
2. In **Remote Mirrors**, hover over the z2 row.
   - Expected: rocket and trash actions appear next to the row.
3. Select the trash action, then cancel **Back Up and Retire**.
   - Expected: no retirement command runs and the mirror remains visible.
4. Select the trash action again and confirm **Back Up and Retire**.
   - Expected: progress says the workspace is being backed up and retired.
   - Expected: the success notification names a ZIP below
     `~/.geno/tt/backups/mirrors/` on the Mac.
   - Expected: **Geno Tools: TT** output reports the backup before the remote
     graveyard destination.
5. Rescan TT workspaces.
   - Expected: the disposable z2 row is gone; the local source workspace still
     exists.

## Failure observations

- If the section is absent, the old extension host is still active; reload the
  window and verify the displayed version is `v0.3.6`.
- If the section says **Not mirrored yet**, run **Rescan TT Workspaces** and
  inspect **Geno Tools: Show TT Output**. Both registries must contain the same
  stable workspace ID.

## Cleanup and rollback

Keep or remove the generated local ZIP after inspecting its reported path.
Retire the disposable local source separately if it is no longer needed. To
roll back the UI change, reinstall the `0.3.4` VSIX and reload VS Code; the
graveyard move and backup already performed are not reversed.

## Known limitation

The final rendered-sidebar observation must be made in the user's existing VS
Code window after reload; package, registry, and automated view behavior can be
verified independently.
