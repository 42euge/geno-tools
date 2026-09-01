import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import vm from "node:vm";

import * as esbuild from "esbuild";

interface VscodeStub {
  agentOptions?: Record<string, unknown>;
  agentProposal?: Record<string, unknown>;
  clipboardText?: string;
  commands: Map<string, (...args: unknown[]) => Promise<unknown>>;
  errorMessages: string[];
  informationResults?: string[];
  inputValues: string[];
  openFolderCalls: Array<[{ path: string }, boolean]>;
  spawnCalls: Array<{ executable: string; args: string[] }>;
  terminalCommands: string[];
  terminalHistory?: string;
  treeDescriptions?: Record<string, string>;
  warningResults?: string[];
}

test("+ creates a new tmux session and accepts an optional name", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errorMessages: [],
    inputValues: ["", "focus", "remote-focus"],
    openFolderCalls: [],
    spawnCalls: [],
    terminalCommands: []
  };
  const extension = await loadExtension(stub);
  const context = { subscriptions: [] as Array<{ dispose?: () => void }> };
  extension.activate(context);

  const createTmuxSession = stub.commands.get("genoTools.createTmuxSession");
  assert.ok(createTmuxSession, "create tmux command should be registered");

  const node = {
    kind: "workspace",
    host: { alias: "local", hostname: "localhost", isDefault: true },
    registry: {
      schema_version: 1,
      host: "localhost",
      generated_at: "2026-09-01T00:00:00Z",
      workspaces: []
    },
    workspace: {
      id: "chore.geno.demo.2026.q3",
      track: "chore",
      domain: "geno",
      name: "demo",
      born: "2026.q3",
      path: "/tmp/demo.2026.q3",
      repos: [],
      state: { tmux: { sessions: [] } }
    }
  };

  await createTmuxSession(node);
  await createTmuxSession(node);
  node.host.alias = "build";
  node.host.hostname = "build.example.com";
  node.registry.host = "build.example.com";
  node.workspace.path = "/srv/demo.2026.q3";
  await createTmuxSession(node);

  assert.deepEqual(stub.terminalCommands, [
    "tt-test -H local tmux demo.2026.q3 ws-demo",
    "tt-test -H local tmux demo.2026.q3 focus",
    "tt-test -H build tmux demo.2026.q3 remote-focus"
  ]);
});

test("creating a tmux session refreshes the host registry", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errorMessages: [],
    inputValues: ["focus"],
    openFolderCalls: [],
    spawnCalls: [],
    terminalCommands: []
  };
  const extension = await loadExtension(stub);
  const context = { subscriptions: [] as Array<{ dispose?: () => void }> };
  extension.activate(context);

  const createTmuxSession = stub.commands.get("genoTools.createTmuxSession");
  assert.ok(createTmuxSession, "create tmux command should be registered");
  await createTmuxSession({
    kind: "tmuxSessionGroup",
    host: { alias: "local", hostname: "localhost", isDefault: true },
    registry: {
      schema_version: 1,
      host: "localhost",
      generated_at: "2026-09-01T00:00:00Z",
      workspaces: []
    },
    workspace: {
      id: "chore.geno.demo.2026.q3",
      track: "chore",
      domain: "geno",
      name: "demo",
      born: "2026.q3",
      path: "/tmp/demo.2026.q3",
      repos: [],
      state: { tmux: { sessions: [] } }
    }
  });

  assert.deepEqual(JSON.parse(JSON.stringify(stub.spawnCalls)), [
    {
      executable: "tmux",
      args: [
        "new-session",
        "-d",
        "-s",
        "focus",
        "-c",
        "/tmp/demo.2026.q3"
      ]
    },
    {
      executable: "tt-test",
      args: ["-H", "local", "registry", "refresh"]
    }
  ]);
});

