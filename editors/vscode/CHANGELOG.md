# Changelog

## 0.3.4

- Keep Remote Mirrors visible as the third sidebar section and show an explicit
  empty state before a workspace is mirrored

## 0.3.3

- Mirror the selected workspace path with rsync instead of resolving and
  cloning repository remotes

## 0.3.2

- Move Mirror Workspace from the section toolbar onto each workspace row

## 0.3.1

- Make workspace mirroring the lightweight primary remote action
- Replace the task-scoped Remote Dispatches view with persistent Remote Mirrors
- Allow work to be dispatched directly from a remote mirror row

## 0.3.0

- Persist explicit ownership for tmux sessions created or adopted in the VS
  Code extension and distinguish Live, Stopped, and External rows.
- Keep managed sessions visible after a tmux server dies, with Restore and
  Remove actions; saved agent recoveries replay their validated resume command.
- Make Remove idempotent when tmux reports that its server or selected session
  is already absent, while preserving managed records on real connection,
  authorization, executable, or cancellation failures.
- Refresh live tmux state when the tree loads and after lifecycle actions
  without background polling.
- Add workspace dispatch to configured remote hosts using editor selections,
  documents, brief instructions, or handoff files.
- Add a conditional Remote Dispatches sidebar section for active dispatches
  originating from the current workspace.
- Add dispatch management for reopening tmux, safe recall, stop-and-recall,
  and opening the returned handoff.

## 0.2.3

- Match captured terminal scrollback against locally saved Claude and Codex
  transcripts before creating a recovery tmux session.
- Build the verified `clauded -r <session-id>` or
  `codexd resume <session-id>` command locally and show it in the confirmation
  dialog; the OpenAI planner can no longer invent a startup command or ID.
- Refuse shell-only recovery when no saved agent session matches confidently,
  so environment setup such as virtualenv activation cannot masquerade as
  conversation recovery.

## 0.2.2

- Add a confirmed trash action for deleting local or remote tmux sessions from
  either Geno Tools workspace view.
- Refresh the TT registry and clear stale VS Code terminal link indicators
  after deletion.
- Derive recovery names from the overall human-stated task instead of host or
  workspace metadata, sampling long histories across the full scrollback.
- Add an `Edit Name…` option before a recovered tmux session is created.

## 0.2.1

- Read the recovery provider endpoint, model, API-key environment variable, and
  API surface from `~/.geno/config.yaml`.
- Route Agents SDK runs through an explicit provider so GUI-launched VS Code
  does not silently fall back to `api.openai.com`.
- Disable SDK tracing for terminal-history recovery and show the resolved
  endpoint in the consent dialog.

## 0.2.0

- Add an OpenAI Agents SDK action that scans bounded VS Code terminal history
  and proposes a reviewed tmux continuation.
- Restore the clipboard after history capture and validate proposed session
  names, workspace paths, and single-line startup commands before creation.
- Show bidirectional terminal/tmux link indicators and distinguish a recovery
  source from a terminal actually attached to tmux.
- Add `genoTools.agentModel`, defaulting to `gpt-5.6`.

## 0.1.1

- Show the running extension version and UTC build datetime in each view title.
- Refresh and invalidate the workspace trees after creating a tmux session.
- Add the live VS Code Terminals workspace section.

## 0.1.0

- Add local and remote TT workspace explorer.
- Add create, rescan, open, mirror, and whole-workspace worktree actions.
- Make the workspace `+` create a new tmux session every time, with an optional
  custom name.
- Add a Current Workspace view with its repositories and registered tmux state.
- Group repositories and tmux sessions into separate workspace folders.
- Add adjacent actions to open a workspace in the current window or a new one.
- Put `+` actions on the workspace view, repository group, and tmux group.
- Show open integrated terminals by workspace with refresh and focus actions.
- Refresh the TT registry immediately after creating a detached tmux session.
- Show the extension version and UTC build datetime in each view title.
- Add cross-host report command and configurable TT executable path.
