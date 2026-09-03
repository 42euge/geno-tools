# VS Code tmux lifecycle management

**Date:** 2026-09-03  
**Status:** Approved  
**Repository:** `geno-tools` (`editors/vscode`)

## Goal

Make tmux management in the Geno Tools VS Code extension resilient when live
tmux state and the last TT workspace registry snapshot disagree. In particular,
if the tmux server dies, a user must still be able to see, restore, or remove a
session that the extension owns. Removing such a session must converge even
when `tmux kill-session` reports that the server or session is already gone.

This is lifecycle management for explicitly managed workspace sessions, not a
general tmux browser. Sessions outside TT workspaces are not shown, and live
workspace sessions that the extension did not create or adopt are visible but
remain external to lifecycle management.

## Approaches considered

### 1. Persist ownership in the extension and reconcile it with TT live state

This is the selected approach. The extension records sessions it creates or the
user explicitly adopts in VS Code's durable extension state. On every TT
registry refresh, it overlays those records on the live sessions returned by
the host-owned workspace registry.

This keeps the change in one deployable repository, survives tmux server death,
and gives the UI enough information to restore a single-pane session. The
storage is deliberately a plugin concern: it records only what the plugin owns,
while TT's registry remains the authority for currently live workspace state.

### 2. Infer ownership from a session's current directory

Rejected. A manually created tmux session can happen to run inside a TT
workspace. Its location associates it with a workspace but does not give the
plugin permission to manage or delete it.

### 3. Only tolerate missing-session errors during deletion

Rejected as incomplete. It fixes the reported deletion failure but still makes
a dead server erase the user's ability to distinguish a stopped managed session
from an unrelated or forgotten registry row, and it provides no restore path.

## Session model and ownership

A managed-session record contains:

- canonical TT registry host;
- TT workspace id and workspace path;
- tmux session name;
- last known pane command and path;
- launch kind (`shell` or `agent-resume`);
- an optional validated agent resume command; and
- creation or adoption time.

The record key is the canonical host plus tmux session name, matching tmux's
per-server uniqueness rule. The schema is versioned and malformed records are
ignored rather than allowed to break the workspace tree.

The extension creates a record only when:

1. it successfully creates a tmux session; or
2. the user explicitly chooses **Manage tmux Session** for a live external row.

Adopting a session records a shell fallback because the extension cannot infer
the original launch intent safely. Sessions created by the extension's agent
recovery flow retain the already validated resume command. Live external
sessions remain openable but do not receive Restore or Remove actions until
adopted.

## Lifecycle states

The tree derives state by reconciling persistent managed records with a freshly
scanned TT workspace registry:

- **Live:** a managed record and a live tmux session share host and name.
- **Stopped:** a managed record exists, the host scan succeeded, and no matching
  live session exists. A dead tmux server therefore makes its managed sessions
  Stopped rather than deleting their identity.
- **External:** a live workspace session has no managed record.
- **Unknown:** the host registry cannot be refreshed. The host shows the
  existing load error and managed records remain stored unchanged; an outage is
  never interpreted as session death.

The tree refreshes on initial load, explicit refresh, and after lifecycle
actions. It does not poll continuously.

## Commands and data flow

### Create

The existing create flow creates the detached tmux session, records it as a
managed shell session, refreshes the TT registry, and attaches a terminal. Agent
recovery updates the record with its validated resume command after sending that
command successfully.

### Manage

**Manage tmux Session** adopts a live external row into persistent state. It does
not mutate the running tmux session. A subsequent refresh renders it Live and
enables lifecycle actions.

### Restore

**Restore tmux Session** is available only for Stopped rows. It recreates the
same session name in the recorded workspace path. For an `agent-resume` record,
the confirmation identifies the saved resume command and the extension sends it
after creation. Otherwise the restored session starts at a shell. Successful
restore refreshes the registry and attaches a VS Code terminal.

If the directory no longer exists, tmux creation fails normally and the record
remains Stopped. If the session reappears between rendering and restore, the
extension reports the real tmux error and refreshes rather than overwriting it.

### Remove

**Remove tmux Session** is destructive and remains modal. It always attempts
`tmux kill-session` so a Stopped-to-Live race cannot leave a process behind.
The operation has convergent semantics:

- exit zero means the session was killed;
- `no server running`, `no sessions`, or `can't find session` means it was
  already absent and is also success;
- SSH, authorization, timeout, missing executable, cancellation, and all other
  failures remain errors.

Only killed or already-absent outcomes delete the managed record and unlink the
terminal association. The extension then refreshes the TT registry and both
workspace trees. A real failure preserves the record.

## Component boundaries

- `tmuxSessions.ts` owns the versioned managed-session record, persistence,
  reconciliation, and pure state transitions.
- `ttCli.ts` owns local and remote process execution and classifies the narrow
  set of tmux absence errors. Command handlers never match stderr strings.
- `workspaceTree.ts` renders lifecycle state and exposes state-specific context
  values; it does not persist or mutate sessions.
- `extension.ts` coordinates confirmation, lifecycle operations, registry
  refresh, terminal linking, and user-facing errors.

These boundaries keep persistence and error classification independently
testable and avoid adding lifecycle rules to the already large tree renderer.

## UI behavior

- Live managed row: normal tmux icon, pane command, Open and Remove actions.
- Stopped managed row: stopped icon and `Stopped` description, Restore as its
  primary action, plus Remove.
- Live external row: `External` description, Open and Manage actions.
- Workspace and group counts include live and stopped managed sessions plus
  visible external live sessions.

The existing command title changes from **Delete tmux Session** to **Remove tmux
Session** because the operation removes both live state and the plugin's durable
record. Existing command identifiers can remain stable to avoid breaking VS Code
keybindings.

## Testing

Focused Node tests cover:

- record parsing, versioning, persistence, and malformed-state tolerance;
- reconciliation into Live, Stopped, External, and Unknown-preserving outcomes;
- create and agent recovery recording the correct restore recipe;
- explicit adoption of an external session;
- restore to a shell and restore with a validated agent command;
- live removal, server-already-dead removal, session-already-missing removal,
  and a session that disappears during removal;
- genuine SSH, permission, cancellation, and executable failures remaining
  errors with the record intact;
- state-specific tree labels, icons, commands, and manifest menu visibility;
- local and remote command construction; and
- refresh and terminal-link cleanup after successful lifecycle changes.

Repository verification remains `npm run check`, `npm test`, and `npm run
build` from `editors/vscode`, followed by `git diff --check`.

## Non-goals

- Managing tmux sessions outside TT workspaces.
- Inferring ownership from a working directory or process name.
- Reconstructing multi-pane layouts that the extension did not create.
- Recovering tmux scrollback or process memory.
- Continuous background polling or a tmux watchdog.
- Treating host connectivity failures as stopped sessions.