test("deleting a tmux session requires confirmation, kills it, and refreshes", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errorMessages: [],
    inputValues: [],
    openFolderCalls: [],
    spawnCalls: [],
    terminalCommands: [],
    warningResults: ["Delete tmux Session"]
  };
  const extension = await loadExtension(stub);
  const contextObject = { subscriptions: [] as Array<{ dispose?: () => void }> };
  extension.activate(contextObject);
  const deleteTmuxSession = stub.commands.get("genoTools.deleteTmuxSession");
  assert.ok(deleteTmuxSession, "delete tmux command should be registered");

  await deleteTmuxSession({
    kind: "tmuxSession",
    host: { alias: "local", hostname: "localhost", isDefault: true },
    registry: {
      schema_version: 1,
      host: "localhost",
      generated_at: "2026-09-01T00:00:00Z",
      workspaces: []
    },
    workspace: {
      id: "chore.geno.demo.2026.q3",
      track: "chore",
      domain: "geno",
      name: "demo",
      born: "2026.q3",
      path: "/tmp/demo.2026.q3",
      repos: [],
      state: { tmux: { sessions: [] } }
    },
    session: {
      session_name: "obsolete-work",
      pane_current_path: "/tmp/demo.2026.q3",
      pane_current_command: "zsh",
      session_activity: 0
    }
  });

  assert.deepEqual(JSON.parse(JSON.stringify(stub.spawnCalls)), [
    {
      executable: "tmux",
      args: ["kill-session", "-t", "obsolete-work"]
    },
    {
      executable: "tt-test",
      args: ["-H", "local", "registry", "refresh"]
    }
  ]);
});

test("canceling tmux deletion leaves the session untouched", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errorMessages: [],
    inputValues: [],
    openFolderCalls: [],
    spawnCalls: [],
    terminalCommands: []
  };
  const extension = await loadExtension(stub);
  const contextObject = { subscriptions: [] as Array<{ dispose?: () => void }> };
  extension.activate(contextObject);
  const deleteTmuxSession = stub.commands.get("genoTools.deleteTmuxSession");
  assert.ok(deleteTmuxSession);
  await deleteTmuxSession({
    kind: "tmuxSession",
    host: { alias: "local", hostname: "localhost", isDefault: true },
    registry: { host: "localhost" },
    session: { session_name: "keep-work" }
  });
  assert.deepEqual(stub.spawnCalls, []);
});

test("workspace actions explicitly choose the current or a new window", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errorMessages: [],
    inputValues: [],
    openFolderCalls: [],
    spawnCalls: [],
    terminalCommands: []
  };
  const extension = await loadExtension(stub);
  const context = { subscriptions: [] as Array<{ dispose?: () => void }> };
  extension.activate(context);

  const openWorkspace = stub.commands.get("genoTools.openWorkspace");
  const openWorkspaceInNewWindow = stub.commands.get(
    "genoTools.openWorkspaceInNewWindow"
  );
  assert.ok(openWorkspace, "current-window command should be registered");
  assert.ok(openWorkspaceInNewWindow, "new-window command should be registered");

  const node = {
    kind: "workspace",
    host: { alias: "local", hostname: "localhost", isDefault: true },
    registry: {
      schema_version: 1,
      host: "localhost",
      generated_at: "2026-09-01T00:00:00Z",
      workspaces: []
    },
    workspace: {
      id: "chore.geno.demo.2026.q3",
      track: "chore",
      domain: "geno",
      name: "demo",
      born: "2026.q3",
      path: "/tmp/demo.2026.q3",
      repos: [],
      state: { tmux: { sessions: [] } }
    }
  };

  await openWorkspace(node);
  await openWorkspaceInNewWindow(node);

  assert.equal(stub.openFolderCalls.length, 2);
  assert.equal(stub.openFolderCalls[0][0].path, "/tmp/demo.2026.q3");
  assert.equal(stub.openFolderCalls[0][1], false);
  assert.equal(stub.openFolderCalls[1][0].path, "/tmp/demo.2026.q3");
  assert.equal(stub.openFolderCalls[1][1], true);
});

