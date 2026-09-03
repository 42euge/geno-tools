import { readdir } from "node:fs/promises";
import { homedir } from "node:os";
import { basename, join } from "node:path";

import * as vscode from "vscode";

import { loadAgentRuntimeConfig } from "./agentConfig";
import {
  captureTerminalHistory,
  proposeRecovery,
  RecoveryContext,
  RecoveryProposal
} from "./agentRecovery";
import {
  AgentSessionMatch,
  agentResumeCommand,
  findAgentSessionMatches
} from "./agentSessions";
import { TRACK_ORDER, TtHost, TtWorkspace, workspaceReference } from "./model";
import { TerminalLinkRegistry } from "./terminalLinks";
import {
  ManagedTmuxSession,
  ManagedTmuxSessionStore
} from "./tmuxSessions";
import { TtCli } from "./ttCli";
import {
  HostNode,
  isHostNode,
  isRepoGroupNode,
  isRepoNode,
  isTerminalNode,
  isTmuxSessionGroupNode,
  isTmuxSessionNode,
  isWorkspaceNode,
  RepoGroupNode,
  RepoNode,
  TmuxSessionGroupNode,
  TmuxSessionNode,
  TerminalNode,
  WorkspaceNode,
  WorkspaceTreeProvider
} from "./workspaceTree";

const SAFE_SEGMENT = /^[a-z0-9][a-z0-9-]*$/;
const SAFE_REPO = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
const SAFE_WORKTREE = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
const SAFE_TMUX_SESSION = /^[A-Za-z0-9][A-Za-z0-9_-]*$/;

