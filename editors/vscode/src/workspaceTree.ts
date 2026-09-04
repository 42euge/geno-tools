import * as vscode from "vscode";

import {
  relativeAge,
  sortedTracks,
  TtHost,
  TtRegistry,
  TtRepo,
  TtWorkspace,
  workspaceReference
} from "./model";
import { TerminalLinkRegistry } from "./terminalLinks";
import {
  ManagedTmuxSessionStore,
  TmuxSessionView
} from "./tmuxSessions";
import { TtCli } from "./ttCli";

export type WorkspaceTreeNode =
  | HostNode
  | TrackNode
  | DomainNode
  | WorkspaceNode
  | RepoGroupNode
  | TmuxSessionGroupNode
  | TerminalGroupNode
  | RepoNode
  | TmuxSessionNode
  | TerminalNode
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

export interface RepoGroupNode {
  kind: "repoGroup";
  host: TtHost;
  registry: TtRegistry;
  workspace: TtWorkspace;
}

export interface TmuxSessionGroupNode {
  kind: "tmuxSessionGroup";
  host: TtHost;
  registry: TtRegistry;
  workspace: TtWorkspace;
}

export interface TerminalGroupNode {
  kind: "terminalGroup";
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
  session: TmuxSessionView;
}

export interface TerminalNode {
  kind: "terminal";
  host: TtHost;
  registry: TtRegistry;
  workspace: TtWorkspace;
  terminal: vscode.Terminal;
  cwd?: string;
  splitPrefix?: string;
}