test("terminal rows focus their open VS Code terminal", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errorMessages: [],
    inputValues: [],
    openFolderCalls: [],
    spawnCalls: [],
    terminalCommands: []
  };
  const extension = await loadExtension(stub);
  const context = { subscriptions: [] as Array<{ dispose?: () => void }> };
  extension.activate(context);

  let focused = false;
  const focusTerminal = stub.commands.get("genoTools.focusTerminal");
  assert.ok(focusTerminal, "focus terminal command should be registered");
  await focusTerminal({
    kind: "terminal",
    terminal: { show: () => { focused = true; } }
  });
  assert.equal(focused, true);
});

test("view titles expose the extension version and build datetime", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errorMessages: [],
    inputValues: [],
    openFolderCalls: [],
    spawnCalls: [],
    terminalCommands: []
  };
  const extension = await loadExtension(stub);
  const context = { subscriptions: [] as Array<{ dispose?: () => void }> };
  extension.activate(context);

  const expected = "v0.1.0-test · built 2026-09-01T20:00:00.000Z";
  assert.equal(stub.treeDescriptions?.["genoTools.workspaces"], expected);
  assert.equal(stub.treeDescriptions?.["genoTools.currentWorkspace"], expected);
});

test("repository plus initializes a repo and refreshes its host registry", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errorMessages: [],
    inputValues: ["new-repo"],
    openFolderCalls: [],
    spawnCalls: [],
    terminalCommands: []
  };
  const extension = await loadExtension(stub);
  const context = { subscriptions: [] as Array<{ dispose?: () => void }> };
  extension.activate(context);

  const createRepo = stub.commands.get("genoTools.createRepo");
  assert.ok(createRepo, "create repo command should be registered");
  const workspacePath = `/tmp/geno-tools-extension-test-${process.pid}`;
  await createRepo({
    kind: "repoGroup",
    host: { alias: "local", hostname: "localhost", isDefault: true },
    registry: {
      schema_version: 1,
      host: "localhost",
      generated_at: "2026-09-01T00:00:00Z",
      workspaces: []
    },
    workspace: {
      id: "chore.geno.demo.2026.q3",
      track: "chore",
      domain: "geno",
      name: "demo",
      born: "2026.q3",
      path: workspacePath,
      repos: [],
      state: { tmux: { sessions: [] } }
    }
  });

  assert.deepEqual(stub.errorMessages, []);
  assert.deepEqual(JSON.parse(JSON.stringify(stub.spawnCalls)), [
    {
      executable: "git",
      args: ["init", "--", `${workspacePath}/new-repo`]
    },
    {
      executable: "tt-test",
      args: ["-H", "local", "registry", "refresh"]
    }
  ]);
});

test("workspace open actions are adjacent inline buttons", () => {
  const manifest = JSON.parse(
    readFileSync(join(__dirname, "..", "..", "package.json"), "utf8")
  ) as {
    contributes: {
      menus: {
        "view/item/context": Array<{ command: string; group: string }>;
      };
    };
  };
  const actions = manifest.contributes.menus["view/item/context"]
    .filter((item) => item.command.startsWith("genoTools.openWorkspace"))
    .map(({ command, group }) => ({ command, group }));

  assert.deepEqual(actions, [
    { command: "genoTools.openWorkspace", group: "inline@2" },
    {
      command: "genoTools.openWorkspaceInNewWindow",
      group: "inline@3"
    }
  ]);
});

