import { readdir } from "node:fs/promises";
import { homedir } from "node:os";
import { basename, join } from "node:path";

import * as vscode from "vscode";

import { TRACK_ORDER, TtHost, TtWorkspace, workspaceReference } from "./model";
import { TtCli } from "./ttCli";
import {
  HostNode,
  isHostNode,
  isRepoNode,
  isTmuxSessionNode,
  isWorkspaceNode,
  RepoNode,
  TmuxSessionNode,
  WorkspaceNode,
  WorkspaceTreeProvider
} from "./workspaceTree";

const SAFE_SEGMENT = /^[a-z0-9][a-z0-9-]*$/;
const SAFE_WORKTREE = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

export function activate(context: vscode.ExtensionContext): void {
  const output = vscode.window.createOutputChannel("Geno Tools: TT");
  const cli = new TtCli(output);
  const provider = new WorkspaceTreeProvider(cli);
  const currentProvider = new WorkspaceTreeProvider(cli, "current");
  const tree = vscode.window.createTreeView("genoTools.workspaces", {
    treeDataProvider: provider,
    showCollapseAll: true
  });
  const currentTree = vscode.window.createTreeView("genoTools.currentWorkspace", {
    treeDataProvider: currentProvider
  });

  context.subscriptions.push(
    output,
    provider,
    currentProvider,
    tree,
    currentTree,
    vscode.workspace.onDidChangeWorkspaceFolders(() => currentProvider.reload())
  );
  register(context, "genoTools.reloadWorkspaces", async () => {
    provider.reload();
    currentProvider.reload();
  });
  register(context, "genoTools.refreshWorkspaces", async (node?: unknown) => {
    const host = isHostNode(node) ? node.host : undefined;
    await refreshWorkspaces(cli, [provider, currentProvider], host);
  });
  register(context, "genoTools.createWorkspace", async (node?: unknown) => {
    await createWorkspace(
      cli,
      [provider, currentProvider],
      isHostNode(node) ? node.host : undefined
    );
  });
  register(context, "genoTools.createTmuxSession", async (node?: unknown) => {
    const workspace = isWorkspaceNode(node)
      ? node
      : tree.selection.find(isWorkspaceNode) ??
        currentTree.selection.find(isWorkspaceNode) ??
        (await currentProvider.currentWorkspace()) ??
        (await pickWorkspace(cli, provider));
    if (workspace) {
      await resumeTmuxSession(cli, workspace);
    }
  });
  register(context, "genoTools.openTmuxSession", async (node?: unknown) => {
    if (isTmuxSessionNode(node)) {
      await openTmuxSession(cli, node);
    }
  });
  register(context, "genoTools.openWorkspace", async (node?: unknown) => {
    const workspace = isWorkspaceNode(node) ? node : await pickWorkspace(cli, provider);
    if (workspace) {
      await openWorkspace(workspace);
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
        provider.invalidateHost(host);
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
    one.invalidateHost(host);
  }
}

async function resumeTmuxSession(cli: TtCli, node: WorkspaceNode): Promise<void> {
  const reference = workspaceReference(node.workspace);
  const terminal = vscode.window.createTerminal({
    name: `TT: ${node.host.alias}/${reference}`,
    cwd: homedir()
  });
  terminal.show();
  terminal.sendText(await cli.resumeTmuxCommand(node.host, node.workspace.id));
}

async function openTmuxSession(cli: TtCli, node: TmuxSessionNode): Promise<void> {
  const terminal = vscode.window.createTerminal({
    name: `TT: ${node.host.alias}/${node.session.session_name}`,
    cwd: homedir()
  });
  terminal.show();
  terminal.sendText(
    await cli.openTmuxCommand(
      node.host,
      node.session.pane_current_path,
      node.session.session_name
    )
  );
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
  provider.invalidateHost(picked.host);
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

async function openWorkspace(node: WorkspaceNode): Promise<void> {
  if (isLocal(node.host, node.registry.host)) {
    const workspaceFile = await findWorkspaceFile(node.workspace);
    await openUri(vscode.Uri.file(workspaceFile ?? node.workspace.path));
    return;
  }
  await openPath(node.host, node.registry.host, node.workspace.path);
}

async function openPath(
  host: TtHost,
  registryHost: string,
  path: string
): Promise<void> {
  const uri = isLocal(host, registryHost)
    ? vscode.Uri.file(path)
    : vscode.Uri.from({
        scheme: "vscode-remote",
        authority: `ssh-remote+${host.hostname}`,
        path
      });
  await openUri(uri);
}

async function openUri(uri: vscode.Uri): Promise<void> {
  const forceNewWindow = vscode.workspace
    .getConfiguration("genoTools")
    .get<boolean>("openInNewWindow", true);
  await vscode.commands.executeCommand("vscode.openFolder", uri, {
    forceNewWindow
  });
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
