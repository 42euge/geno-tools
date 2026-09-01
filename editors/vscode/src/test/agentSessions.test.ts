import assert from "node:assert/strict";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  agentResumeCommand,
  findAgentSessionMatches
} from "../agentSessions";

test("Claude scrollback resolves to a saved session and resume command", async () => {
  const homeDirectory = await mkdtemp(join(tmpdir(), "geno-agent-sessions-"));
  const workspacePath = "/tmp/demo.2026.q3";
  const currentDirectory = `${workspacePath}/repo-a`;
  const projectDirectory = join(
    homeDirectory,
    ".claude",
    "projects",
    "-tmp-demo-2026-q3-repo-a"
  );
  const sessionId = "11111111-2222-4333-8444-555555555555";

  try {
    await mkdir(projectDirectory, { recursive: true });
    await writeJsonl(join(projectDirectory, `${sessionId}.jsonl`), [
      {
        type: "user",
        cwd: currentDirectory,
        sessionId,
        message: {
          role: "user",
          content: "Investigate why the receiver GUI is live while IQ samples stay at zero."
        }
      },
      {
        type: "assistant",
        cwd: currentDirectory,
        sessionId,
        message: {
          role: "assistant",
          content: [{
            type: "text",
            text: "I will trace the receive pipeline and verify the deployed digitizer configuration."
          }]
        }
      }
    ]);

    const matches = await findAgentSessionMatches(
      [
        "Investigate why the receiver GUI is live while IQ samples stay at zero.",
        "I will trace the receive pipeline and verify the deployed digitizer configuration."
      ].join("\n"),
      { currentDirectory, workspacePath },
      { homeDirectory }
    );

    assert.equal(matches[0]?.agent, "claude");
    assert.equal(matches[0]?.sessionId, sessionId);
    assert.ok((matches[0]?.score ?? 0) >= 2);
    assert.equal(agentResumeCommand(matches[0]), `clauded -r ${sessionId}`);
  } finally {
    await rm(homeDirectory, { recursive: true, force: true });
  }
});

test("Codex scrollback resolves to a saved session and resume command", async () => {
  const homeDirectory = await mkdtemp(join(tmpdir(), "geno-agent-sessions-"));
  const workspacePath = "/tmp/demo.2026.q3";
  const currentDirectory = `${workspacePath}/repo-a`;
  const sessionId = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";
  const sessionsDirectory = join(
    homeDirectory,
    ".codex",
    "sessions",
    "2026",
    "09",
    "01"
  );

  try {
    await mkdir(sessionsDirectory, { recursive: true });
    await writeJsonl(
      join(sessionsDirectory, `rollout-2026-09-01T10-00-00-${sessionId}.jsonl`),
      [
        {
          type: "session_meta",
          timestamp: "2026-09-01T17:00:00Z",
          payload: { id: sessionId, cwd: currentDirectory }
        },
        {
          type: "response_item",
          payload: {
            type: "message",
            role: "user",
            content: [{
              type: "input_text",
              text: "Repair the workspace registry without replacing any open VS Code window."
            }]
          }
        },
        {
          type: "response_item",
          payload: {
            type: "message",
            role: "assistant",
            content: [{
              type: "output_text",
              text: "I will register every open workspace before launching the new editor window."
            }]
          }
        }
      ]
    );

    const matches = await findAgentSessionMatches(
      [
        "Repair the workspace registry without replacing any open VS Code window.",
        "I will register every open workspace before launching the new editor window."
      ].join("\n"),
      { currentDirectory, workspacePath },
      { homeDirectory }
    );

    assert.equal(matches[0]?.agent, "codex");
    assert.equal(matches[0]?.sessionId, sessionId);
    assert.equal(agentResumeCommand(matches[0]), `codexd resume ${sessionId}`);
  } finally {
    await rm(homeDirectory, { recursive: true, force: true });
  }
});

test("equally plausible saved sessions are not guessed", async () => {
  const homeDirectory = await mkdtemp(join(tmpdir(), "geno-agent-sessions-"));
  const workspacePath = "/tmp/demo.2026.q3";
  const currentDirectory = `${workspacePath}/repo-a`;
  const projectDirectory = join(
    homeDirectory,
    ".claude",
    "projects",
    "-tmp-demo-2026-q3-repo-a"
  );
  const history = [
    "Human: investigate the first distinctive receiver pipeline behavior",
    "Assistant: inspect the second distinctive digitizer configuration detail",
    "Human: preserve the third distinctive editor workspace requirement",
    "Assistant: verify the fourth distinctive terminal registry outcome"
  ];

  try {
    await mkdir(projectDirectory, { recursive: true });
    for (const sessionId of [
      "11111111-2222-4333-8444-555555555555",
      "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
    ]) {
      await writeJsonl(join(projectDirectory, `${sessionId}.jsonl`), history.map(
        (content, index) => ({
          type: index % 2 === 0 ? "user" : "assistant",
          cwd: currentDirectory,
          sessionId,
          message: {
            role: index % 2 === 0 ? "user" : "assistant",
            content
          }
        })
      ));
    }

    const matches = await findAgentSessionMatches(
      history.join("\n"),
      { currentDirectory, workspacePath },
      { homeDirectory }
    );

    assert.deepEqual(matches, []);
  } finally {
    await rm(homeDirectory, { recursive: true, force: true });
  }
});

async function writeJsonl(
  path: string,
  records: readonly Record<string, unknown>[]
): Promise<void> {
  await writeFile(path, `${records.map((record) => JSON.stringify(record)).join("\n")}\n`);
}
