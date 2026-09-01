# Manual test: remote dispatch from VS Code

This runbook validates remote dispatch and recall through the Geno Tools VS
Code extension. Do not invoke `tt` directly during this test.

## Preconditions

- Geno Tools TT Workspaces `0.3.0` is installed.
- `Geno Tools: TT Path` points to the dispatch-capable `tt` installation.
- At least one remote TT host is configured and has Git, tmux, and Claude.
- The current window contains a local TT workspace with no important
  uncommitted changes.

Run **Developer: Reload Window** from the Command Palette before starting.

## 1. Verify the initial sidebar

1. Open the Geno Tools activity-bar view.
2. Confirm that **Current Workspace** identifies the local workspace.
3. Confirm that **Remote Dispatches** is absent when this workspace has no
   active dispatch.

The extension intentionally hides the third section when there is nothing to
manage.

## 2. Prepare the handoff

Create or open a Markdown file in the workspace with a small, reversible task.
For example:

```markdown
# VS Code dispatch smoke test

Work only in this repository. Create `remote-dispatch-smoke.txt` containing
`remote dispatch complete`, record the verification in `RETURN.md`, and then
wait for recall. Do not push, deploy, or contact external services.
```

Keep that document active in the editor.

## 3. Dispatch from VS Code

1. In **Current Workspace**, select **Dispatch Workspace to Remote Host** from
   the toolbar or the workspace row's context menu.
2. Choose the remote host.
3. Accept or edit the generated durable dispatch name.
4. Choose **Use Active Document** as the dispatch context.
5. Review the modal confirmation and select **Dispatch**.

Expected results:

- VS Code reports that the dispatch was created.
- A third **Remote Dispatches** section appears.
- The section contains the dispatch name with an arrow to the selected host.
- The item tooltip shows its host, tmux session, and source workspace path.

Canceling any prompt must leave the sidebar and workspace unchanged.

## 4. Exercise the third section

1. Select the dispatch item under **Remote Dispatches**.
2. Choose **Open Remote Session**.
3. Confirm that an integrated terminal opens the remote tmux session.
4. Observe the agent completing the handoff, then detach from tmux without
   closing VS Code.

Open an unrelated local workspace in another VS Code window. Its Geno Tools
sidebar must not show this dispatch. Return to the source workspace; the third
section must still be present. A dispatch originating from a `.wt` worktree is
also considered part of its canonical workspace.

## 5. Recall from VS Code

1. Select the dispatch item again.
2. Choose **Stop and Recall**.
3. Review the destructive-action confirmation and select **Stop and Recall**.
4. If offered, select **Open Return Handoff**.

Expected results:

- The remote tmux session stops.
- The remote changes return to the original local workspace.
- `RETURN.md` opens in VS Code when requested.
- **Remote Dispatches** disappears because the workspace no longer has an
  active dispatch.
- The returned files and Git state are visible in Explorer and Source Control.

## 6. Safety checks

Repeat with a disposable dispatch if you want to validate the guards:

- Choose **Recall** while the remote tmux session is still running. The action
  must fail without changing local files.
- After dispatching, make a local edit and choose **Stop and Recall**. Recall
  must reject the locally drifted workspace and preserve the remote session.
- Cancel the **Stop and Recall** confirmation. The dispatch must remain active
  and listed in the third section.

Use **Geno Tools: Show TT Output** from the Command Palette to inspect a failed
operation without leaving VS Code.

## Pass criteria

The test passes when the third section appears only for an active dispatch from
the current canonical workspace or one of its `.wt` worktrees, opens the
correct remote session, and disappears after a successful recall.
