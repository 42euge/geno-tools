# Manual test: mirror and dispatch from VS Code

This runbook validates the distinction between a persistent remote workspace
mirror and a task dispatch. Do not invoke `tt` directly during this test.

## Preconditions

- Geno Tools TT Workspaces `0.3.3` is installed.
- `Geno Tools: TT Path` points to the mirror/dispatch-capable `tt` installation.
- At least one remote TT host is configured and has Git, tmux, and Claude.
- The current window contains a local TT workspace with no important
  uncommitted changes.

Run **Developer: Reload Window** from the Command Palette before starting.

## 1. Verify the initial sidebar

1. Open the Geno Tools activity-bar view.
2. Confirm that **Current Workspace** identifies the local workspace.
3. If the workspace does not yet exist on another host, confirm that **Remote
   Mirrors** is absent.

The third section is based on workspace presence in the host registries, not on
whether an agent task is running.

## 2. Mirror the workspace

1. On the workspace row under **Current Workspace**, select **Mirror Workspace
   to Host** beside the two open buttons.
2. Choose the remote host.

There should be no task name, context picker, or confirmation dialog. Expected
results:

- The selected workspace's current files, Git metadata, dirty state, untracked
  files, and ignored files are transferred with rsync. `.wt` worktrees and
  `.DS_Store` files are intentionally excluded.
- VS Code reports that the workspace was mirrored.
- A third **Remote Mirrors** section appears.
- The section contains the selected host and repository count.
- The row tooltip shows the stable workspace name, host, and remote path.

Canceling the host picker must leave the workspace unchanged.

## 3. Open the mirror

Select the remote host under **Remote Mirrors**. A new VS Code window should
open over Remote SSH at the mirrored workspace. The original local window must
remain open.

An unrelated workspace must not show this mirror. A window opened inside one
of the canonical workspace's `.wt` worktrees should show the same mirrors
because worktrees share the stable workspace identity.

## 4. Prepare a dispatch handoff

In the local window, create or open a Markdown file with a small, reversible
task. For example:

```markdown
# VS Code dispatch smoke test

Work only in this repository. Create `remote-dispatch-smoke.txt` containing
`remote dispatch complete`, record the verification in `RETURN.md`, and then
wait for recall. Do not push, deploy, or contact external services.
```

Keep that document active in the editor.

## 5. Dispatch work from the mirror

1. Use the rocket action on the host row under **Remote Mirrors**.
2. Accept or edit the generated durable dispatch name.
3. Choose **Use Active Document** as the dispatch context.
4. Review the task-level confirmation and select **Dispatch**.

The destination-host picker should not appear because the mirror row already
identifies the host. VS Code should report that the dispatch was created.

## 6. Observe and recall the task

1. Run **Geno Tools: Manage Remote Dispatches** from the Command Palette or the
   Remote Mirrors toolbar.
2. Choose the new dispatch, then **Open Remote Session**.
3. Observe the agent in the integrated terminal and detach from tmux when it is
   ready for recall.
4. Manage the dispatch again and choose **Stop and Recall**.
5. Review the destructive-action confirmation and select **Stop and Recall**.
6. If offered, select **Open Return Handoff**.

Expected results:

- The remote task tmux session stops.
- The dispatched changes return to the original local workspace.
- `RETURN.md` opens in VS Code when requested.
- Returned files and Git state are visible in Explorer and Source Control.
- **Remote Mirrors remains visible** because recalling a task does not remove
  the mirrored workspace.

## 7. Safety checks

Repeat with a disposable dispatch if you want to validate the guards:

- Choose **Recall** while the remote tmux session is still running. The action
  must fail without changing local files.
- After dispatching, make a local edit and choose **Stop and Recall**. Recall
  must reject the locally drifted workspace and preserve the remote session.
- Cancel the **Stop and Recall** confirmation. The dispatch must remain active.

Use **Geno Tools: Show TT Output** from the Command Palette to inspect a failed
operation without leaving VS Code.

## Pass criteria

The test passes when mirroring requires only a host choice, **Remote Mirrors**
tracks durable cross-host workspace presence, dispatching from a mirror asks
for task context without asking for the host again, and recall leaves the
mirror available for later work.