export function activate(context: vscode.ExtensionContext): void {
  const output = vscode.window.createOutputChannel("Geno Tools: TT");
  const cli = new TtCli(output);
  const terminalLinks = new TerminalLinkRegistry();
  const tmuxSessions = new ManagedTmuxSessionStore(context.globalState);
  const provider = new WorkspaceTreeProvider(
    cli,
    "all",
    terminalLinks,
    tmuxSessions
  );
  const currentProvider = new WorkspaceTreeProvider(
    cli,
    "current",
    terminalLinks,
    tmuxSessions
  );
  const tree = vscode.window.createTreeView("genoTools.workspaces", {
    treeDataProvider: provider,
    showCollapseAll: true
  });
  const currentTree = vscode.window.createTreeView("genoTools.currentWorkspace", {
    treeDataProvider: currentProvider
  });
  const buildDescription = extensionBuildDescription(context);
  tree.description = buildDescription;
  currentTree.description = buildDescription;
  const refreshTerminalViews = (): void => {
    provider.refreshTerminals();
    currentProvider.refreshTerminals();
  };

  context.subscriptions.push(
    output,
    terminalLinks,
    provider,
    currentProvider,
    tree,
    currentTree,
    vscode.workspace.onDidChangeWorkspaceFolders(() => currentProvider.reload()),
    vscode.window.onDidOpenTerminal(refreshTerminalViews),
    vscode.window.onDidCloseTerminal((terminal) => {
      terminalLinks.forget(terminal);
      refreshTerminalViews();
    }),
    vscode.window.onDidChangeTerminalShellIntegration(refreshTerminalViews)
  );
  register(context, "genoTools.reloadWorkspaces", async () => {
    provider.reload();
    currentProvider.reload();
  });
  register(context, "genoTools.refreshWorkspaces", async (node?: unknown) => {
    const host = isHostNode(node) ? node.host : undefined;
    await refreshWorkspaces(cli, [provider, currentProvider], host);
  });
  register(context, "genoTools.refreshTerminals", async () => {
    refreshTerminalViews();
  });
  register(context, "genoTools.createWorkspace", async (node?: unknown) => {
    await createWorkspace(
      cli,
      [provider, currentProvider],
      isHostNode(node) ? node.host : undefined
    );
  });
  register(context, "genoTools.createTmuxSession", async (node?: unknown) => {
    const selected = isTmuxSessionGroupNode(node) || isWorkspaceNode(node)
      ? node
      : undefined;
    const workspace = selected ??
      tree.selection.find(isWorkspaceNode) ??
      currentTree.selection.find(isWorkspaceNode) ??
      (await currentProvider.currentWorkspace()) ??
      (await pickWorkspace(cli, provider));
    if (workspace) {
      await createTmuxSession(
        cli,
        [provider, currentProvider],
        terminalLinks,
        tmuxSessions,
        workspace
      );
    }
  });
  register(context, "genoTools.createRepo", async (node?: unknown) => {
    const workspace = (isRepoGroupNode(node) ? node : undefined) ??
      tree.selection.find(isRepoGroupNode) ??
      currentTree.selection.find(isRepoGroupNode) ??
      (await currentProvider.currentWorkspace()) ??
      (await pickWorkspace(cli, provider));
    if (workspace) {
      await createRepo(cli, [provider, currentProvider], workspace);
    }
  });
  register(context, "genoTools.openTmuxSession", async (node?: unknown) => {
    if (isTmuxSessionNode(node)) {
      await openTmuxSession(cli, terminalLinks, node);
      refreshTerminalViews();
    }
  });
  register(context, "genoTools.manageTmuxSession", async (node?: unknown) => {
    if (isTmuxSessionNode(node)) {
      await manageTmuxSession(tmuxSessions, [provider, currentProvider], node);
    }
  });
  register(context, "genoTools.restoreTmuxSession", async (node?: unknown) => {
    if (isTmuxSessionNode(node)) {
      await restoreTmuxSession(
        cli,
        [provider, currentProvider],
        terminalLinks,
        tmuxSessions,
        node
      );
    }
  });
  register(context, "genoTools.deleteTmuxSession", async (node?: unknown) => {
    if (isTmuxSessionNode(node)) {
      await removeTmuxSession(
        cli,
        [provider, currentProvider],
        terminalLinks,
        tmuxSessions,
        node
      );
    }
  });
  register(context, "genoTools.focusTerminal", async (node?: unknown) => {
    if (isTerminalNode(node)) {
      node.terminal.show();
    }
  });
  register(context, "genoTools.recoverTerminalInTmux", async (node?: unknown) => {
    if (isTerminalNode(node)) {
      await recoverTerminalInTmux(
        cli,
        [provider, currentProvider],
        terminalLinks,
        tmuxSessions,
        node
      );
    }
  });
  register(context, "genoTools.openWorkspace", async (node?: unknown) => {
    const workspace = isWorkspaceNode(node) ? node : await pickWorkspace(cli, provider);
    if (workspace) {
      await openWorkspace(workspace, false);
    }
  });
  register(context, "genoTools.openWorkspaceInNewWindow", async (node?: unknown) => {
    const workspace = isWorkspaceNode(node) ? node : await pickWorkspace(cli, provider);
    if (workspace) {
      await openWorkspace(workspace, true);
    }
  });
  register(context, "genoTools.openRepo", async (node?: unknown) => {
    const repo = isRepoNode(node) ? node : await pickRepo(cli, provider);
    if (repo) {
      await openPath(repo.host, repo.registry.host, repo.repo.path);
    }
  });
  register(context, "genoTools.copyPath", async (node?: unknown) => {
    const path = isWorkspaceNode(node)
      ? node.workspace.path
      : isRepoNode(node)
        ? node.repo.path
        : undefined;
    if (!path) {
      return;
    }
    await vscode.env.clipboard.writeText(path);
    void vscode.window.setStatusBarMessage(`Copied ${path}`, 2500);
  });
  register(context, "genoTools.mirrorWorkspace", async (node?: unknown) => {
    const workspace = isWorkspaceNode(node) ? node : await pickWorkspace(cli, provider);
    if (workspace) {
      await mirrorWorkspace(cli, provider, workspace);
    }
  });
  register(context, "genoTools.createWorktree", async (node?: unknown) => {
    const workspace = isWorkspaceNode(node) ? node : await pickWorkspace(cli, provider);
    if (workspace) {
      await createWorktree(cli, workspace);
    }
  });
  register(context, "genoTools.listWorktrees", async (node?: unknown) => {
    const workspace = isWorkspaceNode(node) ? node : await pickWorkspace(cli, provider);
    if (workspace) {
      await listWorktrees(cli, workspace);
    }
  });
  register(context, "genoTools.removeWorktree", async (node?: unknown) => {
    const workspace = isWorkspaceNode(node) ? node : await pickWorkspace(cli, provider);
    if (workspace) {
      await removeWorktree(cli, workspace);
    }
  });
  register(context, "genoTools.showReport", async () => {
    await cli.run(["report", "--all-hosts"], "Building TT workspace report");
  });
  register(context, "genoTools.showOutput", async () => cli.showOutput());
}