test("plus buttons create workspaces, repositories, and tmux sessions", () => {
  const manifest = JSON.parse(
    readFileSync(join(__dirname, "..", "..", "package.json"), "utf8")
  ) as {
    contributes: {
      commands: Array<{ command: string; icon?: string }>;
      menus: {
        "view/title": Array<{ command: string; when: string; group: string }>;
        "view/item/context": Array<{
          command: string;
          when: string;
          group: string;
        }>;
      };
    };
  };
  const plusCommands = manifest.contributes.commands.filter(({ command }) =>
    [
      "genoTools.createWorkspace",
      "genoTools.createRepo",
      "genoTools.createTmuxSession"
    ].includes(command)
  );
  assert.ok(plusCommands.every(({ icon }) => icon === "$(add)"));

  assert.deepEqual(
    manifest.contributes.menus["view/title"]
      .filter(({ group }) => group === "navigation@1")
      .map(({ command, when }) => ({ command, when })),
    [
      { command: "genoTools.createWorkspace", when: "view == genoTools.workspaces" },
      {
        command: "genoTools.createWorkspace",
        when: "view == genoTools.currentWorkspace"
      }
    ]
  );

  assert.deepEqual(
    manifest.contributes.menus["view/item/context"]
      .filter(({ command }) =>
        command === "genoTools.createRepo" ||
        command === "genoTools.createTmuxSession"
      )
      .map(({ command, when, group }) => ({ command, when, group })),
    [
      {
        command: "genoTools.createRepo",
        when: "(view == genoTools.workspaces || view == genoTools.currentWorkspace) && viewItem == repoGroup",
        group: "inline@1"
      },
      {
        command: "genoTools.createTmuxSession",
        when: "(view == genoTools.workspaces || view == genoTools.currentWorkspace) && viewItem == tmuxSessionGroup",
        group: "inline@1"
      }
    ]
  );
});

test("VS Code terminal groups have a live refresh button", () => {
  const manifest = JSON.parse(
    readFileSync(join(__dirname, "..", "..", "package.json"), "utf8")
  ) as {
    contributes: {
      commands: Array<{ command: string; icon?: string }>;
      menus: {
        "view/item/context": Array<{
          command: string;
          when: string;
          group: string;
        }>;
      };
    };
  };
  const command = manifest.contributes.commands.find(
    ({ command }) => command === "genoTools.refreshTerminals"
  );
  assert.equal(command?.icon, "$(refresh)");
  assert.deepEqual(
    manifest.contributes.menus["view/item/context"].find(
      ({ command }) => command === "genoTools.refreshTerminals"
    ),
    {
      command: "genoTools.refreshTerminals",
      when: "(view == genoTools.workspaces || view == genoTools.currentWorkspace) && viewItem == terminalGroup",
      group: "inline@1"
    }
  );
});

test("unlinked terminal rows expose the OpenAI tmux recovery button", () => {
  const manifest = JSON.parse(
    readFileSync(join(__dirname, "..", "..", "package.json"), "utf8")
  ) as {
    dependencies: Record<string, string>;
    contributes: {
      commands: Array<{ command: string; icon?: string }>;
      menus: {
        "view/item/context": Array<{
          command: string;
          when: string;
          group: string;
        }>;
      };
      configuration: {
        properties: Record<string, { default?: unknown }>;
      };
    };
  };
  assert.equal(manifest.dependencies["@openai/agents"], "^0.17.0");
  assert.equal(
    manifest.contributes.configuration.properties["genoTools.agentModel"].default,
    ""
  );
  assert.equal(
    manifest.contributes.configuration.properties["genoTools.agentConfigPath"].default,
    "~/.geno/config.yaml"
  );
  assert.deepEqual(
    manifest.contributes.commands.find(
      ({ command }) => command === "genoTools.recoverTerminalInTmux"
    ),
    {
      command: "genoTools.recoverTerminalInTmux",
      title: "Geno Tools: Recover Terminal in tmux with OpenAI",
      icon: "$(robot)"
    }
  );
  assert.deepEqual(
    manifest.contributes.menus["view/item/context"].find(
      ({ command }) => command === "genoTools.recoverTerminalInTmux"
    ),
    {
      command: "genoTools.recoverTerminalInTmux",
      when: "(view == genoTools.workspaces || view == genoTools.currentWorkspace) && viewItem == terminal",
      group: "inline@1"
    }
  );
});

