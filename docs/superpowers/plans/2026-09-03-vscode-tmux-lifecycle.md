# VS Code tmux Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Give explicitly managed VS Code tmux sessions durable Live/Stopped lifecycle state, restorable launch recipes, and idempotent removal when the tmux server or session is already gone.

**Architecture:** A focused editors/vscode/src/tmuxSessions.ts module persists extension-owned records in ExtensionContext.globalState and reconciles them with fresh TT workspace registry sessions. ttCli.ts remains the process boundary and converts only tmux's known absence errors into an alreadyAbsent result; workspaceTree.ts renders state while extension.ts coordinates actions.

**Tech Stack:** TypeScript 5.7, VS Code Extension API 1.96, Node 22 node:test, esbuild, tmux, SSH, TT CLI.

**Spec:** docs/superpowers/specs/2026-09-03-vscode-tmux-lifecycle-design.md

## Global Constraints

- Manage only sessions the extension created or the user explicitly adopted.
- Keep live external workspace sessions openable but non-destructive.
- Never infer ownership from current directory or process name.
- Treat only no server running, no sessions, and can't find session as already absent.
- Preserve managed records on SSH, permission, timeout, executable, cancellation, and unclassified failures.
- Refresh on initial tree load, explicit refresh, and completed lifecycle actions; do not poll.
- Keep the genoTools.deleteTmuxSession command id for keybinding compatibility while presenting it as Remove.

---

### Task 1: Durable managed-session records and reconciliation

**Files:**
- Create: editors/vscode/src/tmuxSessions.ts
- Create: editors/vscode/src/test/tmuxSessions.test.ts

**Interfaces:**
- Consumes: TtTmuxSession and TtWorkspace from model.ts; get and update from vscode.Memento.
- Produces: ManagedTmuxSession, TmuxSessionView, and ManagedTmuxSessionStore with records(), forWorkspace(), get(), put(), and remove().

- [ ] **Step 1: Write failing record and reconciliation tests**

~~~ts
test("reconciles managed, stopped, and external sessions", () => {
  const store = new ManagedTmuxSessionStore(memento({
    schema: 1,
    sessions: [managed("live"), managed("stopped")]
  }));
  const views = store.forWorkspace("localhost", workspace([
    live("live"), live("external")
  ]));
  assert.deepEqual(
    views.map((item) => [item.session_name, item.lifecycle]),
    [["external", "external"], ["live", "live"], ["stopped", "stopped"]]
  );
});

test("ignores malformed or unsupported persisted records", () => {
  const store = new ManagedTmuxSessionStore(memento({
    schema: 99,
    sessions: [{ sessionName: 42 }]
  }));
  assert.deepEqual(store.records(), []);
});
~~~

- [ ] **Step 2: Run the test to verify RED**

Run: cd editors/vscode && npx tsx --test src/test/tmuxSessions.test.ts

Expected: FAIL because ../tmuxSessions does not exist.

- [ ] **Step 3: Implement the model and versioned store**

Use these public types:

~~~ts
export type TmuxLifecycle = "live" | "stopped" | "external";

export interface ManagedTmuxSession {
  registryHost: string;
  workspaceId: string;
  workspacePath: string;
  sessionName: string;
  paneCurrentPath: string;
  paneCurrentCommand: string;
  launch: { kind: "shell" } |
    { kind: "agent-resume"; command: string };
  managedAt: string;
}

export interface TmuxSessionView extends TtTmuxSession {
  lifecycle: TmuxLifecycle;
  managed?: ManagedTmuxSession;
}

export class ManagedTmuxSessionStore {
  constructor(state?: Pick<vscode.Memento, "get" | "update">);
  records(): ManagedTmuxSession[];
  get(registryHost: string, sessionName: string):
    ManagedTmuxSession | undefined;
  forWorkspace(registryHost: string, workspace: TtWorkspace):
    TmuxSessionView[];
  put(record: ManagedTmuxSession): Promise<void>;
  remove(registryHost: string, sessionName: string): Promise<void>;
}
~~~

Persist schema 1 at key genoTools.managedTmuxSessions.v1. Parse every field. Ignore an unsupported root or malformed individual record. Use an in-memory fallback when no Memento is supplied. Reconciliation sorts by session name, adds managed records missing from live state as Stopped, marks matches Live, and marks unmatched live rows External.

