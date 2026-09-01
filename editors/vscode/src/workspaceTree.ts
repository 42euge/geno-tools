import * as vscode from "vscode";

import {
  relativeAge,
  sortedTracks,
  TtHost,
  TtRegistry,
  TtRepo,
  TtTmuxSession,
  TtWorkspace,
  workspaceReference
} from "./model";
import { TtCli } from "./ttCli";

export type WorkspaceTreeNode =
  | HostNode
  | TrackNode
  | DomainNode
  | WorkspaceNode
  | RepoNode
  | TmuxSessionNode
  | MessageNode;

export interface HostNode {
  kind: "host";
  host: TtHost;
}

export interface TrackNode {
  kind: "track";
  host: TtHost;
  registry: TtRegistry;
  track: string;
}

export interface DomainNode {
  kind: "domain";
  host: TtHost;
  registry: TtRegistry;
  track: string;
  domain: string;
}

export interface WorkspaceNode {
  kind: "workspace";
  host: TtHost;
  registry: TtRegistry;
  workspace: TtWorkspace;
}

export interface RepoNode {
  kind: "repo";
  host: TtHost;
  registry: TtRegistry;
  workspace: TtWorkspace;
  repo: TtRepo;
}

export interface TmuxSessionNode {
  kind: "tmuxSession";
  host: TtHost;
  registry: TtRegistry;
  workspace: TtWorkspace;
  session: TtTmuxSession;
}

export interface MessageNode {
  kind: "message";
  label: string;
  description?: string;
  icon?: string;
}

export function isWorkspaceNode(value: unknown): value is WorkspaceNode {
  return isNode(value) && value.kind === "workspace";
}

export function isRepoNode(value: unknown): value is RepoNode {
  return isNode(value) && value.kind === "repo";
}

export function isTmuxSessionNode(value: unknown): value is TmuxSessionNode {
  return isNode(value) && value.kind === "tmuxSession";
}

export function isHostNode(value: unknown): value is HostNode {
  return isNode(value) && value.kind === "host";
}

