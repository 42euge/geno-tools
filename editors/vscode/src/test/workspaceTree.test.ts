import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join } from "node:path";
import test from "node:test";
import vm from "node:vm";

import * as esbuild from "esbuild";

interface TreeNode {
  kind: string;
  [key: string]: unknown;
}

interface TreeProvider {
  getChildren(node: TreeNode): Promise<TreeNode[]>;
  getTreeItem(node: TreeNode): {
    label: string;
    description?: string;
    contextValue?: string;
    command?: { command: string; arguments?: unknown[] };
  };
}

test("repositories, tmux sessions, and VS Code terminals have separate folders", async () => {
  const WorkspaceTreeProvider = await loadWorkspaceTreeProvider();
  const workspace = {
    id: "chore.geno.demo.2026.q3",
    track: "chore",
    domain: "geno",
    name: "demo",
    born: "2026.q3",
    path: "/tmp/demo.2026.q3",
    repos: [{
      name: "repo-a",
      path: "/tmp/demo.2026.q3/repo-a",
      last_accessed: "2026-09-01T00:00:00Z"
    }],
    state: {
      tmux: {
        sessions: [
          {
            session_name: "workspace-agent",
            pane_current_path: "/tmp/demo.2026.q3",
            pane_current_command: "codex",
            session_activity: 1788249600
          },
          {
            session_name: "repo-agent",
            pane_current_path: "/tmp/demo.2026.q3/repo-a",
            pane_current_command: "claude",
            session_activity: 1788249600
          }
        ]
      }
    }
  };
  const host = { alias: "local", hostname: "localhost", isDefault: true };
  const registry = {
    schema_version: 1,
    host: "localhost",
    generated_at: "2026-09-01T00:00:00Z",
    workspaces: [workspace]
  };
  const provider = new WorkspaceTreeProvider({});
  const workspaceNode = { kind: "workspace", host, registry, workspace };
  const workspaceChildren = await provider.getChildren(workspaceNode);

  assert.deepEqual(labels(provider, workspaceChildren), [
    "Repositories",
    "tmux Sessions",
    "VS Code Terminals"
  ]);

  const repositories = workspaceChildren.find(
    (node) => provider.getTreeItem(node).label === "Repositories"
  );
  assert.ok(repositories, "repository folder should be present");
  const repoNodes = await provider.getChildren(repositories);
  assert.deepEqual(labels(provider, repoNodes), ["repo-a"]);
  assert.equal((await provider.getChildren(repoNodes[0])).length, 0);

  const tmuxSessions = workspaceChildren.find(
    (node) => provider.getTreeItem(node).label === "tmux Sessions"
  );
  assert.ok(tmuxSessions, "tmux session folder should be present");
  assert.deepEqual(labels(provider, await provider.getChildren(tmuxSessions)), [
    "repo-agent",
    "workspace-agent"
  ]);
});

test("empty workspace groups remain available for their action buttons", async () => {
  const WorkspaceTreeProvider = await loadWorkspaceTreeProvider();
  const workspace = {
    id: "chore.geno.empty.2026.q3",
    track: "chore",
    domain: "geno",
    name: "empty",
    born: "2026.q3",
    path: "/tmp/empty.2026.q3",
    repos: [],
    state: { tmux: { sessions: [] } }
  };
  const host = { alias: "local", hostname: "localhost", isDefault: true };
  const registry = {
    schema_version: 1,
    host: "localhost",
    generated_at: "2026-09-01T00:00:00Z",
    workspaces: [workspace]
  };
  const provider = new WorkspaceTreeProvider({});
  const children = await provider.getChildren({
    kind: "workspace",
    host,
    registry,
    workspace
  });

  assert.deepEqual(labels(provider, children), [
    "Repositories",
    "tmux Sessions",
    "VS Code Terminals"
  ]);
  assert.deepEqual(
    Array.from(children, (node) => provider.getTreeItem(node).contextValue),
    ["repoGroup", "tmuxSessionGroup", "terminalGroup"]
  );
});

test("open VS Code terminals are listed under their workspace", async () => {
  const workspacePath = "/tmp/demo.2026.q3";
  const inside = {
    name: "demo shell",
    creationOptions: {},
    shellIntegration: {
      cwd: {
        scheme: "file",
        authority: "",
        path: `${workspacePath}/repo-a`,
        fsPath: `${workspacePath}/repo-a`
      }
    },
    show() {}
  };
  const outside = {
    name: "other shell",
    creationOptions: { cwd: "/tmp/other.2026.q3" },
    shellIntegration: undefined,
    show() {}
  };
  const WorkspaceTreeProvider = await loadWorkspaceTreeProvider([inside, outside]);
  const workspace = {
    id: "chore.geno.demo.2026.q3",
    track: "chore",
    domain: "geno",
    name: "demo",
    born: "2026.q3",
    path: workspacePath,
    repos: [],
    state: { tmux: { sessions: [] } }
  };
  const host = { alias: "local", hostname: "localhost", isDefault: true };
  const registry = {
    schema_version: 1,
    host: "localhost",
    generated_at: "2026-09-01T00:00:00Z",
    workspaces: [workspace]
  };
  const provider = new WorkspaceTreeProvider({});
  const groups = await provider.getChildren({
    kind: "workspace",
    host,
    registry,
    workspace
  });
  const terminalGroup = groups.find(
    (node) => provider.getTreeItem(node).label === "VS Code Terminals"
  );
  assert.ok(terminalGroup, "terminal folder should be present");

  const terminals = await provider.getChildren(terminalGroup);
  assert.deepEqual(labels(provider, terminals), ["demo shell"]);
  const item = provider.getTreeItem(terminals[0]);
  assert.equal(item.command?.command, "genoTools.focusTerminal");
  assert.equal(item.command?.arguments?.[0], terminals[0]);
});