- [ ] **Step 4: Add mutation and recipe tests**

~~~ts
test("put replaces by host and name and remove persists", async () => {
  const state = memento();
  const store = new ManagedTmuxSessionStore(state);
  await store.put(managed("agent", {
    launch: { kind: "agent-resume", command: "codexd resume abc" }
  }));
  await store.put(managed("agent", { paneCurrentCommand: "codexd" }));
  assert.equal(store.get("localhost", "agent")?.paneCurrentCommand, "codexd");
  await store.remove("localhost", "agent");
  assert.equal(store.get("localhost", "agent"), undefined);
});
~~~

- [ ] **Step 5: Run focused tests and commit**

Run: cd editors/vscode && npx tsx --test src/test/tmuxSessions.test.ts

Expected: PASS.

~~~bash
git add editors/vscode/src/tmuxSessions.ts editors/vscode/src/test/tmuxSessions.test.ts
git commit -m "feat(vscode): persist managed tmux sessions"
~~~

### Task 2: Idempotent tmux removal and fresh registry scans

**Files:**
- Modify: editors/vscode/src/ttCli.ts
- Create: editors/vscode/src/test/ttCli.test.ts

**Interfaces:**
- Consumes: TtCommandError, executeProgram(), local/remote routing, and registry().
- Produces: TmuxKillOutcome, isTmuxSessionAbsentError(), killTmuxSession() returning the outcome, and scanRegistry().

- [ ] **Step 1: Write failing classifier tests**

~~~ts
test("recognizes only tmux absence diagnostics", () => {
  for (const message of [
    "no server running on /private/tmp/tmux-503/default",
    "no sessions",
    "can't find session: old-work"
  ]) {
    assert.equal(
      isTmuxSessionAbsentError(new TtCommandError(message, [])), true
    );
  }
  for (const message of [
    "ssh: connect to host build: Operation timed out",
    "bash: tmux: command not found",
    "permission denied"
  ]) {
    assert.equal(
      isTmuxSessionAbsentError(new TtCommandError(message, [])), false
    );
  }
});
~~~

- [ ] **Step 2: Run the test to verify RED**

Run: cd editors/vscode && npx tsx --test src/test/ttCli.test.ts

Expected: FAIL because the classifier is not exported.

- [ ] **Step 3: Implement narrow classification and outcomes**

~~~ts
export type TmuxKillOutcome = "killed" | "alreadyAbsent";