export class WorkspaceTreeProvider
  implements vscode.TreeDataProvider<WorkspaceTreeNode>
{
  private readonly changed = new vscode.EventEmitter<WorkspaceTreeNode | undefined>();
  private hostsCache: TtHost[] | undefined;
  private readonly registryCache = new Map<string, TtRegistry>();

  readonly onDidChangeTreeData = this.changed.event;

  constructor(
    private readonly cli: TtCli,
    private readonly scope: "all" | "current" = "all"
  ) {}

  async hosts(reload = false): Promise<TtHost[]> {
    if (reload || !this.hostsCache) {
      this.hostsCache = await this.cli.hosts();
    }
    return this.hostsCache;
  }

  reload(): void {
    this.hostsCache = undefined;
    this.registryCache.clear();
    this.changed.fire(undefined);
  }

  invalidateHost(host: TtHost): void {
    this.registryCache.delete(host.alias);
    this.changed.fire(this.scope === "all" ? { kind: "host", host } : undefined);
  }

  async currentWorkspace(): Promise<WorkspaceNode | undefined> {
    const locations = currentWorkspaceLocations();
    if (locations.length === 0) {
      return undefined;
    }
    const results = await Promise.allSettled(
      (await this.hosts()).map(async (host) => ({
        host,
        registry: await this.hostRegistry(host)
      }))
    );
    const matches = results.flatMap((result) => {
      if (result.status === "rejected") {
        return [];
      }
      const { host, registry } = result.value;
      return registry.workspaces
        .filter((workspace) =>
          locations.some(
            (location) =>
              locationMatchesHost(location, host, registry) &&
              pathIsInside(location.path, workspace.path)
          )
        )
        .map((workspace) => ({
          kind: "workspace" as const,
          host,
          registry,
          workspace
        }));
    });
    return matches.sort(
      (left, right) => right.workspace.path.length - left.workspace.path.length
    )[0];
  }

  getTreeItem(node: WorkspaceTreeNode): vscode.TreeItem {
    switch (node.kind) {
      case "host":
        return hostItem(node);
      case "track":
        return trackItem(node);
      case "domain":
        return domainItem(node);
      case "workspace":
        return workspaceItem(node);
      case "repo":
        return repoItem(node);
      case "tmuxSession":
        return tmuxSessionItem(node);
      case "message":
        return messageItem(node);
    }
  }

  async getChildren(node?: WorkspaceTreeNode): Promise<WorkspaceTreeNode[]> {
    try {
      if (!node) {
        if (this.scope === "current") {
          const current = await this.currentWorkspace();
          return current
            ? [current]
            : [{
                kind: "message",
                label: "Not a TT workspace",
                description: "No registry match for this window",
                icon: "info"
              }];
        }
        return (await this.hosts()).map((host) => ({ kind: "host", host }));
      }
      switch (node.kind) {
        case "host":
          return this.hostChildren(node.host);
        case "track":
          return trackChildren(node);
        case "domain":
          return domainChildren(node);
        case "workspace":
          return workspaceChildren(node);
        case "repo":
          return repoChildren(node);
        case "tmuxSession":
        case "message":
          return [];
      }
    } catch (error) {
      return [
        {
          kind: "message",
          label: error instanceof Error ? error.message : String(error),
          description: "See Geno Tools output",
          icon: "error"
        }
      ];
    }
  }

  dispose(): void {
    this.changed.dispose();
  }

  private async hostChildren(host: TtHost): Promise<WorkspaceTreeNode[]> {
    const registry = await this.hostRegistry(host);
    if (registry.workspaces.length === 0) {
      return [
        {
          kind: "message",
          label: "No TT workspaces",
          description: "Create one with the + button",
          icon: "info"
        }
      ];
    }
    return sortedTracks(registry.workspaces).map((track) => ({
      kind: "track",
      host,
      registry,
      track
    }));
  }

  private async hostRegistry(host: TtHost): Promise<TtRegistry> {
    let registry = this.registryCache.get(host.alias);
    if (!registry) {
      registry = await this.cli.registry(host);
      this.registryCache.set(host.alias, registry);
    }
    return registry;
  }
}

interface WorkspaceLocation {
  path: string;
  remote?: string;
}

function currentWorkspaceLocations(): WorkspaceLocation[] {
  const locations = (vscode.workspace.workspaceFolders ?? []).map(({ uri }) => ({
    path: uri.scheme === "file" ? uri.fsPath : uri.path,
    remote: remoteName(uri)
  }));
  const workspaceFile = vscode.workspace.workspaceFile;
  if (workspaceFile) {
    const path = workspaceFile.scheme === "file" ? workspaceFile.fsPath : workspaceFile.path;
    const separator = path.lastIndexOf("/");
    locations.push({
      path: separator > 0 ? path.slice(0, separator) : path,
      remote: remoteName(workspaceFile)
    });
  }
  return locations;
}

function remoteName(uri: vscode.Uri): string | undefined {
  if (uri.scheme !== "vscode-remote") {
    return undefined;
  }
  return decodeURIComponent(uri.authority).replace(/^ssh-remote\+/, "");
}

function locationMatchesHost(
  location: WorkspaceLocation,
  host: TtHost,
  registry: TtRegistry
): boolean {
  if (location.remote) {
    return [host.alias, host.hostname, registry.host].includes(location.remote);
  }
  return host.hostname === "localhost" || registry.host === "localhost";
}

function pathIsInside(path: string, workspacePath: string): boolean {
  const root = workspacePath.replace(/\/+$/, "");
  const candidate = path.replace(/\/+$/, "");
  return candidate === root || candidate.startsWith(`${root}/`);
}