test("tmux rows expose adjacent reopen and confirmed delete actions", () => {
  const manifest = JSON.parse(
    readFileSync(join(__dirname, "..", "..", "package.json"), "utf8")
  ) as {
    contributes: {
      commands: Array<{ command: string; icon?: string }>;
      menus: {
        "view/item/context": Array<{
          command: string;
          when: string;
          group: string;
        }>;
      };
    };
  };
  assert.deepEqual(
    manifest.contributes.commands.find(
      ({ command }) => command === "genoTools.deleteTmuxSession"
    ),
    {
      command: "genoTools.deleteTmuxSession",
      title: "Geno Tools: Delete tmux Session",
      icon: "$(trash)"
    }
  );
  assert.deepEqual(
    manifest.contributes.menus["view/item/context"]
      .filter(({ command }) =>
        command === "genoTools.openTmuxSession" ||
        command === "genoTools.deleteTmuxSession"
      )
      .map(({ command, group }) => ({ command, group })),
    [
      { command: "genoTools.openTmuxSession", group: "inline@1" },
      { command: "genoTools.deleteTmuxSession", group: "inline@2" }
    ]
  );
});

test("the recovery agent creates, seeds, registers, and attaches a tmux session", async (t) => {
  const sessionId = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";
  const history = [
    "Human: continue the distinctive workspace cleanup implementation",
    "Assistant: I will preserve every open editor window while repairing the registry"
  ];
  const temporaryHome = await createCodexSessionHome(
    "/tmp/demo.2026.q3/repo-a",
    sessionId,
    history
  );
  const previousHome = process.env.HOME;
  process.env.HOME = temporaryHome;
  t.after(async () => {
    if (previousHome === undefined) {
      delete process.env.HOME;
    } else {
      process.env.HOME = previousHome;
    }
    await rm(temporaryHome, { recursive: true, force: true });
  });
  const stub: VscodeStub = {
    agentProposal: {
      sessionName: "recovered-work",
      workingDirectory: "/tmp/demo.2026.q3/repo-a",
      summary: "Continue the cleanup task."
    },
    clipboardText: "original clipboard",
    commands: new Map(),
    errorMessages: [],
    informationResults: ["Create tmux Session"],
    inputValues: [],
    openFolderCalls: [],
    spawnCalls: [],
    terminalCommands: [],
    terminalHistory: history.join("\n"),
    warningResults: ["Scan History"]
  };
  const extension = await loadExtension(stub);
  const contextObject = { subscriptions: [] as Array<{ dispose?: () => void }> };
  extension.activate(contextObject);
  const recover = stub.commands.get("genoTools.recoverTerminalInTmux");
  assert.ok(recover, "recovery command should be registered");

  const previousKey = process.env.OPENAI_API_KEY;
  process.env.OPENAI_API_KEY = "test-only";
  try {
    await recover({
      kind: "terminal",
      host: { alias: "local", hostname: "localhost", isDefault: true },
      registry: {
        schema_version: 1,
        host: "localhost",
        generated_at: "2026-09-01T00:00:00Z",
        workspaces: []
      },
      workspace: {
        id: "chore.geno.demo.2026.q3",
        track: "chore",
        domain: "geno",
        name: "demo",
        born: "2026.q3",
        path: "/tmp/demo.2026.q3",
        repos: [],
        state: { tmux: { sessions: [] } }
      },
      terminal: { name: "cleanup shell", show() {} },
      cwd: "/tmp/demo.2026.q3/repo-a"
    });
  } finally {
    if (previousKey === undefined) {
      delete process.env.OPENAI_API_KEY;
    } else {
      process.env.OPENAI_API_KEY = previousKey;
    }
  }

  assert.equal(stub.clipboardText, "original clipboard");
  assert.equal(stub.agentOptions?.model, "gpt-5.6");
  assert.deepEqual(JSON.parse(JSON.stringify(stub.spawnCalls)), [
    {
      executable: "tmux",
      args: [
        "new-session",
        "-d",
        "-s",
        "recovered-work",
        "-c",
        "/tmp/demo.2026.q3/repo-a"
      ]
    },
    {
      executable: "tmux",
      args: [
        "send-keys",
        "-t",
        "recovered-work",
        "-l",
        "--",
        `codexd resume ${sessionId}`
      ]
    },
    {
      executable: "tmux",
      args: ["send-keys", "-t", "recovered-work", "Enter"]
    },
    {
      executable: "tt-test",
      args: ["-H", "local", "registry", "refresh"]
    }
  ]);
  assert.deepEqual(stub.terminalCommands, [
    "tt-test -H local tmux repo-a recovered-work"
  ]);
});