test("tmux sessions can be reopened from the tree", async () => {
  const WorkspaceTreeProvider = await loadWorkspaceTreeProvider();
  const host = { alias: "local", hostname: "localhost", isDefault: true };
  const session = {
    session_name: "ws-tools-cleanup",
    pane_current_path: "/tmp/tools-cleanup.2026.q3",
    pane_current_command: "codex",
    session_activity: 1788249600
  };
  const node = { kind: "tmuxSession", host, session };
  const item = new WorkspaceTreeProvider({}).getTreeItem(node);

  assert.equal(item.command?.command, "genoTools.openTmuxSession");
  assert.equal(item.command?.arguments?.[0], node);
});

test("terminal and tmux rows show their bidirectional VS Code link", async () => {
  const attached = {
    name: "TT: local/recovered-work",
    creationOptions: { cwd: "/Users/test" },
    shellIntegration: undefined,
    show() {}
  };
  const WorkspaceTreeProvider = await loadWorkspaceTreeProvider([attached]);
  const workspace = {
    id: "chore.geno.demo.2026.q3",
    track: "chore",
    domain: "geno",
    name: "demo",
    born: "2026.q3",
    path: "/tmp/demo.2026.q3",
    repos: [],
    state: {
      tmux: {
        sessions: [{
          session_name: "recovered-work",
          pane_current_path: "/tmp/demo.2026.q3",
          pane_current_command: "codex",
          session_activity: 1788249600
        }]
      }
    }
  };
  const host = { alias: "local", hostname: "localhost", isDefault: true };
  const registry = {
    schema_version: 1,
    host: "localhost",
    generated_at: "2026-09-01T00:00:00Z",
    workspaces: [workspace]
  };
  const provider = new WorkspaceTreeProvider({});
  const groups = await provider.getChildren({
    kind: "workspace",
    host,
    registry,
    workspace
  });
  const terminalGroup = groups.find(({ kind }) => kind === "terminalGroup");
  const tmuxGroup = groups.find(({ kind }) => kind === "tmuxSessionGroup");
  assert.ok(terminalGroup);
  assert.ok(tmuxGroup);

  const terminals = await provider.getChildren(terminalGroup);
  assert.equal(terminals.length, 1, "linked terminal should be listed by session");
  const terminalItem = provider.getTreeItem(terminals[0]);
  assert.equal(terminalItem.contextValue, "terminalLinked");
  assert.match(terminalItem.description ?? "", /tmux: recovered-work/);

  const sessions = await provider.getChildren(tmuxGroup);
  const tmuxItem = provider.getTreeItem(sessions[0]);
  assert.match(tmuxItem.description ?? "", /VS Code/);
});

function labels(provider: TreeProvider, nodes: TreeNode[]): string[] {
  return Array.from(nodes, (node) => provider.getTreeItem(node).label);
}

async function loadWorkspaceTreeProvider(
  terminals: unknown[] = []
): Promise<new (cli: object) => TreeProvider> {
  const result = await esbuild.build({
    entryPoints: [join(__dirname, "..", "workspaceTree.ts")],
    bundle: true,
    format: "cjs",
    platform: "node",
    write: false,
    plugins: [{
      name: "vscode-stub",
      setup(build) {
        build.onResolve({ filter: /^vscode$/ }, () => ({
          path: "vscode",
          namespace: "stub"
        }));
        build.onLoad({ filter: /.*/, namespace: "stub" }, () => ({
          contents: `
            const state = globalThis.__vscodeStub;
            class EventEmitter {
              event = () => ({ dispose() {} });
              fire() {}
              dispose() {}
            }
            class TreeItem {
              constructor(label, collapsibleState) {
                this.label = label;
                this.collapsibleState = collapsibleState;
              }
            }
            class MarkdownString { constructor(value) { this.value = value; } }
            class ThemeIcon { constructor(id) { this.id = id; } }
            module.exports = {
              EventEmitter,
              TreeItem,
              MarkdownString,
              ThemeIcon,
              TreeItemCollapsibleState: { None: 0, Collapsed: 1, Expanded: 2 },
              window: { terminals: state.terminals },
              workspace: { workspaceFolders: [], workspaceFile: undefined }
            };
          `,
          loader: "js"
        }));
      }
    }]
  });

  const compiledModule: { exports: Record<string, unknown> } = { exports: {} };
  vm.runInNewContext(result.outputFiles[0].text, {
    module: compiledModule,
    exports: compiledModule.exports,
    require: createRequire(__filename),
    process,
    Buffer,
    console,
    setTimeout,
    clearTimeout,
    __vscodeStub: { terminals }
  });
  return compiledModule.exports.WorkspaceTreeProvider as new (
    cli: object
  ) => TreeProvider;
}