export interface TerminalLayoutReader {
  readGroups(): Promise<number[][] | undefined>;
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

export function isRepoGroupNode(value: unknown): value is RepoGroupNode {
  return isNode(value) && value.kind === "repoGroup";
}

export function isTmuxSessionNode(value: unknown): value is TmuxSessionNode {
  return isNode(value) && value.kind === "tmuxSession";
}

export function isTmuxSessionGroupNode(
  value: unknown
): value is TmuxSessionGroupNode {
  return isNode(value) && value.kind === "tmuxSessionGroup";
}

export function isTerminalNode(value: unknown): value is TerminalNode {
  return isNode(value) && value.kind === "terminal";
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
  private readonly scannedHosts = new Set<string>();

  readonly onDidChangeTreeData = this.changed.event;

  constructor(
    private readonly cli: TtCli,
    private readonly scope: "all" | "current" = "all",
    private readonly terminalLinks = new TerminalLinkRegistry(),
    private readonly tmuxSessions = new ManagedTmuxSessionStore(),
    private readonly terminalLayout?: TerminalLayoutReader,
    private readonly terminalsByLayoutId = new Map<number, vscode.Terminal>()
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
    this.scannedHosts.clear();
    this.changed.fire(undefined);
  }

  refreshTerminals(): void {
    this.changed.fire(undefined);
  }

  invalidateHost(host: TtHost, liveStateAlreadyRefreshed = false): void {
    this.registryCache.delete(host.alias);
    if (liveStateAlreadyRefreshed) {
      this.scannedHosts.add(host.alias);
    } else {
      this.scannedHosts.delete(host.alias);
    }
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

  async remoteMirrorsFor(source: WorkspaceNode): Promise<WorkspaceNode[]> {
    const hosts = (await this.hosts()).filter(
      (host) =>
        host.alias !== source.host.alias &&
        host.hostname !== source.host.hostname
    );
    const results = await Promise.allSettled(
      hosts.map(async (host) => ({
        host,
        registry: await this.hostRegistry(host)
      }))
    );
    return results
      .flatMap((result) => {
        if (result.status === "rejected") {
          return [];
        }
        const { host, registry } = result.value;
        return registry.workspaces
          .filter((workspace) => workspace.id === source.workspace.id)
          .map((workspace) => ({
            kind: "workspace" as const,
            host,
            registry,
            workspace
          }));
      })
      .sort((left, right) => left.host.alias.localeCompare(right.host.alias));
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
        return workspaceItem(node, this.tmuxSessions);
      case "repoGroup":
        return repoGroupItem(node);
      case "tmuxSessionGroup":
        return tmuxSessionGroupItem(node, this.tmuxSessions);
      case "terminalGroup":
        return terminalGroupItem(node, this.terminalLinks);
      case "repo":
        return repoItem(node);
      case "tmuxSession":
        return tmuxSessionItem(node, this.terminalLinks);
      case "terminal":
        return terminalItem(node, this.terminalLinks);
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
          return await this.hostChildren(node.host);
        case "track":
          return trackChildren(node);
        case "domain":
          return domainChildren(node);
        case "workspace":
          return workspaceChildren(node);
        case "repoGroup":
          return repoGroupChildren(node);
        case "tmuxSessionGroup":
          return tmuxSessionGroupChildren(node, this.tmuxSessions);
        case "terminalGroup":
          return terminalGroupChildren(
            node,
            this.terminalLinks,
            this.terminalLayout,
            this.terminalsByLayoutId
          );
        case "repo":
          return [];
        case "tmuxSession":
        case "terminal":
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
      if (this.scannedHosts.has(host.alias)) {
        registry = await this.cli.registry(host);
      } else {
        registry = await this.cli.scanRegistry(host);
        this.scannedHosts.add(host.alias);
      }
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

function workspaceItem(
  node: WorkspaceNode,
  tmuxSessionStore: ManagedTmuxSessionStore
): vscode.TreeItem {
  const reference = workspaceReference(node.workspace);
  const tmuxSessions = tmuxSessionStore.forWorkspace(
    node.registry.host,
    node.workspace
  );
  const item = new vscode.TreeItem(
    reference,
    vscode.TreeItemCollapsibleState.Collapsed
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

function repoGroupItem(node: RepoGroupNode): vscode.TreeItem {
  const count = node.workspace.repos.length;
  const item = new vscode.TreeItem(
    "Repositories",
    count > 0
      ? vscode.TreeItemCollapsibleState.Collapsed
      : vscode.TreeItemCollapsibleState.None
  );
  item.contextValue = "repoGroup";
  item.description = `${count}`;
  item.tooltip = `${count} repositor${count === 1 ? "y" : "ies"}`;
  item.iconPath = new vscode.ThemeIcon("repo");
  return item;
}

function tmuxSessionGroupItem(
  node: TmuxSessionGroupNode,
  tmuxSessionStore: ManagedTmuxSessionStore
): vscode.TreeItem {
  const count = tmuxSessionStore.forWorkspace(
    node.registry.host,
    node.workspace
  ).length;
  const item = new vscode.TreeItem(
    "tmux Sessions",
    count > 0
      ? vscode.TreeItemCollapsibleState.Collapsed
      : vscode.TreeItemCollapsibleState.None
  );
  item.contextValue = "tmuxSessionGroup";
  item.description = `${count}`;
  item.tooltip = `${count} tmux session${count === 1 ? "" : "s"}`;
  item.iconPath = new vscode.ThemeIcon("terminal-tmux");
  return item;
}

function terminalGroupItem(
  node: TerminalGroupNode,
  terminalLinks: TerminalLinkRegistry
): vscode.TreeItem {
  const count = terminalsForWorkspace(node, terminalLinks).length;
  const item = new vscode.TreeItem(
    "VS Code Terminals",
    count > 0
      ? vscode.TreeItemCollapsibleState.Collapsed
      : vscode.TreeItemCollapsibleState.None
  );
  item.contextValue = "terminalGroup";
  item.description = `${count}`;
  item.tooltip = `${count} open VS Code terminal${count === 1 ? "" : "s"}`;
  item.iconPath = new vscode.ThemeIcon("terminal");
  return item;
}

function repoItem(node: RepoNode): vscode.TreeItem {
  const item = new vscode.TreeItem(
    node.repo.name,
    vscode.TreeItemCollapsibleState.None
  );
  item.contextValue = "repo";
  item.description = relativeAge(node.repo.last_accessed);
  item.tooltip = new vscode.MarkdownString(
    `**${node.repo.name}**  \n${node.host.alias}:${node.repo.path}  \nLast accessed ${relativeAge(node.repo.last_accessed)}`
  );
  item.iconPath = new vscode.ThemeIcon("repo");
  item.command = {
    command: "genoTools.openRepo",
    title: "Open TT Repository",
    arguments: [node]
  };
  return item;
}

function tmuxSessionItem(
  node: TmuxSessionNode,
  terminalLinks: TerminalLinkRegistry
): vscode.TreeItem {
  const openInVsCode = terminalLinks.hasAttachedTerminal(
    node.host.alias,
    node.session.session_name
  );
  const item = new vscode.TreeItem(
    node.session.session_name,
    vscode.TreeItemCollapsibleState.None
  );
  item.contextValue = `tmuxSession.${node.session.lifecycle}`;
  item.description = node.session.lifecycle === "stopped"
    ? "Stopped"
    : `${node.session.pane_current_command}${
        node.session.lifecycle === "external" ? " · External" : ""
      }${openInVsCode ? " · VS Code" : ""}`;
  const stateDescription = node.session.lifecycle === "stopped"
    ? "Managed session is stopped"
    : node.session.lifecycle === "external"
      ? "External live session; choose Manage before lifecycle actions"
      : `Running ${node.session.pane_current_command}`;
  item.tooltip = new vscode.MarkdownString(
    `**${node.session.session_name}**  \n${node.host.alias}:${node.session.pane_current_path}  \n${stateDescription}${
      openInVsCode ? "  \nAttached in a VS Code terminal" : ""
    }`
  );
  item.iconPath = new vscode.ThemeIcon(
    node.session.lifecycle === "stopped" ? "debug-stop" : "terminal-tmux"
  );
  item.command = node.session.lifecycle === "stopped"
    ? {
        command: "genoTools.restoreTmuxSession",
        title: "Restore tmux Session",
        arguments: [node]
      }
    : {
        command: "genoTools.openTmuxSession",
        title: "Reopen tmux Session",
        arguments: [node]
      };
  return item;
}

function terminalItem(
  node: TerminalNode,
  terminalLinks: TerminalLinkRegistry
): vscode.TreeItem {
  const link = terminalLinks.linkFor(node.terminal);
  const location = node.cwd ?? "working directory unavailable";
  const item = new vscode.TreeItem(
    `${node.splitPrefix ? `${node.splitPrefix} ` : ""}${node.terminal.name}`,
    vscode.TreeItemCollapsibleState.None
  );
  item.contextValue = link ? "terminalLinked" : "terminal";
  item.description = link
    ? `${location} · tmux: ${link.sessionName}`
    : location;
  item.tooltip = new vscode.MarkdownString(
    `**${node.terminal.name}**  \n${node.cwd ?? "Working directory unavailable"}${
      link
        ? `  \nLinked to ${link.hostAlias}/${link.sessionName}${
            link.kind === "attached" ? " (attached)" : " (recovery source)"
          }`
        : "  \nNot linked to tmux"
    }`
  );
  item.iconPath = new vscode.ThemeIcon(link ? "link" : "terminal");
  item.command = {
    command: "genoTools.focusTerminal",
    title: "Focus VS Code Terminal",
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
): Array<RepoGroupNode | TmuxSessionGroupNode | TerminalGroupNode> {
  return [
    {
      kind: "repoGroup",
      host: node.host,
      registry: node.registry,
      workspace: node.workspace
    },
    {
      kind: "tmuxSessionGroup",
      host: node.host,
      registry: node.registry,
      workspace: node.workspace
    },
    {
      kind: "terminalGroup",
      host: node.host,
      registry: node.registry,
      workspace: node.workspace
    }
  ];
}

function repoGroupChildren(node: RepoGroupNode): RepoNode[] {
  return [...node.workspace.repos]
    .sort((left, right) => left.name.localeCompare(right.name))
    .map((repo) => ({
      kind: "repo" as const,
      host: node.host,
      registry: node.registry,
      workspace: node.workspace,
      repo
    }));
}

function tmuxSessionGroupChildren(
  node: TmuxSessionGroupNode,
  tmuxSessionStore: ManagedTmuxSessionStore
): TmuxSessionNode[] {
  return tmuxSessionStore
    .forWorkspace(node.registry.host, node.workspace)
    .map((session) => tmuxSessionNode(node, session));
}

async function terminalGroupChildren(
  node: TerminalGroupNode,
  terminalLinks: TerminalLinkRegistry,
  terminalLayout: TerminalLayoutReader | undefined,
  terminalsByLayoutId: Map<number, vscode.Terminal>
): Promise<TerminalNode[]> {
  const displayTerminals = reconcileTerminalLayout(
    await terminalLayout?.readGroups(),
    vscode.window.terminals,
    terminalsByLayoutId
  );
  return terminalsForWorkspace(node, terminalLinks, displayTerminals)
    .map(({ terminal, cwd, splitPrefix }) => ({
      kind: "terminal",
      host: node.host,
      registry: node.registry,
      workspace: node.workspace,
      terminal,
      cwd,
      splitPrefix
    }));
}

interface DisplayTerminal {
  terminal: vscode.Terminal;
  splitPrefix?: string;
}

function terminalsForWorkspace(
  node: TerminalGroupNode,
  terminalLinks: TerminalLinkRegistry,
  displayTerminals: DisplayTerminal[] = vscode.window.terminals.map(
    (terminal) => ({ terminal })
  )
): Array<DisplayTerminal & { cwd?: string }> {
  const currentLocations = currentWorkspaceLocations();
  return displayTerminals.flatMap((displayTerminal) => {
    const { terminal } = displayTerminal;
    const location = terminalLocation(terminal);
    const link = terminalLinks.linkFor(terminal);
    const linkedToWorkspace = link?.hostAlias === node.host.alias &&
      node.workspace.state.tmux.sessions.some(
        ({ session_name }) => session_name === link.sessionName
      );
    const belongs = linkedToWorkspace || (location
      ? locationMatchesHost(location, node.host, node.registry) &&
        pathIsInside(location.path, node.workspace.path)
      : currentLocations.some(
          (current) =>
            locationMatchesHost(current, node.host, node.registry) &&
            pathIsInside(current.path, node.workspace.path)
        ));
    return belongs ? [{ ...displayTerminal, cwd: location?.path }] : [];
  });
}

function reconcileTerminalLayout(
  groups: number[][] | undefined,
  terminals: readonly vscode.Terminal[],
  terminalsByLayoutId: Map<number, vscode.Terminal>
): DisplayTerminal[] {
  const fallback = terminals.map((terminal) => ({ terminal }));
  if (!groups) {
    return fallback;
  }
  const layoutIds = groups.flat();
  if (
    groups.some((group) => group.length === 0) ||
    new Set(layoutIds).size !== layoutIds.length ||
    layoutIds.length > terminals.length
  ) {
    return fallback;
  }

  const liveIds = new Set(layoutIds);
  const liveTerminals = new Set(terminals);
  for (const [layoutId, terminal] of terminalsByLayoutId) {
    if (!liveIds.has(layoutId) || !liveTerminals.has(terminal)) {
      terminalsByLayoutId.delete(layoutId);
    }
  }

  const mappedTerminals = new Set(terminalsByLayoutId.values());
  const unmappedIds = layoutIds.filter((id) => !terminalsByLayoutId.has(id));
  const unmappedTerminals = terminals.filter(
    (terminal) => !mappedTerminals.has(terminal)
  );
  if (unmappedIds.length > unmappedTerminals.length) {
    return fallback;
  }
  unmappedIds.forEach((id, index) => {
    terminalsByLayoutId.set(id, unmappedTerminals[index]);
  });

  const layoutTerminals = groups.flatMap((group) =>
    group.flatMap((id, index) => {
      const terminal = terminalsByLayoutId.get(id);
      if (!terminal) {
        return [];
      }
      const splitPrefix = group.length <= 1
        ? undefined
        : index === 0
          ? "┌"
          : index === group.length - 1
            ? "└"
            : "├";
      return [{ terminal, splitPrefix }];
    })
  );
  const terminalsInLayout = new Set(
    layoutTerminals.map(({ terminal }) => terminal)
  );
  const extraTerminals = terminals
    .filter((terminal) => !terminalsInLayout.has(terminal))
    .map((terminal) => ({ terminal }));
  return [...layoutTerminals, ...extraTerminals];
}

function terminalLocation(terminal: vscode.Terminal): WorkspaceLocation | undefined {
  const shellCwd = terminal.shellIntegration?.cwd;
  if (shellCwd) {
    return uriLocation(shellCwd);
  }
  const options = terminal.creationOptions;
  if (!("cwd" in options) || options.cwd === undefined) {
    return undefined;
  }
  return typeof options.cwd === "string"
    ? {
        path: options.cwd,
        remote: currentWorkspaceLocations().find(({ remote }) => remote)?.remote
      }
    : uriLocation(options.cwd);
}

function uriLocation(uri: vscode.Uri): WorkspaceLocation {
  return {
    path: uri.scheme === "file" ? uri.fsPath : uri.path,
    remote: remoteName(uri)
  };
}

function tmuxSessionNode(
  parent: TmuxSessionGroupNode,
  session: TmuxSessionView
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