test("recovery does not create tmux without a matching saved agent session", async () => {
  const temporaryHome = await mkdtemp(join(tmpdir(), "geno-empty-agent-home-"));
  const previousHome = process.env.HOME;
  process.env.HOME = temporaryHome;
  const stub: VscodeStub = {
    agentProposal: {
      sessionName: "missing-agent-work",
      workingDirectory: "/tmp/missing-session.2026.q3/repo-a",
      summary: "Continue work from the missing agent session."
    },
    clipboardText: "original clipboard",
    commands: new Map(),
    errorMessages: [],
    informationResults: ["Create tmux Session"],
    inputValues: [],
    openFolderCalls: [],
    spawnCalls: [],
    terminalCommands: [],
    terminalHistory: [
      "$ codexd",
      "Human: continue the distinctive missing agent task from yesterday",
      "Assistant: I will inspect the distinctive missing agent implementation"
    ].join("\n"),
    warningResults: ["Scan History"]
  };

  try {
    const extension = await loadExtension(stub);
    const contextObject = { subscriptions: [] as Array<{ dispose?: () => void }> };
    extension.activate(contextObject);
    const recover = stub.commands.get("genoTools.recoverTerminalInTmux");
    assert.ok(recover);

    const previousKey = process.env.OPENAI_API_KEY;
    process.env.OPENAI_API_KEY = "test-only";
    try {
      await recover({
        kind: "terminal",
        host: { alias: "local", hostname: "localhost", isDefault: true },
        registry: {
          schema_version: 1,
          host: "localhost",
          generated_at: "2026-09-01T00:00:00Z",
          workspaces: []
        },
        workspace: {
          id: "chore.geno.missing-session.2026.q3",
          track: "chore",
          domain: "geno",
          name: "missing-session",
          born: "2026.q3",
          path: "/tmp/missing-session.2026.q3",
          repos: [],
          state: { tmux: { sessions: [] } }
        },
        terminal: { name: "lost agent", show() {} },
        cwd: "/tmp/missing-session.2026.q3/repo-a"
      });
    } finally {
      if (previousKey === undefined) {
        delete process.env.OPENAI_API_KEY;
      } else {
        process.env.OPENAI_API_KEY = previousKey;
      }
    }

    assert.deepEqual(stub.spawnCalls, []);
    assert.match(stub.errorMessages[0] ?? "", /no saved Claude or Codex session/i);
  } finally {
    if (previousHome === undefined) {
      delete process.env.HOME;
    } else {
      process.env.HOME = previousHome;
    }
    await rm(temporaryHome, { recursive: true, force: true });
  }
});