function hostItem(node: HostNode): vscode.TreeItem {
  const item = new vscode.TreeItem(
    node.host.alias,
    node.host.isDefault
      ? vscode.TreeItemCollapsibleState.Expanded
      : vscode.TreeItemCollapsibleState.Collapsed
  );
  item.contextValue = "host";
  item.description = `${node.host.hostname}${node.host.isDefault ? " · default" : ""}`;
  item.tooltip = new vscode.MarkdownString(
    `**${node.host.alias}**  \n${node.host.hostname}${node.host.isDefault ? "  \nDefault TT host" : ""}`
  );
  item.iconPath = new vscode.ThemeIcon(
    node.host.hostname === "localhost" ? "device-desktop" : "remote"
  );
  return item;
}

function trackItem(node: TrackNode): vscode.TreeItem {
  const count = node.registry.workspaces.filter(
    (workspace) => workspace.track === node.track
  ).length;
  const item = new vscode.TreeItem(
    node.track,
    vscode.TreeItemCollapsibleState.Collapsed
  );
  item.contextValue = "track";
  item.description = `${count} workspace${count === 1 ? "" : "s"}`;
  item.iconPath = new vscode.ThemeIcon(trackIcon(node.track));
  return item;
}

function domainItem(node: DomainNode): vscode.TreeItem {
  const count = node.registry.workspaces.filter(
    (workspace) =>
      workspace.track === node.track && workspace.domain === node.domain
  ).length;
  const item = new vscode.TreeItem(
    node.domain,
    vscode.TreeItemCollapsibleState.Collapsed
  );
  item.contextValue = "domain";
  item.description = `${count}`;
  item.iconPath = new vscode.ThemeIcon("folder-library");
  return item;
}

function workspaceItem(node: WorkspaceNode): vscode.TreeItem {
  const reference = workspaceReference(node.workspace);
  const tmuxSessions = node.workspace.state.tmux.sessions;
  const item = new vscode.TreeItem(
    reference,
    node.workspace.repos.length > 0 || tmuxSessions.length > 0
      ? vscode.TreeItemCollapsibleState.Collapsed
      : vscode.TreeItemCollapsibleState.None
  );
  item.contextValue = "workspace";
  item.description = `${node.workspace.repos.length} repo${
    node.workspace.repos.length === 1 ? "" : "s"
  } · ${tmuxSessions.length} tmux`;
  item.tooltip = new vscode.MarkdownString(
    `**${node.workspace.id}**  \n${node.host.alias}:${node.workspace.path}  \n${node.workspace.repos.length} repositories  \n${
      tmuxSessions.length > 0
        ? `tmux: ${tmuxSessions.map((session) => session.session_name).join(", ")}`
        : "tmux: no registered session"
    }`
  );
  item.iconPath = new vscode.ThemeIcon("root-folder");
  item.command = {
    command: "genoTools.openWorkspace",
    title: "Open TT Workspace",
    arguments: [node]
  };
  return item;
}

function repoItem(node: RepoNode): vscode.TreeItem {
  const tmuxSessions = sessionsForRepo(node.workspace, node.repo);
  const item = new vscode.TreeItem(
    node.repo.name,
    tmuxSessions.length > 0
      ? vscode.TreeItemCollapsibleState.Collapsed
      : vscode.TreeItemCollapsibleState.None
  );
  item.contextValue = "repo";
  item.description = `${relativeAge(node.repo.last_accessed)}${
    tmuxSessions.length > 0 ? ` · ${tmuxSessions.length} tmux` : ""
  }`;
  item.tooltip = new vscode.MarkdownString(
    `**${node.repo.name}**  \n${node.host.alias}:${node.repo.path}  \nLast accessed ${relativeAge(node.repo.last_accessed)}${
      tmuxSessions.length > 0
        ? `  \ntmux: ${tmuxSessions.map((session) => session.session_name).join(", ")}`
        : ""
    }`
  );
  item.iconPath = new vscode.ThemeIcon("repo");
  item.command = {
    command: "genoTools.openRepo",
    title: "Open TT Repository",
    arguments: [node]
  };
  return item;
}

