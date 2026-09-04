import assert from "node:assert/strict";
import test from "node:test";

import {
  parseVsCodeTerminalGroups,
  UnsupportedVsCodeTerminalLayoutReader
} from "../terminalLayout";

test("VS Code internal layout JSON exposes persistent terminal groups", () => {
  const value = JSON.stringify({
    workspaceId: "workspace-id",
    tabs: [
      {
        isActive: true,
        activePersistentProcessId: 39,
        terminals: [
          { relativeSize: 0.6, terminal: 39 },
          { relativeSize: 0.4, terminal: 41 }
        ]
      },
      {
        isActive: false,
        activePersistentProcessId: 40,
        terminals: [{ relativeSize: 1, terminal: 40 }]
      }
    ],
    background: []
  });

  assert.deepEqual(parseVsCodeTerminalGroups(value), [[39, 41], [40]]);
});

test("malformed VS Code internal layout JSON is ignored", () => {
  assert.doesNotThrow(() => parseVsCodeTerminalGroups("{not-json"));
  assert.equal(parseVsCodeTerminalGroups("{not-json"), undefined);
});

test("the unsupported reader loads layout state beside extension storage", async () => {
  const expectedDatabase = "/tmp/workspaceStorage/hash/state.vscdb";
  const reader = new UnsupportedVsCodeTerminalLayoutReader(
    "/tmp/workspaceStorage/hash/42euge.geno-tools-tt-workspaces",
    () => {},
    async (databasePath) => {
      if (databasePath !== expectedDatabase) {
        throw new Error(`unexpected database path: ${databasePath}`);
      }
      return JSON.stringify({
        tabs: [
          { terminals: [{ terminal: 39 }, { terminal: 41 }] },
          { terminals: [{ terminal: 40 }] }
        ]
      });
    }
  );

  assert.deepEqual(await reader.readGroups(), [[39, 41], [40]]);
});