test("a recovery proposal can be renamed before tmux creation", async (t) => {
  const sessionId = "11111111-2222-4333-8444-555555555555";
  const history = [
    "Human: receiver deployment follow up for the live GUI investigation",
    "Assistant: I will trace why deployed IQ samples remain at zero"
  ];
  const temporaryHome = await createCodexSessionHome(
    "/tmp/demo.2026.q3",
    sessionId,
    history
  );
  const previousHome = process.env.HOME;
  process.env.HOME = temporaryHome;
  t.after(async () => {
    if (previousHome === undefined) {
      delete process.env.HOME;
    } else {
      process.env.HOME = previousHome;
    }
    await rm(temporaryHome, { recursive: true, force: true });
  });
  const stub: VscodeStub = {
    agentProposal: {
      sessionName: "receiver-z2-recovery",
      workingDirectory: "/tmp/demo.2026.q3",
      summary: "Follow up on the receiver deployment."
    },
    clipboardText: "original clipboard",
    commands: new Map(),
    errorMessages: [],
    informationResults: ["Edit Name…", "Create tmux Session"],
    inputValues: ["receiver-deployment-follow-up"],
    openFolderCalls: [],
    spawnCalls: [],
    terminalCommands: [],
    terminalHistory: history.join("\n"),
    warningResults: ["Scan History"]
  };
  const extension = await loadExtension(stub);
  const contextObject = { subscriptions: [] as Array<{ dispose?: () => void }> };
  extension.activate(contextObject);
  const recover = stub.commands.get("genoTools.recoverTerminalInTmux");
  assert.ok(recover);

  const previousKey = process.env.OPENAI_API_KEY;
  process.env.OPENAI_API_KEY = "test-only";
  try {
    await recover({
      kind: "terminal",
      host: { alias: "local", hostname: "localhost", isDefault: true },
      registry: {
        schema_version: 1,
        host: "localhost",
        generated_at: "2026-09-01T00:00:00Z",
        workspaces: []
      },
      workspace: {
        id: "chore.geno.demo.2026.q3",
        track: "chore",
        domain: "geno",
        name: "demo",
        born: "2026.q3",
        path: "/tmp/demo.2026.q3",
        repos: [],
        state: { tmux: { sessions: [] } }
      },
      terminal: { name: "receiver shell", show() {} },
      cwd: "/tmp/demo.2026.q3"
    });
  } finally {
    if (previousKey === undefined) {
      delete process.env.OPENAI_API_KEY;
    } else {
      process.env.OPENAI_API_KEY = previousKey;
    }
  }

  assert.deepEqual(JSON.parse(JSON.stringify(stub.spawnCalls)), [
    {
      executable: "tmux",
      args: [
        "new-session",
        "-d",
        "-s",
        "receiver-deployment-follow-up",
        "-c",
        "/tmp/demo.2026.q3"
      ]
    },
    {
      executable: "tmux",
      args: [
        "send-keys",
        "-t",
        "receiver-deployment-follow-up",
        "-l",
        "--",
        `codexd resume ${sessionId}`
      ]
    },
    {
      executable: "tmux",
      args: ["send-keys", "-t", "receiver-deployment-follow-up", "Enter"]
    },
    {
      executable: "tt-test",
      args: ["-H", "local", "registry", "refresh"]
    }
  ]);
  assert.deepEqual(stub.terminalCommands, [
    "tt-test -H local tmux demo.2026.q3 receiver-deployment-follow-up"
  ]);
});

async function createCodexSessionHome(
  workingDirectory: string,
  sessionId: string,
  messages: readonly string[]
): Promise<string> {
  const home = await mkdtemp(join(tmpdir(), "geno-codex-session-home-"));
  const sessionsDirectory = join(home, ".codex", "sessions", "2026", "09", "01");
  await mkdir(sessionsDirectory, { recursive: true });
  const records = [
    {
      type: "session_meta",
      timestamp: "2026-09-01T17:00:00Z",
      payload: { id: sessionId, cwd: workingDirectory }
    },
    ...messages.map((message, index) => ({
      type: "response_item",
      payload: {
        type: "message",
        role: index % 2 === 0 ? "user" : "assistant",
        content: [{
          type: index % 2 === 0 ? "input_text" : "output_text",
          text: message
        }]
      }
    }))
  ];
  await writeFile(
    join(sessionsDirectory, `rollout-2026-09-01T10-00-00-${sessionId}.jsonl`),
    `${records.map((record) => JSON.stringify(record)).join("\n")}\n`
  );
  return home;
}

