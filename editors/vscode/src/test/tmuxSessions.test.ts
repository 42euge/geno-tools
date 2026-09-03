import assert from "node:assert/strict";
import test from "node:test";

import { TtTmuxSession, TtWorkspace } from "../model";
import {
  ManagedTmuxSession,
  ManagedTmuxSessionStore
} from "../tmuxSessions";

const STORAGE_KEY = "genoTools.managedTmuxSessions.v1";

test("reconciles managed, stopped, and external sessions", () => {
  const state = memento({
    schema: 1,
    sessions: [managed("live"), managed("stopped")]
  });
  const store = new ManagedTmuxSessionStore(state);

  const views = store.forWorkspace(
    "localhost",
    workspace([live("live", "codex"), live("external", "claude")])
  );

  assert.deepEqual(
    views.map(({ session_name, lifecycle }) => [session_name, lifecycle]),
    [
      ["external", "external"],
      ["live", "live"],
      ["stopped", "stopped"]
    ]
  );
  assert.equal(views[1].pane_current_command, "codex");
  assert.equal(views[2].pane_current_path, "/work/demo.2026.q3");
});

test("managed records are isolated by canonical host and workspace", () => {
  const store = new ManagedTmuxSessionStore(memento({
    schema: 1,
    sessions: [
      managed("same-name"),
      managed("same-name", {
        registryHost: "build.example.com",
        workspaceId: "chore.geno.other.2026.q3",
        workspacePath: "/srv/other.2026.q3",
        paneCurrentPath: "/srv/other.2026.q3"
      })
    ]
  }));

  assert.deepEqual(
    store.forWorkspace("localhost", workspace([])).map((item) => item.session_name),
    ["same-name"]
  );
  assert.deepEqual(
    store.forWorkspace("build.example.com", workspace([])).map(
      (item) => item.session_name
    ),
    []
  );
});

test("ignores unsupported roots and malformed individual records", () => {
  const unsupported = new ManagedTmuxSessionStore(memento({
    schema: 99,
    sessions: [managed("ignored")]
  }));
  assert.deepEqual(unsupported.records(), []);

  const partial = new ManagedTmuxSessionStore(memento({
    schema: 1,
    sessions: [managed("kept"), { sessionName: 42 }]
  }));
  assert.deepEqual(partial.records().map((record) => record.sessionName), ["kept"]);
});

test("put replaces by host and name and remove persists", async () => {
  const state = memento();
  const store = new ManagedTmuxSessionStore(state);

  await store.put(managed("agent", {
    launch: { kind: "agent-resume", command: "codexd resume abc" }
  }));
  await store.put(managed("agent", {
    paneCurrentCommand: "codexd",
    launch: { kind: "agent-resume", command: "codexd resume def" }
  }));

  assert.equal(store.get("localhost", "agent")?.paneCurrentCommand, "codexd");
  assert.deepEqual(store.get("localhost", "agent")?.launch, {
    kind: "agent-resume",
    command: "codexd resume def"
  });
  assert.deepEqual(state.value, {
    schema: 1,
    sessions: [managed("agent", {
      paneCurrentCommand: "codexd",
      launch: { kind: "agent-resume", command: "codexd resume def" }
    })]
  });

  await store.remove("localhost", "agent");
  assert.equal(store.get("localhost", "agent"), undefined);
  assert.deepEqual(state.value, { schema: 1, sessions: [] });
});

test("works in memory when VS Code persistence is unavailable", async () => {
  const store = new ManagedTmuxSessionStore();
  await store.put(managed("memory"));
  assert.equal(store.get("localhost", "memory")?.sessionName, "memory");
});

function live(
  sessionName: string,
  command = "zsh"
): TtTmuxSession {
  return {
    session_name: sessionName,
    pane_current_path: "/live/demo.2026.q3",
    pane_current_command: command,
    session_activity: 1788249600
  };
}

function managed(
  sessionName: string,
  overrides: Partial<ManagedTmuxSession> = {}
): ManagedTmuxSession {
  return {
    registryHost: "localhost",
    workspaceId: "chore.geno.demo.2026.q3",
    workspacePath: "/work/demo.2026.q3",
    sessionName,
    paneCurrentPath: "/work/demo.2026.q3",
    paneCurrentCommand: "zsh",
    launch: { kind: "shell" },
    managedAt: "2026-09-03T12:00:00.000Z",
    ...overrides
  };
}

function workspace(sessions: TtTmuxSession[]): TtWorkspace {
  return {
    id: "chore.geno.demo.2026.q3",
    track: "chore",
    domain: "geno",
    name: "demo",
    born: "2026.q3",
    path: "/work/demo.2026.q3",
    repos: [],
    state: { tmux: { sessions } }
  };
}

interface FakeMemento {
  value: unknown;
  get<T>(key: string): T | undefined;
  update(key: string, value: unknown): Promise<void>;
}

function memento(initial?: unknown): FakeMemento {
  return {
    value: initial,
    get<T>(key: string): T | undefined {
      assert.equal(key, STORAGE_KEY);
      return this.value as T | undefined;
    },
    async update(key: string, value: unknown): Promise<void> {
      assert.equal(key, STORAGE_KEY);
      this.value = value;
    }
  };
}
