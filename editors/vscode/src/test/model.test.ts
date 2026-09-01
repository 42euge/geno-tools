import assert from "node:assert/strict";
import test from "node:test";

import {
  activeDispatchesForWorkspace,
  parseDispatches,
  parseHosts,
  parseRegistry,
  relativeAge,
  sortedTracks,
  workspaceReference
} from "../model";

test("parseDispatches validates the editor-facing dispatch record", () => {
  const dispatches = parseDispatches(JSON.stringify([{
    name: "parser-fix",
    status: "active",
    session: "dispatch-parser-fix",
    created_at: "2026-09-01T12:00:00+00:00",
    source: { workspace_view: "/Users/dev/code/chore/geno/parser.2026.q3" },
    target: { host_alias: "build", hostname: "build.example.com" }
  }]));

  assert.deepEqual(dispatches, [{
    name: "parser-fix",
    status: "active",
    session: "dispatch-parser-fix",
    created_at: "2026-09-01T12:00:00+00:00",
    source: { workspace_view: "/Users/dev/code/chore/geno/parser.2026.q3" },
    target: { host_alias: "build", hostname: "build.example.com" },
    return_file: undefined
  }]);
});

test("parseDispatches rejects malformed records", () => {
  assert.throws(() => parseDispatches("{}"), /not an array/);
  assert.throws(
    () => parseDispatches('[{"name":"missing-state"}]'),
    /dispatch entry 0 is invalid/
  );
});

test("activeDispatchesForWorkspace selects current root and worktree dispatches", () => {
  const record = {
    name: "root",
    status: "active",
    session: "dispatch-root",
    created_at: "2026-09-01T12:00:00+00:00",
    source: { workspace_view: "/code/crit/ngrt/receiver.2026.q3" },
    target: { host_alias: "z2", hostname: "ngrt-ug-z2" }
  };
  const selected = activeDispatchesForWorkspace(
    [
      record,
      {
        ...record,
        name: "worktree",
        created_at: "2026-09-01T13:00:00+00:00",
        source: {
          workspace_view: "/code/crit/ngrt/receiver.2026.q3/.wt/feature"
        }
      },
      { ...record, name: "recalled", status: "recalled" },
      {
        ...record,
        name: "other",
        source: { workspace_view: "/code/crit/ngrt/other.2026.q3" }
      }
    ],
    "/code/crit/ngrt/receiver.2026.q3"
  );

  assert.deepEqual(selected.map(({ name }) => name), ["worktree", "root"]);
});

test("parseHosts recognizes aliases, hostnames, and the default host", () => {
  assert.deepEqual(
    parseHosts("  z2 -> build.example.com\n  local -> localhost (default)\n"),
    [
      { alias: "local", hostname: "localhost", isDefault: true },
      { alias: "z2", hostname: "build.example.com", isDefault: false }
    ]
  );
});

test("parseHosts ignores unrelated output", () => {
  assert.deepEqual(parseHosts("No hosts configured\n"), []);
});

test("parseRegistry validates and returns the TT schema", () => {
  const registry = parseRegistry(
    JSON.stringify({
      schema_version: 1,
      host: "localhost",
      generated_at: "2026-09-01T00:00:00+00:00",
      workspaces: [
        {
          id: "chore.geno.tools-cleanup.2026.q3",
          track: "chore",
          domain: "geno",
          name: "tools-cleanup",
          born: "2026.q3",
          path: "/home/dev/code/chore/geno/tools-cleanup.2026.q3",
          state: {
            tmux: {
              sessions: [
                {
                  session_name: "ws-tools-cleanup",
                  pane_current_path: "/home/dev/code/chore/geno/tools-cleanup.2026.q3",
                  pane_current_command: "codex",
                  session_activity: 1788249600
                }
              ]
            }
          },
          repos: [
            {
              name: "geno-tools",
              path: "/home/dev/code/chore/geno/tools-cleanup.2026.q3/geno-tools",
              last_accessed: "2026-09-01T00:00:00+00:00"
            }
          ]
        }
      ]
    })
  );

  assert.equal(registry.workspaces[0].name, "tools-cleanup");
  assert.equal(registry.workspaces[0].repos[0].name, "geno-tools");
  assert.equal(
    registry.workspaces[0].state.tmux.sessions[0].session_name,
    "ws-tools-cleanup"
  );
  assert.equal(workspaceReference(registry.workspaces[0]), "tools-cleanup.2026.q3");
});

test("parseRegistry rejects unsupported data", () => {
  assert.throws(
    () => parseRegistry('{"schema_version":2,"workspaces":[]}'),
    /unsupported workspace registry schema/
  );
  assert.throws(() => parseRegistry("not json"), /invalid workspace registry/);
});

test("sortedTracks uses TT's canonical track order", () => {
  const workspace = {
    id: "id",
    domain: "domain",
    name: "name",
    born: "2026.q3",
    path: "/tmp/name",
    repos: [],
    state: { tmux: { sessions: [] } }
  };
  assert.deepEqual(
    sortedTracks([
      { ...workspace, track: "side" },
      { ...workspace, track: "custom" },
      { ...workspace, track: "crit" },
      { ...workspace, track: "chore" }
    ]),
    ["crit", "chore", "side", "custom"]
  );
});

test("relativeAge renders useful short labels", () => {
  const now = Date.parse("2026-09-01T12:00:00Z");
  assert.equal(relativeAge("2026-09-01T01:00:00Z", now), "today");
  assert.equal(relativeAge("2026-08-31T01:00:00Z", now), "1d ago");
  assert.equal(relativeAge("2026-07-01T01:00:00Z", now), "2mo ago");
  assert.equal(relativeAge("unknown", now), "unknown");
});