async function loadExtension(
  stub: VscodeStub
): Promise<{ activate(context: object): void }> {
  const result = await esbuild.build({
    entryPoints: [join(__dirname, "..", "extension.ts")],
    bundle: true,
    format: "cjs",
    platform: "node",
    write: false,
    define: {
      __GENO_TOOLS_VERSION__: JSON.stringify("0.1.0-test"),
      __GENO_TOOLS_BUILD_DATETIME__: JSON.stringify("2026-09-01T20:00:00.000Z")
    },
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
              ProgressLocation: { Notification: 15 },
              env: {
                clipboard: {
                  readText: async () => state.clipboardText ?? "",
                  writeText: async (value) => { state.clipboardText = value; }
                }
              },
              workspace: {
                workspaceFolders: [],
                workspaceFile: undefined,
                onDidChangeWorkspaceFolders: () => ({ dispose() {} }),
                getConfiguration: () => ({
                  get: (key, fallback) => {
                    if (key === "ttPath") return "tt-test";
                    if (key === "agentConfigPath") {
                      return "/tmp/geno-tools-extension-missing-config.yaml";
                    }
                    return fallback;
                  }
                })
              },
              Uri: {
                file: (path) => ({ scheme: "file", path }),
                from: (parts) => parts
              },
              window: {
                terminals: [],
                onDidOpenTerminal: () => ({ dispose() {} }),
                onDidCloseTerminal: () => ({ dispose() {} }),
                onDidChangeTerminalShellIntegration: () => ({ dispose() {} }),
                createOutputChannel: () => ({
                  append() {}, appendLine() {}, show() {}, dispose() {}
                }),
                createTreeView: (id) => {
                  const view = { selection: [], dispose() {} };
                  Object.defineProperty(view, "description", {
                    set(value) {
                      state.treeDescriptions ??= {};
                      state.treeDescriptions[id] = value;
                    }
                  });
                  return view;
                },
                withProgress: async (_options, task) => task(
                  {},
                  { onCancellationRequested: () => ({ dispose() {} }) }
                ),
                createTerminal: () => ({
                  show() {},
                  sendText(command) { state.terminalCommands.push(command); }
                }),
                showInputBox: async () => state.inputValues.shift(),
                showWarningMessage: async () => state.warningResults?.shift(),
                showInformationMessage: async () => state.informationResults?.shift(),
                showErrorMessage: async (message) => {
                  state.errorMessages.push(message);
                  return undefined;
                }
              },
              commands: {
                registerCommand: (name, callback) => {
                  state.commands.set(name, callback);
                  return { dispose() {} };
                },
                executeCommand: async (name, ...args) => {
                  if (name === "vscode.openFolder") {
                    state.openFolderCalls.push(args);
                  }
                  if (name === "workbench.action.terminal.copySelection") {
                    state.clipboardText = state.terminalHistory ?? "";
                  }
                }
              }
            };
          `,
          loader: "js"
        }));
        build.onResolve({ filter: /^@openai\/agents$/ }, () => ({
          path: "@openai/agents",
          namespace: "openai-agents-stub"
        }));
        build.onLoad({ filter: /.*/, namespace: "openai-agents-stub" }, () => ({
          contents: `
            const state = globalThis.__vscodeStub;
            class Agent {
              constructor(options) {
                this.options = options;
                state.agentOptions = options;
              }
            }
            class OpenAIProvider {
              constructor(options) { state.providerOptions = options; }
              async close() {}
            }
            class Runner {
              constructor(config) { state.runnerConfig = config; }
              async run() {
                if (!state.agentProposal) {
                  throw new Error("Unexpected OpenAI agent run in test");
                }
                return { finalOutput: state.agentProposal };
              }
            }
            module.exports = { Agent, OpenAIProvider, Runner };
          `,
          loader: "js"
        }));
        build.onResolve({ filter: /^node:child_process$/ }, () => ({
          path: "node:child_process",
          namespace: "child-process-stub"
        }));
        build.onLoad({ filter: /.*/, namespace: "child-process-stub" }, () => ({
          contents: `
            const state = globalThis.__vscodeStub;
            function spawn(executable, args) {
              state.spawnCalls.push({ executable, args });
              const listeners = {};
              const stream = { on() { return stream; } };
              const child = {
                stdout: stream,
                stderr: stream,
                kill() {},
                on(event, callback) {
                  listeners[event] = callback;
                  if (event === "close") {
                    Promise.resolve().then(() => callback(0));
                  }
                  return child;
                }
              };
              return child;
            }
            module.exports = { spawn };
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
    __vscodeStub: stub
  });
  return compiledModule.exports as unknown as { activate(context: object): void };
}
