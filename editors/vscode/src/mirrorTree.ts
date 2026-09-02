import * as vscode from "vscode";

import { workspaceReference } from "./model";
import { WorkspaceNode } from "./workspaceTree";

export const HAS_CURRENT_WORKSPACE_MIRROR =
  "genoTools.hasCurrentWorkspaceMirror";

export interface RemoteMirrorNode {
  kind: "remoteMirror";
  source: WorkspaceNode;
  mirror: WorkspaceNode;
}

interface RemoteMirrorMessageNode {
  kind: "message";
  label: string;
  description: string;
}

type RemoteMirrorTreeNode = RemoteMirrorNode | RemoteMirrorMessageNode;

export function isRemoteMirrorNode(value: unknown): value is RemoteMirrorNode {
  return Boolean(
    value &&
      typeof value === "object" &&
      "kind" in value &&
      value.kind === "remoteMirror" &&
      "source" in value &&
      "mirror" in value
  );
}

export class RemoteMirrorTreeProvider
  implements vscode.TreeDataProvider<RemoteMirrorTreeNode>, vscode.Disposable
{
  private readonly changed = new vscode.EventEmitter<RemoteMirrorTreeNode | undefined>();
  private cache: RemoteMirrorTreeNode[] | undefined;

  readonly onDidChangeTreeData = this.changed.event;

  constructor(
    private readonly currentWorkspace: () => Promise<WorkspaceNode | undefined>,
    private readonly mirrorsFor: (source: WorkspaceNode) => Promise<WorkspaceNode[]>
  ) {}

  async reload(): Promise<void> {
    this.cache = undefined;
    await this.nodes();
    this.changed.fire(undefined);
  }

  getTreeItem(node: RemoteMirrorTreeNode): vscode.TreeItem {
    if (node.kind === "message") {
      const item = new vscode.TreeItem(
        node.label,
        vscode.TreeItemCollapsibleState.None
      );
      item.description = node.description;
      item.iconPath = new vscode.ThemeIcon("info");
      item.contextValue = "remoteMirrorMessage";
      return item;
    }
    const reference = workspaceReference(node.mirror.workspace);
    const item = new vscode.TreeItem(
      node.mirror.host.alias,
      vscode.TreeItemCollapsibleState.None
    );
    item.description = `${node.mirror.workspace.repos.length} repos`;
    item.iconPath = new vscode.ThemeIcon("remote");
    item.contextValue = "remoteMirror";
    item.tooltip = new vscode.MarkdownString([
      `**${reference} on ${node.mirror.host.alias}**`,
      "",
      `Host: ${node.mirror.host.hostname}`,
      `Path: ${node.mirror.workspace.path}`,
      `Repositories: ${node.mirror.workspace.repos.length}`
    ].join("  \n"));
    item.command = {
      command: "genoTools.openWorkspaceInNewWindow",
      title: "Open Remote Mirror in New Window",
      arguments: [node.mirror]
    };
    return item;
  }

  async getChildren(node?: RemoteMirrorTreeNode): Promise<RemoteMirrorTreeNode[]> {
    return node ? [] : this.nodes();
  }

  dispose(): void {
    this.changed.dispose();
  }

  private async nodes(): Promise<RemoteMirrorTreeNode[]> {
    if (this.cache) {
      return this.cache;
    }
    const source = await this.currentWorkspace();
    const mirrors = source ? await this.mirrorsFor(source) : [];
    this.cache = source && mirrors.length > 0
      ? mirrors.map((mirror) => ({ kind: "remoteMirror", source, mirror }))
      : [{
          kind: "message",
          label: source ? "Not mirrored yet" : "Not a TT workspace",
          description: source
            ? "Use the remote button on the workspace row"
            : "Open a local TT workspace to create a mirror"
        }];
    await vscode.commands.executeCommand(
      "setContext",
      HAS_CURRENT_WORKSPACE_MIRROR,
      mirrors.length > 0
    );
    return this.cache;
  }
}