export function isTmuxSessionAbsentError(error: unknown): boolean {
  if (!(error instanceof TtCommandError)) return false;
  return /(?:no server running|no sessions|can't find session)(?::|\s|$)/i
    .test(error.message);
}
~~~

Wrap local and SSH kill execution in one try/catch. Return killed on exit zero, alreadyAbsent only for the classifier, and rethrow everything else. Never match generic not found.

- [ ] **Step 4: Add a quiet fresh-scan API**

~~~ts
async scanRegistry(host: TtHost): Promise<TtRegistry> {
  await this.execute(this.forHost(host, ["registry", "refresh"]));
  return this.registry(host);
}
~~~

Keep refreshRegistry() for explicit progress UI.

- [ ] **Step 5: Run focused tests and commit**

Run: cd editors/vscode && npx tsx --test src/test/ttCli.test.ts

Expected: PASS.

~~~bash
git add editors/vscode/src/ttCli.ts editors/vscode/src/test/ttCli.test.ts
git commit -m "fix(vscode): make tmux removal idempotent"
~~~

### Task 3: Render lifecycle states in the tree

**Files:**
- Modify: editors/vscode/src/workspaceTree.ts
- Modify: editors/vscode/src/test/workspaceTree.test.ts

**Interfaces:**
- Consumes: ManagedTmuxSessionStore.forWorkspace(), TmuxSessionView, and TtCli.scanRegistry().
- Produces: state-specific TmuxSessionNode rows, counts, context values, icons, and primary commands.

- [ ] **Step 1: Write failing row and group tests**

~~~ts
test("tmux rows distinguish lifecycle state", () => {
  const provider = new WorkspaceTreeProvider({});
  assert.equal(
    provider.getTreeItem(tmuxNode("live")).contextValue,
    "tmuxSession.live"
  );
  assert.equal(
    provider.getTreeItem(tmuxNode("stopped")).command?.command,
    "genoTools.restoreTmuxSession"
  );
  assert.match(
    provider.getTreeItem(tmuxNode("external")).description ?? "",
    /External/
  );
});
~~~

Add a group test with one raw live row and a fake store returning Live plus Stopped. The group count must be 2 and both children must appear.

- [ ] **Step 2: Run tree tests to verify RED**

Run: cd editors/vscode && npx tsx --test src/test/workspaceTree.test.ts

Expected: FAIL because nodes still use TtTmuxSession.

- [ ] **Step 3: Inject the session store and use reconciled views**

~~~ts
constructor(
  private readonly cli: TtCli,
  private readonly scope: "all" | "current" = "all",
  private readonly terminalLinks = new TerminalLinkRegistry(),
  private readonly tmuxSessions = new ManagedTmuxSessionStore()
) {}
~~~

Change TmuxSessionNode.session to TmuxSessionView. Make workspace counts, tmux group counts, tooltips, and children use forWorkspace(registry.host, workspace). On the first uncached load, scan the registry. Track scanned host aliases. invalidateHost(host, true) means the caller already refreshed; reload() clears registry and scan caches.

- [ ] **Step 4: Render exact state behavior**

~~~ts
item.contextValue = "tmuxSession." + node.session.lifecycle;
item.description = node.session.lifecycle === "stopped"
  ? "Stopped"
  : node.session.pane_current_command +
    (node.session.lifecycle === "external" ? " · External" : "") +
    (openInVsCode ? " · VS Code" : "");
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
~~~

Stopped tooltips say Managed session is stopped. External tooltips say Manage before lifecycle actions.

- [ ] **Step 5: Run tree tests and commit**

Run: cd editors/vscode && npx tsx --test src/test/workspaceTree.test.ts

Expected: PASS.

~~~bash
git add editors/vscode/src/workspaceTree.ts editors/vscode/src/test/workspaceTree.test.ts
git commit -m "feat(vscode): show tmux lifecycle state"
~~~

### Task 4: Wire create, manage, restore, and remove

**Files:**
- Modify: editors/vscode/src/extension.ts
- Modify: editors/vscode/src/test/extension.test.ts

**Interfaces:**
- Consumes: the store and records from Task 1, kill outcomes from Task 2, and stateful tree nodes from Task 3.
- Produces: genoTools.manageTmuxSession, genoTools.restoreTmuxSession, and durable create/recovery/remove behavior.

- [ ] **Step 1: Extend the test stub for persistence and failures**

Add globalState?: Map<string, unknown> and spawnResults?: Array<{ code: number; stdout?: string; stderr?: string }>. Make the process stub emit configured stdout/stderr before close. Contexts under test expose get/update methods backed by the map.

- [ ] **Step 2: Write failing persistence tests**

Normal creation persists a shell recipe. Manage adopts an External row without spawning tmux. Extend recovery tests to require this record only after send-keys succeeds:

~~~ts
assert.deepEqual(record.launch, {
  kind: "agent-resume",
  command: "codexd resume " + sessionId
});
~~~

When send-keys fails, the record remains a shell recipe.

- [ ] **Step 3: Write failing Restore tests**

Cover shell and agent-resume records. Agent restore must spawn new-session, two send-keys commands, registry refresh, and then attach. Canceling the modal spawns nothing and preserves the record.

- [ ] **Step 4: Write failing Remove tests**

For no server running and can't find session, assert record removal, link cleanup, registry refresh, and no error. For SSH timeout, assert an error, no registry refresh, and the record remains.

- [ ] **Step 5: Construct and share the store**

~~~ts
const tmuxSessions = new ManagedTmuxSessionStore(context.globalState);
const provider = new WorkspaceTreeProvider(
  cli, "all", terminalLinks, tmuxSessions
);
const currentProvider = new WorkspaceTreeProvider(
  cli, "current", terminalLinks, tmuxSessions
);
~~~

Record normal sessions after successful creation. Record recovery as shell first and replace it with the validated agent command only after send-keys succeeds.

- [ ] **Step 6: Implement Manage and Restore**

Manage accepts only External nodes and writes a shell record. Restore accepts only Stopped managed nodes, confirms the directory and optional resume command, recreates the session, sends the saved command when present, refreshes, and attaches.

Factor terminal attachment into:

~~~ts
async function attachTmuxTerminal(
  cli: TtCli,
  terminalLinks: TerminalLinkRegistry,
  host: TtHost,
  cwd: string,
  sessionName: string
): Promise<void>;
~~~

- [ ] **Step 7: Make Remove convergent**

Keep command id genoTools.deleteTmuxSession. Rename visible text to Remove. Require Live or Stopped managed state. Always call kill to close a Stopped-to-Live race. Delete the record and link only after killed/alreadyAbsent; then refresh and invalidate providers with true. Thrown errors preserve the record.

- [ ] **Step 8: Run extension tests and commit**

Run: cd editors/vscode && npx tsx --test src/test/extension.test.ts

Expected: PASS.

~~~bash
git add editors/vscode/src/extension.ts editors/vscode/src/test/extension.test.ts
git commit -m "feat(vscode): manage stopped tmux sessions"
~~~

### Task 5: Manifest, documentation, and release notes

**Files:**
- Modify: editors/vscode/package.json
- Modify: editors/vscode/package-lock.json
- Modify: editors/vscode/README.md
- Modify: editors/vscode/CHANGELOG.md
- Modify: editors/vscode/src/test/extension.test.ts

**Interfaces:**
- Consumes: context values and commands from Tasks 3 and 4.
- Produces: state-specific palette commands and inline actions.

- [ ] **Step 1: Write failing manifest tests**

Require Manage with verified icon, Restore with debug-restart icon, and the existing delete command titled Remove. Menu visibility:

- Open for tmuxSession.live and tmuxSession.external.
- Restore for tmuxSession.stopped.
- Manage for tmuxSession.external.
- Remove for tmuxSession.live and tmuxSession.stopped.

- [ ] **Step 2: Run the test to verify RED**

Run: cd editors/vscode && npx tsx --test src/test/extension.test.ts

Expected: FAIL because Manage/Restore are absent.

- [ ] **Step 3: Update manifest and versions**

Add the commands and menus. Bump 0.2.3 to 0.3.0 in package.json and the root package-lock entry.

- [ ] **Step 4: Update README and changelog**

Document Live, Stopped, External, Manage, shell/agent Restore, idempotent Remove, Unknown host failures, and refresh without polling. Add a 0.3.0 changelog section.

- [ ] **Step 5: Run checks and commit**

~~~bash
cd editors/vscode
npm run check
npm test
npm run build
cd ../..
git add editors/vscode/package.json editors/vscode/package-lock.json editors/vscode/README.md editors/vscode/CHANGELOG.md editors/vscode/src/test/extension.test.ts
git commit -m "docs(vscode): explain tmux lifecycle management"
~~~

Expected: all commands pass.

### Task 6: Final verification and PR

**Files:**
- Modify only if verification finds a defect in an earlier task.

**Interfaces:**
- Consumes: the completed feature.
- Produces: a clean, pushed branch and GitHub PR.

- [ ] **Step 1: Run final checks**

~~~bash
cd editors/vscode
npm run check
npm test
npm run build
cd ../..
git diff --check origin/main...HEAD
git status --short
~~~

Expected: all checks pass, diff check is silent, and status is clean.

- [ ] **Step 2: Review scope**

Run git diff --stat origin/main...HEAD and inspect tmuxSessions.ts, ttCli.ts, workspaceTree.ts, extension.ts, and package.json. Confirm there is no ownership inference, broad error swallowing, polling, or unrelated refactor.

- [ ] **Step 3: Push and open the PR**

~~~bash
git push -u origin feat/vscode-tmux-lifecycle
gh pr create --base main --head feat/vscode-tmux-lifecycle --title "feat(vscode): manage stopped tmux sessions" --body-file /tmp/geno-tools-vscode-tmux-lifecycle-pr.md
~~~

The PR body summarizes ownership, lifecycle state, restore recipes, idempotent Remove, retained real errors, and the three verification commands.