export function deactivate(): void {}

function extensionBuildDescription(context: vscode.ExtensionContext): string {
  const version = typeof __GENO_TOOLS_VERSION__ === "string"
    ? __GENO_TOOLS_VERSION__
    : String(context.extension?.packageJSON?.version ?? "development");
  const builtAt = typeof __GENO_TOOLS_BUILD_DATETIME__ === "string"
    ? __GENO_TOOLS_BUILD_DATETIME__
    : "development";
  return `v${version} · built ${builtAt}`;
}

function register(
  context: vscode.ExtensionContext,
  command: string,
  callback: (...args: unknown[]) => Promise<unknown>
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand(command, async (...args: unknown[]) => {
      try {
        return await callback(...args);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        const action = await vscode.window.showErrorMessage(message, "Show TT Output");
        if (action) {
          await vscode.commands.executeCommand("genoTools.showOutput");
        }
        return undefined;
      }
    })
  );
}

async function refreshWorkspaces(
  cli: TtCli,
  providers: readonly WorkspaceTreeProvider[],
  selected?: TtHost
): Promise<void> {
  const hosts = selected ? [selected] : await providers[0].hosts(true);
  const failures: string[] = [];
  for (const host of hosts) {
    try {
      await cli.refreshRegistry(host);
      for (const provider of providers) {
        provider.invalidateHost(host, true);
      }
    } catch (error) {
      failures.push(`${host.alias}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  if (failures.length > 0) {
    throw new Error(`Some TT hosts could not be scanned:\n${failures.join("\n")}`);
  }
}

async function createWorkspace(
  cli: TtCli,
  providers: readonly WorkspaceTreeProvider[],
  selectedHost?: TtHost
): Promise<void> {
  const provider = providers[0];
  const host = selectedHost ?? (await pickHost(provider, "Create workspace on which host?"));
  if (!host) {
    return;
  }
  const track = await vscode.window.showQuickPick([...TRACK_ORDER], {
    title: "Create TT Workspace",
    placeHolder: "Choose a track"
  });
  if (!track) {
    return;
  }
  const domain = await segmentInput("Domain", "e.g. geno or ngrt");
  if (!domain) {
    return;
  }
  const name = await segmentInput("Workspace name", "e.g. tools-cleanup");
  if (!name) {
    return;
  }
  const repo = await vscode.window.showInputBox({
    title: "Create TT Workspace",
    prompt: "Initial repository directory (optional; defaults to the workspace name)",
    placeHolder: name,
    validateInput: (value) =>
      value.length === 0 || SAFE_SEGMENT.test(value)
        ? undefined
        : "Use lowercase letters, digits, and hyphens."
  });
  if (repo === undefined) {
    return;
  }

  const spec = [track, domain, name, repo || undefined].filter(Boolean).join(".");
  await cli.run(
    cli.forHost(host, ["new-project", spec]),
    `Creating ${track}.${domain}.${name} on ${host.alias}`
  );
  await cli.refreshRegistry(host);
  for (const one of providers) {
    one.invalidateHost(host, true);
  }
}

async function createRepo(
  cli: TtCli,
  providers: readonly WorkspaceTreeProvider[],
  node: WorkspaceNode | RepoGroupNode
): Promise<void> {
  const name = await vscode.window.showInputBox({
    title: `Create Repository in ${workspaceReference(node.workspace)}`,
    prompt: "Enter a name for the empty Git repository",
    placeHolder: node.workspace.name,
    validateInput: (value) => {
      const candidate = value.trim();
      if (!SAFE_REPO.test(candidate)) {
        return "Use letters, digits, periods, hyphens, or underscores.";
      }
      return node.workspace.repos.some((repo) => repo.name === candidate)
        ? `Repository '${candidate}' already exists in this workspace.`
        : undefined;
    }
  });
  if (!name) {
    return;
  }
  await cli.createRepository(
    node.host,
    node.registry.host,
    node.workspace.path,
    name.trim()
  );
  await cli.refreshRegistry(node.host);
  for (const provider of providers) {
    provider.invalidateHost(node.host, true);
  }
}

async function createTmuxSession(
  cli: TtCli,
  providers: readonly WorkspaceTreeProvider[],
  terminalLinks: TerminalLinkRegistry,
  tmuxSessions: ManagedTmuxSessionStore,
  node: WorkspaceNode | TmuxSessionGroupNode
): Promise<void> {
  const reference = workspaceReference(node.workspace);
  const knownSessions = tmuxSessions.forWorkspace(
    node.registry.host,
    node.workspace
  );
  const input = await vscode.window.showInputBox({
    title: `New tmux Session in ${reference}`,
    prompt: "Enter a session name, or leave blank to generate the next available name",
    placeHolder: nextTmuxSessionName(node.workspace, knownSessions),
    validateInput: (value) => {
      const name = value.trim();
      return name.length === 0 || SAFE_TMUX_SESSION.test(name)
        ? undefined
        : "Use letters, digits, hyphens, or underscores; periods and colons are not allowed.";
    }
  });
  if (input === undefined) {
    return;
  }
  const sessionName = input.trim() || nextTmuxSessionName(
    node.workspace,
    knownSessions
  );
  await cli.createTmuxSession(
    node.host,
    node.registry.host,
    node.workspace.path,
    sessionName
  );
  await tmuxSessions.put(managedTmuxRecord(
    node.registry.host,
    node.workspace,
    sessionName,
    node.workspace.path,
    shellCommand(),
    { kind: "shell" }
  ));
  await cli.refreshRegistry(node.host);
  for (const provider of providers) {
    provider.invalidateHost(node.host, true);
  }
  await attachTmuxTerminal(
    cli,
    terminalLinks,
    node.host,
    node.workspace.path,
    sessionName
  );
  for (const provider of providers) {
    provider.refreshTerminals();
  }
}

function nextTmuxSessionName(
  workspace: TtWorkspace,
  sessions = workspace.state.tmux.sessions
): string {
  const base = `ws-${workspace.name}`;
  const existing = new Set(
    sessions.map((session) => session.session_name)
  );
  if (!existing.has(base)) {
    return base;
  }
  for (let index = 2; ; index += 1) {
    const candidate = `${base}-${index}`;
    if (!existing.has(candidate)) {
      return candidate;
    }
  }
}

function managedTmuxRecord(
  registryHost: string,
  workspace: TtWorkspace,
  sessionName: string,
  paneCurrentPath: string,
  paneCurrentCommand: string,
  launch: ManagedTmuxSession["launch"]
): ManagedTmuxSession {
  return {
    registryHost,
    workspaceId: workspace.id,
    workspacePath: workspace.path,
    sessionName,
    paneCurrentPath,
    paneCurrentCommand,
    launch,
    managedAt: new Date().toISOString()
  };
}

function shellCommand(): string {
  return basename(process.env.SHELL ?? "shell");
}

async function openTmuxSession(
  cli: TtCli,
  terminalLinks: TerminalLinkRegistry,
  node: TmuxSessionNode
): Promise<void> {
  if (node.session.lifecycle === "stopped") {
    return;
  }
  await attachTmuxTerminal(
    cli,
    terminalLinks,
    node.host,
    node.session.pane_current_path,
    node.session.session_name
  );
}

async function attachTmuxTerminal(
  cli: TtCli,
  terminalLinks: TerminalLinkRegistry,
  host: TtHost,
  cwd: string,
  sessionName: string
): Promise<void> {
  const terminal = vscode.window.createTerminal({
    name: `TT: ${host.alias}/${sessionName}`,
    cwd: homedir()
  });
  terminalLinks.markAttached(terminal, host.alias, sessionName);
  terminal.show();
  terminal.sendText(
    await cli.openTmuxCommand(host, cwd, sessionName)
  );
}

async function manageTmuxSession(
  tmuxSessions: ManagedTmuxSessionStore,
  providers: readonly WorkspaceTreeProvider[],
  node: TmuxSessionNode
): Promise<void> {
  if (node.session.lifecycle !== "external") {
    return;
  }
  await tmuxSessions.put(managedTmuxRecord(
    node.registry.host,
    node.workspace,
    node.session.session_name,
    node.session.pane_current_path,
    node.session.pane_current_command,
    { kind: "shell" }
  ));
  for (const provider of providers) {
    provider.invalidateHost(node.host, true);
  }
}

async function restoreTmuxSession(
  cli: TtCli,
  providers: readonly WorkspaceTreeProvider[],
  terminalLinks: TerminalLinkRegistry,
  tmuxSessions: ManagedTmuxSessionStore,
  node: TmuxSessionNode
): Promise<void> {
  if (node.session.lifecycle !== "stopped" || !node.session.managed) {
    return;
  }
  const record = node.session.managed;
  const resume = record.launch.kind === "agent-resume"
    ? `\n\nResume command: ${record.launch.command}`
    : "";
  const confirmation = await vscode.window.showWarningMessage(
    `Restore tmux session '${record.sessionName}'?`,
    {
      modal: true,
      detail: `Recreate it in ${record.paneCurrentPath}.${resume}`
    },
    "Restore tmux Session"
  );
  if (confirmation !== "Restore tmux Session") {
    return;
  }

  await cli.createTmuxSession(
    node.host,
    record.registryHost,
    record.paneCurrentPath,
    record.sessionName
  );
  if (record.launch.kind === "agent-resume") {
    await cli.sendTmuxCommand(
      node.host,
      record.registryHost,
      record.sessionName,
      record.launch.command
    );
  }
  await cli.refreshRegistry(node.host);
  for (const provider of providers) {
    provider.invalidateHost(node.host, true);
  }
  await attachTmuxTerminal(
    cli,
    terminalLinks,
    node.host,
    record.paneCurrentPath,
    record.sessionName
  );
  for (const provider of providers) {
    provider.refreshTerminals();
  }
}

async function removeTmuxSession(
  cli: TtCli,
  providers: readonly WorkspaceTreeProvider[],
  terminalLinks: TerminalLinkRegistry,
  tmuxSessions: ManagedTmuxSessionStore,
  node: TmuxSessionNode
): Promise<void> {
  if (node.session.lifecycle === "external" || !node.session.managed) {
    return;
  }
  const confirmation = await vscode.window.showWarningMessage(
    `Remove tmux session '${node.session.session_name}'?`,
    {
      modal: true,
      detail:
        `This stops every process running in the session on ${node.host.alias} and removes its saved restore recipe. This cannot be undone.`
    },
    "Remove tmux Session"
  );
  if (confirmation !== "Remove tmux Session") {
    return;
  }

  await cli.killTmuxSession(
    node.host,
    node.registry.host,
    node.session.session_name
  );
  await tmuxSessions.remove(
    node.registry.host,
    node.session.session_name
  );
  terminalLinks.unlinkSession(node.host.alias, node.session.session_name);
  await cli.refreshRegistry(node.host);
  for (const provider of providers) {
    provider.invalidateHost(node.host, true);
  }
}

async function recoverTerminalInTmux(
  cli: TtCli,
  providers: readonly WorkspaceTreeProvider[],
  terminalLinks: TerminalLinkRegistry,
  tmuxSessions: ManagedTmuxSessionStore,
  node: TerminalNode
): Promise<void> {
  if (terminalLinks.linkFor(node.terminal)) {
    void vscode.window.showInformationMessage(
      `${node.terminal.name} is already linked to a tmux session.`
    );
    return;
  }

  const extensionConfig = vscode.workspace.getConfiguration("genoTools");
  const runtime = await loadAgentRuntimeConfig({
    configPath: extensionConfig.get<string>(
      "agentConfigPath",
      "~/.geno/config.yaml"
    ),
    modelOverride: extensionConfig.get<string>("agentModel", "")
  });
  const endpointLabel = runtime.endpoint ?? "https://api.openai.com/v1";

  const consent = await vscode.window.showWarningMessage(
    "Send this terminal's recent history to OpenAI for tmux recovery?",
    {
      modal: true,
      detail:
        `Geno Tools will select at most 60,000 characters spanning the full available scrollback, match it locally against saved Claude and Codex sessions, ask an OpenAI Agents SDK planner only for a name and summary, and restore your clipboard. No tmux session is created without a verified saved session. Review or rename the proposal before anything is created.\n\nEndpoint: ${endpointLabel}\nModel: ${runtime.model}\nCredential: ${runtime.apiKeyEnv}`
    },
    "Scan History"
  );
  if (consent !== "Scan History") {
    return;
  }

  const history = await captureTerminalHistory(node.terminal);
  const recoveryContext: RecoveryContext = {
    terminalName: node.terminal.name,
    hostAlias: node.host.alias,
    workspacePath: node.workspace.path,
    currentDirectory: node.cwd,
    existingSessionNames: tmuxSessions
      .forWorkspace(node.registry.host, node.workspace)
      .map(
      ({ session_name }) => session_name
      )
  };
  const matches = await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: `Finding the saved agent session for ${node.terminal.name}`,
      cancellable: false
    },
    async () => findAgentSessionMatches(history, {
      workspacePath: node.workspace.path,
      currentDirectory: node.cwd
    })
  );
  const matchedSession = matches[0];
  if (!matchedSession) {
    void vscode.window.showErrorMessage(
      "No saved Claude or Codex session confidently matched this terminal history. No tmux session was created."
    );
    return;
  }
  const resumeCommand = agentResumeCommand(matchedSession);
  const proposed = await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: `Analyzing ${node.terminal.name} with ${runtime.model}`,
      cancellable: false
    },
    async () => proposeRecovery(history, recoveryContext, runtime)
  );

  const proposal = await reviewRecoveryProposal(
    { ...proposed, workingDirectory: matchedSession.workingDirectory },
    recoveryContext.existingSessionNames,
    matchedSession,
    resumeCommand
  );
  if (!proposal) {
    return;
  }

  await cli.createTmuxSession(
    node.host,
    node.registry.host,
    proposal.workingDirectory,
    proposal.sessionName
  );
  await tmuxSessions.put(managedTmuxRecord(
    node.registry.host,
    node.workspace,
    proposal.sessionName,
    proposal.workingDirectory,
    shellCommand(),
    { kind: "shell" }
  ));

  let resumeFailure: string | undefined;
  try {
    await cli.sendTmuxCommand(
      node.host,
      node.registry.host,
      proposal.sessionName,
      resumeCommand
    );
    await tmuxSessions.put(managedTmuxRecord(
      node.registry.host,
      node.workspace,
      proposal.sessionName,
      proposal.workingDirectory,
      resumeCommand.trim().split(/\s+/, 1)[0] || matchedSession.agent,
      { kind: "agent-resume", command: resumeCommand }
    ));
  } catch (error) {
    resumeFailure = error instanceof Error ? error.message : String(error);
  }

  await cli.refreshRegistry(node.host);
  for (const provider of providers) {
    provider.invalidateHost(node.host, true);
  }

  terminalLinks.markOrigin(
    node.terminal,
    node.host.alias,
    proposal.sessionName
  );
  await attachTmuxTerminal(
    cli,
    terminalLinks,
    node.host,
    proposal.workingDirectory,
    proposal.sessionName
  );
  for (const provider of providers) {
    provider.refreshTerminals();
  }

  if (resumeFailure) {
    void vscode.window.showWarningMessage(
      `Created ${proposal.sessionName}, but its agent resume command failed: ${resumeFailure}`
    );
  }
}

async function reviewRecoveryProposal(
  proposal: RecoveryProposal,
  existingSessionNames: readonly string[],
  matchedSession: AgentSessionMatch,
  resumeCommand: string
): Promise<RecoveryProposal | undefined> {
  let reviewed = proposal;
  while (true) {
    const confirmation = await vscode.window.showInformationMessage(
      `Create recovered tmux session '${reviewed.sessionName}'?`,
      {
        modal: true,
        detail: [
          reviewed.summary,
          `Directory: ${reviewed.workingDirectory}`,
          `Saved agent: ${agentDisplayName(matchedSession.agent)} ${matchedSession.sessionId}`,
          `History match score: ${matchedSession.score.toFixed(1)}`,
          `Resume command: ${resumeCommand}`
        ].join("\n\n")
      },
      "Create tmux Session",
      "Edit Name…"
    );
    if (confirmation === "Create tmux Session") {
      return reviewed;
    }
    if (confirmation !== "Edit Name…") {
      return undefined;
    }

    const sessionName = await vscode.window.showInputBox({
      title: "Name Recovered tmux Session",
      prompt: "Use a short task-focused name.",
      value: reviewed.sessionName,
      valueSelection: [0, reviewed.sessionName.length],
      validateInput: (value) => validateRecoverySessionName(
        value,
        existingSessionNames
      )
    });
    if (sessionName !== undefined) {
      reviewed = { ...reviewed, sessionName: sessionName.trim() };
    }
  }
}

function agentDisplayName(agent: AgentSessionMatch["agent"]): string {
  return agent === "claude" ? "Claude" : "Codex";
}

function validateRecoverySessionName(
  value: string,
  existingSessionNames: readonly string[]
): string | undefined {
  const name = value.trim();
  if (!name) {
    return "Enter a session name.";
  }
  if (name.length > 80) {
    return "Use 80 characters or fewer.";
  }
  if (!SAFE_TMUX_SESSION.test(name)) {
    return "Use letters, digits, hyphens, and underscores only.";
  }
  return existingSessionNames.includes(name)
    ? `A tmux session named '${name}' already exists.`
    : undefined;
}

async function mirrorWorkspace(
  cli: TtCli,
  provider: WorkspaceTreeProvider,
  source: WorkspaceNode
): Promise<void> {
  const hosts = (await provider.hosts()).filter(
    (host) => host.alias !== source.host.alias
  );
  if (hosts.length === 0) {
    throw new Error("Configure another TT host before mirroring a workspace.");
  }
  const picked = await vscode.window.showQuickPick(
    hosts.map((host) => ({
      label: host.alias,
      description: host.hostname,
      host
    })),
    {
      title: `Mirror ${workspaceReference(source.workspace)}`,
      placeHolder: "Choose the destination host"
    }
  );
  if (!picked) {
    return;
  }
  const confirmation = await vscode.window.showWarningMessage(
    `Mirror ${workspaceReference(source.workspace)} from ${source.host.alias} to ${picked.host.alias}?`,
    { modal: true },
    "Mirror"
  );
  if (confirmation !== "Mirror") {
    return;
  }
  await cli.run(
    cli.forHost(source.host, [
      "mirror",
      workspaceReference(source.workspace),
      picked.host.alias
    ]),
    `Mirroring ${workspaceReference(source.workspace)} to ${picked.host.alias}`,
    // TT prefers the current workspace when invoked from inside one. Running
    // from home ensures the explicitly selected workspace remains authoritative.
    homedir()
  );
  await cli.refreshRegistry(picked.host);
  provider.invalidateHost(picked.host, true);
}

async function createWorktree(cli: TtCli, node: WorkspaceNode): Promise<void> {
  const name = await worktreeInput("Create Whole-Workspace Worktree");
  if (!name) {
    return;
  }
  await cli.run(
    cli.forHost(node.host, [
      "wt",
      "new",
      name,
      "-w",
      workspaceReference(node.workspace)
    ]),
    `Creating worktree ${name}`
  );
}

async function listWorktrees(cli: TtCli, node: WorkspaceNode): Promise<void> {
  await cli.run(
    cli.forHost(node.host, [
      "wt",
      "ls",
      "-w",
      workspaceReference(node.workspace)
    ]),
    `Listing worktrees for ${workspaceReference(node.workspace)}`
  );
}

async function removeWorktree(cli: TtCli, node: WorkspaceNode): Promise<void> {
  const name = await worktreeInput("Remove Whole-Workspace Worktree");
  if (!name) {
    return;
  }
  const confirmation = await vscode.window.showWarningMessage(
    `Remove worktree '${name}' from every repository in ${workspaceReference(node.workspace)}?`,
    { modal: true },
    "Remove Worktree"
  );
  if (confirmation !== "Remove Worktree") {
    return;
  }
  await cli.run(
    cli.forHost(node.host, [
      "wt",
      "rm",
      name,
      "-w",
      workspaceReference(node.workspace)
    ]),
    `Removing worktree ${name}`
  );
}

async function openWorkspace(
  node: WorkspaceNode,
  forceNewWindow: boolean
): Promise<void> {
  if (isLocal(node.host, node.registry.host)) {
    const workspaceFile = await findWorkspaceFile(node.workspace);
    await openUri(
      vscode.Uri.file(workspaceFile ?? node.workspace.path),
      forceNewWindow
    );
    return;
  }
  await openPath(
    node.host,
    node.registry.host,
    node.workspace.path,
    forceNewWindow
  );
}

async function openPath(
  host: TtHost,
  registryHost: string,
  path: string,
  forceNewWindow?: boolean
): Promise<void> {
  const uri = isLocal(host, registryHost)
    ? vscode.Uri.file(path)
    : vscode.Uri.from({
        scheme: "vscode-remote",
        authority: `ssh-remote+${host.hostname}`,
        path
      });
  await openUri(uri, forceNewWindow);
}

async function openUri(
  uri: vscode.Uri,
  forceNewWindow?: boolean
): Promise<void> {
  const newWindow = forceNewWindow ?? vscode.workspace
    .getConfiguration("genoTools")
    .get<boolean>("openInNewWindow", true);
  await vscode.commands.executeCommand("vscode.openFolder", uri, newWindow);
}

async function findWorkspaceFile(workspace: TtWorkspace): Promise<string | undefined> {
  try {
    const entries = (await readdir(workspace.path)).filter((name) =>
      name.endsWith(".code-workspace")
    );
    const preferred = `${workspace.name}.code-workspace`;
    if (entries.includes(preferred)) {
      return join(workspace.path, preferred);
    }
    if (entries.length === 1) {
      return join(workspace.path, entries[0]);
    }
  } catch {
    // VS Code will show the useful filesystem error when opening the folder.
  }
  return undefined;
}

async function pickHost(
  provider: WorkspaceTreeProvider,
  placeHolder: string
): Promise<TtHost | undefined> {
  const hosts = await provider.hosts();
  const picked = await vscode.window.showQuickPick(
    hosts.map((host) => ({
      label: host.alias,
      description: `${host.hostname}${host.isDefault ? " · default" : ""}`,
      host
    })),
    { placeHolder }
  );
  return picked?.host;
}

async function pickWorkspace(
  cli: TtCli,
  provider: WorkspaceTreeProvider
): Promise<WorkspaceNode | undefined> {
  const hosts = await provider.hosts();
  const results = await Promise.allSettled(
    hosts.map(async (host) => ({ host, registry: await cli.registry(host) }))
  );
  const items = results.flatMap((result) => {
    if (result.status === "rejected") {
      return [];
    }
    const { host, registry } = result.value;
    return registry.workspaces.map((workspace) => ({
      label: workspaceReference(workspace),
      description: `${host.alias} · ${workspace.track}/${workspace.domain}`,
      detail: workspace.path,
      node: { kind: "workspace", host, registry, workspace } as WorkspaceNode
    }));
  });
  const picked = await vscode.window.showQuickPick(items, {
    title: "Choose a TT Workspace",
    matchOnDescription: true,
    matchOnDetail: true
  });
  return picked?.node;
}

async function pickRepo(
  cli: TtCli,
  provider: WorkspaceTreeProvider
): Promise<RepoNode | undefined> {
  const workspace = await pickWorkspace(cli, provider);
  if (!workspace) {
    return undefined;
  }
  const picked = await vscode.window.showQuickPick(
    workspace.workspace.repos.map((repo) => ({
      label: repo.name,
      description: basename(workspace.workspace.path),
      detail: repo.path,
      repo
    })),
    { title: `Open Repository in ${workspaceReference(workspace.workspace)}` }
  );
  return picked
    ? {
        kind: "repo",
        host: workspace.host,
        registry: workspace.registry,
        workspace: workspace.workspace,
        repo: picked.repo
      }
    : undefined;
}

async function segmentInput(prompt: string, placeHolder: string): Promise<string | undefined> {
  return vscode.window.showInputBox({
    title: "Create TT Workspace",
    prompt,
    placeHolder,
    validateInput: (value) =>
      SAFE_SEGMENT.test(value)
        ? undefined
        : "Use lowercase letters, digits, and hyphens."
  });
}

async function worktreeInput(title: string): Promise<string | undefined> {
  return vscode.window.showInputBox({
    title,
    prompt: "Worktree name",
    placeHolder: "feature-name",
    validateInput: (value) =>
      SAFE_WORKTREE.test(value)
        ? undefined
        : "Use letters, digits, dots, underscores, and hyphens."
  });
}

function isLocal(host: TtHost, registryHost: string): boolean {
  return host.hostname === "localhost" || registryHost === "localhost";
}
