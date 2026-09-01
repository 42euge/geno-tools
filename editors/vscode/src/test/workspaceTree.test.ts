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
    command?: { command: string; arguments?: unknown[] };
  };
}

test("tmux sessions appear beneath their workspace or repository", async () => {
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

  assert.deepEqual(labels(provider, workspaceChildren), ["workspace-agent", "repo-a"]);

  const repoNode = workspaceChildren.find(
    (node) => provider.getTreeItem(node).label === "repo-a"
  );
  assert.ok(repoNode, "repo-a should be present");
  assert.deepEqual(labels(provider, await provider.getChildren(repoNode)), ["repo-agent"]);
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

function labels(provider: TreeProvider, nodes: TreeNode[]): string[] {
  return Array.from(nodes, (node) => provider.getTreeItem(node).label);
}

async function loadWorkspaceTreeProvider(): Promise<new (cli: object) => TreeProvider> {
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
    clearTimeout
  });
  return compiledModule.exports.WorkspaceTreeProvider as new (
    cli: object
  ) => TreeProvider;
}
