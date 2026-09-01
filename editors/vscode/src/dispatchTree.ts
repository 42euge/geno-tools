import * as vscode from "vscode";

import { activeDispatchesForWorkspace, TtDispatch } from "./model";
import { TtCli } from "./ttCli";
import { WorkspaceNode } from "./workspaceTree";

export const HAS_CURRENT_WORKSPACE_DISPATCH =
  "genoTools.hasCurrentWorkspaceDispatch";

export interface RemoteDispatchNode {
  kind: "remoteDispatch";
  dispatch: TtDispatch;
}

export function isRemoteDispatchNode(value: unknown): value is RemoteDispatchNode {
  return Boolean(
    value &&
      typeof value === "object" &&
      "kind" in value &&
      value.kind === "remoteDispatch" &&
      "dispatch" in value
  );
}

export class RemoteDispatchTreeProvider
  implements vscode.TreeDataProvider<RemoteDispatchNode>, vscode.Disposable
{
  private readonly changed = new vscode.EventEmitter<RemoteDispatchNode | undefined>();
  private cache: RemoteDispatchNode[] | undefined;

  readonly onDidChangeTreeData = this.changed.event;

  constructor(
    private readonly cli: TtCli,
    private readonly currentWorkspace: () => Promise<WorkspaceNode | undefined>
  ) {}

  async reload(): Promise<void> {
    this.cache = undefined;
    await this.nodes();
    this.changed.fire(undefined);
  }

  getTreeItem(node: RemoteDispatchNode): vscode.TreeItem {
    const item = new vscode.TreeItem(
      node.dispatch.name,
      vscode.TreeItemCollapsibleState.None
    );
    item.description = `→ ${node.dispatch.target.host_alias}`;
    item.iconPath = new vscode.ThemeIcon("remote");
    item.contextValue = "remoteDispatch";
    item.tooltip = new vscode.MarkdownString([
      `**${node.dispatch.name}**`,
      "",
      `Host: ${node.dispatch.target.host_alias}`,
      `Session: ${node.dispatch.session}`,
      `Source: ${node.dispatch.source.workspace_view}`
    ].join("  \n"));
    item.command = {
      command: "genoTools.manageDispatches",
      title: "Manage Remote Dispatch",
      arguments: [node]
    };
    return item;
  }

  async getChildren(node?: RemoteDispatchNode): Promise<RemoteDispatchNode[]> {
    return node ? [] : this.nodes();
  }

  dispose(): void {
    this.changed.dispose();
  }

  private async nodes(): Promise<RemoteDispatchNode[]> {
    if (this.cache) {
      return this.cache;
    }
    const workspace = await this.currentWorkspace();
    const dispatches = workspace
      ? activeDispatchesForWorkspace(
          await this.cli.dispatches(),
          workspace.workspace.path
        )
      : [];
    this.cache = dispatches.map((dispatch) => ({
      kind: "remoteDispatch",
      dispatch
    }));
    await vscode.commands.executeCommand(
      "setContext",
      HAS_CURRENT_WORKSPACE_DISPATCH,
      this.cache.length > 0
    );
    return this.cache;
  }
}