function tmuxSessionItem(node: TmuxSessionNode): vscode.TreeItem {
  const item = new vscode.TreeItem(
    node.session.session_name,
    vscode.TreeItemCollapsibleState.None
  );
  item.contextValue = "tmuxSession";
  item.description = node.session.pane_current_command;
  item.tooltip = new vscode.MarkdownString(
    `**${node.session.session_name}**  \n${node.host.alias}:${node.session.pane_current_path}  \nRunning ${node.session.pane_current_command}`
  );
  item.iconPath = new vscode.ThemeIcon("terminal-tmux");
  item.command = {
    command: "genoTools.openTmuxSession",
    title: "Reopen tmux Session",
    arguments: [node]
  };
  return item;
}

function messageItem(node: MessageNode): vscode.TreeItem {
  const item = new vscode.TreeItem(node.label, vscode.TreeItemCollapsibleState.None);
  item.contextValue = "message";
  item.description = node.description;
  item.tooltip = node.label;
  item.iconPath = new vscode.ThemeIcon(node.icon ?? "info");
  return item;
}

function trackChildren(node: TrackNode): DomainNode[] {
  const domains = new Set(
    node.registry.workspaces
      .filter((workspace) => workspace.track === node.track)
      .map((workspace) => workspace.domain)
  );
  return Array.from(domains)
    .sort()
    .map((domain) => ({
      kind: "domain",
      host: node.host,
      registry: node.registry,
      track: node.track,
      domain
    }));
}

function domainChildren(node: DomainNode): WorkspaceNode[] {
  return node.registry.workspaces
    .filter(
      (workspace) =>
        workspace.track === node.track && workspace.domain === node.domain
    )
    .sort((left, right) => workspaceReference(left).localeCompare(workspaceReference(right)))
    .map((workspace) => ({
      kind: "workspace",
      host: node.host,
      registry: node.registry,
      workspace
    }));
}

function workspaceChildren(
  node: WorkspaceNode
): Array<TmuxSessionNode | RepoNode> {
  const sessions = node.workspace.state.tmux.sessions
    .filter((session) => !repoForSession(node.workspace, session))
    .sort((left, right) => left.session_name.localeCompare(right.session_name))
    .map((session) => tmuxSessionNode(node, session));
  const repos = [...node.workspace.repos]
    .sort((left, right) => left.name.localeCompare(right.name))
    .map((repo) => ({
      kind: "repo" as const,
      host: node.host,
      registry: node.registry,
      workspace: node.workspace,
      repo
    }));
  return [...sessions, ...repos];
}

function repoChildren(node: RepoNode): TmuxSessionNode[] {
  return sessionsForRepo(node.workspace, node.repo)
    .sort((left, right) => left.session_name.localeCompare(right.session_name))
    .map((session) => tmuxSessionNode(node, session));
}

function sessionsForRepo(
  workspace: TtWorkspace,
  repo: TtRepo
): TtTmuxSession[] {
  return workspace.state.tmux.sessions.filter(
    (session) => repoForSession(workspace, session)?.path === repo.path
  );
}

function repoForSession(
  workspace: TtWorkspace,
  session: TtTmuxSession
): TtRepo | undefined {
  return workspace.repos
    .filter((repo) => pathIsInside(session.pane_current_path, repo.path))
    .sort((left, right) => right.path.length - left.path.length)[0];
}

function tmuxSessionNode(
  parent: WorkspaceNode | RepoNode,
  session: TtTmuxSession
): TmuxSessionNode {
  return {
    kind: "tmuxSession",
    host: parent.host,
    registry: parent.registry,
    workspace: parent.workspace,
    session
  };
}

function trackIcon(track: string): string {
  switch (track) {
    case "crit":
      return "flame";
    case "explore":
      return "compass";
    case "chore":
      return "tools";
    case "side":
      return "beaker";
    default:
      return "symbol-folder";
  }
}

function isNode(value: unknown): value is WorkspaceTreeNode {
  return typeof value === "object" && value !== null && "kind" in value;
}
