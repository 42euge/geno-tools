import { createReadStream } from "node:fs";
import { readdir, stat } from "node:fs/promises";
import { homedir } from "node:os";
import { basename, dirname, join, normalize, resolve } from "node:path";
import { createInterface } from "node:readline";

const MIN_MATCH_SCORE = 2;
const MAX_DOCUMENT_FREQUENCY = 3;
const MIN_FINGERPRINT_LENGTH = 25;
const SESSION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export type AgentKind = "claude" | "codex";

export interface AgentSessionMatch {
  agent: AgentKind;
  sessionId: string;
  workingDirectory: string;
  score: number;
  modifiedAt: number;
}

export interface AgentSessionContext {
  workspacePath: string;
  currentDirectory?: string;
}

export interface AgentSessionStoreOptions {
  homeDirectory?: string;
}

interface SessionEvidence {
  match: Omit<AgentSessionMatch, "score">;
  fingerprints: Set<string>;
}

export async function findAgentSessionMatches(
  history: string,
  context: AgentSessionContext,
  options: AgentSessionStoreOptions = {}
): Promise<AgentSessionMatch[]> {
  const fingerprints = fingerprintLines(history);
  if (fingerprints.length === 0) {
    return [];
  }

  const homeDirectory = options.homeDirectory ?? homedir();
  const claudeSessions = await findClaudeSessions(
    homeDirectory,
    context,
    fingerprints
  );
  const codexSessions = await findCodexSessions(
    homeDirectory,
    context,
    fingerprints
  );
  return scoreSessions([...claudeSessions, ...codexSessions], fingerprints);
}

export function agentResumeCommand(
  match: AgentSessionMatch | undefined
): string {
  if (!match || !SESSION_ID.test(match.sessionId)) {
    throw new Error("Cannot resume an agent session without a valid saved session ID.");
  }
  return match.agent === "claude"
    ? `clauded -r ${match.sessionId}`
    : `codexd resume ${match.sessionId}`;
}

async function findClaudeSessions(
  homeDirectory: string,
  context: AgentSessionContext,
  fingerprints: readonly string[]
): Promise<SessionEvidence[]> {
  const projectsRoot = join(homeDirectory, ".claude", "projects");
  const paths = new Map<string, string>();
  for (const workingDirectory of relevantDirectories(context)) {
    const projectDirectory = join(projectsRoot, mungeClaudeDirectory(workingDirectory));
    for (const file of await jsonlFiles(projectDirectory)) {
      paths.set(file, workingDirectory);
    }
  }

  return Promise.all([...paths].map(async ([path, fallbackDirectory]) => {
    const sessionId = basename(path, ".jsonl");
    const fileStat = await stat(path);
    const scanned = await scanClaudeSession(path, fingerprints);
    return {
      match: {
        agent: "claude" as const,
        sessionId,
        workingDirectory: scanned.workingDirectory ?? fallbackDirectory,
        modifiedAt: fileStat.mtimeMs
      },
      fingerprints: scanned.fingerprints
    };
  })).then((sessions) => sessions.filter(({ match }) =>
    SESSION_ID.test(match.sessionId) &&
    pathIsInside(match.workingDirectory, context.workspacePath)
  ));
}

async function scanClaudeSession(
  path: string,
  fingerprints: readonly string[]
): Promise<{ workingDirectory?: string; fingerprints: Set<string> }> {
  const found = new Set<string>();
  let workingDirectory: string | undefined;
  const input = createReadStream(path, { encoding: "utf8" });
  const lines = createInterface({ input, crlfDelay: Infinity });
  try {
    for await (const line of lines) {
      const record = parseRecord(line);
      if (!record) {
        continue;
      }
      if (!workingDirectory && typeof record.cwd === "string") {
        workingDirectory = record.cwd;
      }
      const text = normalizeText(messageText(record.message));
      if (!text) {
        continue;
      }
      for (const fingerprint of fingerprints) {
        if (!found.has(fingerprint) && text.includes(fingerprint.slice(0, 60))) {
          found.add(fingerprint);
        }
      }
    }
  } finally {
    lines.close();
    input.destroy();
  }
  return { workingDirectory, fingerprints: found };
}

async function findCodexSessions(
  homeDirectory: string,
  context: AgentSessionContext,
  fingerprints: readonly string[]
): Promise<SessionEvidence[]> {
  const sessionsRoot = join(homeDirectory, ".codex", "sessions");
  const files = await recursiveJsonlFiles(sessionsRoot);
  const candidates = (await Promise.all(files.map(async (path) => {
    const metadata = await readFirstRecord(path);
    const payload = isRecord(metadata?.payload) ? metadata.payload : undefined;
    const sessionId = typeof payload?.id === "string"
      ? payload.id
      : typeof payload?.session_id === "string"
        ? payload.session_id
        : undefined;
    const workingDirectory = typeof payload?.cwd === "string"
      ? payload.cwd
      : undefined;
    if (
      metadata?.type !== "session_meta" ||
      !sessionId ||
      !SESSION_ID.test(sessionId) ||
      !workingDirectory ||
      !pathIsInside(workingDirectory, context.workspacePath)
    ) {
      return undefined;
    }
    return { path, sessionId, workingDirectory };
  }))).filter((candidate) => candidate !== undefined);

  return Promise.all(candidates.map(async (candidate) => {
    const fileStat = await stat(candidate.path);
    return {
      match: {
        agent: "codex" as const,
        sessionId: candidate.sessionId,
        workingDirectory: candidate.workingDirectory,
        modifiedAt: fileStat.mtimeMs
      },
      fingerprints: await scanCodexSession(candidate.path, fingerprints)
    };
  }));
}

async function scanCodexSession(
  path: string,
  fingerprints: readonly string[]
): Promise<Set<string>> {
  const found = new Set<string>();
  await forEachJsonlRecord(path, (record) => {
    if (record.type !== "response_item" || !isRecord(record.payload)) {
      return;
    }
    const payload = record.payload;
    if (
      payload.type !== "message" ||
      (payload.role !== "user" && payload.role !== "assistant")
    ) {
      return;
    }
    const text = normalizeText(messageText(payload));
    for (const fingerprint of fingerprints) {
      if (!found.has(fingerprint) && text.includes(fingerprint.slice(0, 60))) {
        found.add(fingerprint);
      }
    }
  });
  return found;
}

function scoreSessions(
  sessions: readonly SessionEvidence[],
  fingerprints: readonly string[]
): AgentSessionMatch[] {
  const documentFrequency = new Map<string, number>();
  for (const fingerprint of fingerprints) {
    documentFrequency.set(
      fingerprint,
      sessions.filter((session) => session.fingerprints.has(fingerprint)).length
    );
  }

  const ranked = sessions
    .map(({ match, fingerprints: found }) => {
      let score = 0;
      for (const fingerprint of found) {
        const frequency = documentFrequency.get(fingerprint) ?? 0;
        if (frequency > 0 && frequency <= MAX_DOCUMENT_FREQUENCY) {
          score += 1 / frequency;
        }
      }
      return { ...match, score };
    })
    .filter(({ score }) => score >= MIN_MATCH_SCORE)
    .sort((left, right) =>
      right.score - left.score || right.modifiedAt - left.modifiedAt
    );
  return ranked.length > 1 && ranked[0].score === ranked[1].score
    ? []
    : ranked;
}

function fingerprintLines(text: string): string[] {
  return [...new Set(text.split(/\r?\n/)
    .map(normalizeText)
    .filter((line) => line.length >= MIN_FINGERPRINT_LENGTH)
    .map((line) => line.slice(0, 80)))];
}

function messageText(value: unknown): string {
  if (!isRecord(value)) {
    return "";
  }
  const content = value.content;
  if (typeof content === "string") {
    return content;
  }
  if (!Array.isArray(content)) {
    return "";
  }
  return content
    .filter(isRecord)
    .map((item) => typeof item.text === "string" ? item.text : "")
    .filter(Boolean)
    .join(" ");
}

function normalizeText(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9 ]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function relevantDirectories(context: AgentSessionContext): string[] {
  const workspacePath = resolve(context.workspacePath);
  const currentDirectory = resolve(context.currentDirectory ?? workspacePath);
  if (!pathIsInside(currentDirectory, workspacePath)) {
    return [workspacePath];
  }

  const directories: string[] = [];
  let candidate = currentDirectory;
  while (true) {
    directories.push(candidate);
    if (candidate === workspacePath) {
      return directories;
    }
    const parent = dirname(candidate);
    if (parent === candidate) {
      return directories;
    }
    candidate = parent;
  }
}

function mungeClaudeDirectory(path: string): string {
  return resolve(path).replace(/[/.]/g, "-");
}

async function jsonlFiles(directory: string): Promise<string[]> {
  try {
    const entries = await readdir(directory, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isFile() && entry.name.endsWith(".jsonl"))
      .map((entry) => join(directory, entry.name));
  } catch (error) {
    if (isRecord(error) && error.code === "ENOENT") {
      return [];
    }
    throw error;
  }
}

async function recursiveJsonlFiles(directory: string): Promise<string[]> {
  let entries;
  try {
    entries = await readdir(directory, { withFileTypes: true });
  } catch (error) {
    if (isRecord(error) && error.code === "ENOENT") {
      return [];
    }
    throw error;
  }
  const nested = await Promise.all(entries.map((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      return recursiveJsonlFiles(path);
    }
    return Promise.resolve(
      entry.isFile() && entry.name.endsWith(".jsonl") ? [path] : []
    );
  }));
  return nested.flat();
}

async function readFirstRecord(
  path: string
): Promise<Record<string, unknown> | undefined> {
  let first: Record<string, unknown> | undefined;
  await forEachJsonlRecord(path, (record) => {
    first = record;
    return false;
  });
  return first;
}

async function forEachJsonlRecord(
  path: string,
  visit: (record: Record<string, unknown>) => boolean | void
): Promise<void> {
  const input = createReadStream(path, { encoding: "utf8" });
  const lines = createInterface({ input, crlfDelay: Infinity });
  try {
    for await (const line of lines) {
      const record = parseRecord(line);
      if (record && visit(record) === false) {
        break;
      }
    }
  } finally {
    lines.close();
    input.destroy();
  }
}

function parseRecord(line: string): Record<string, unknown> | undefined {
  try {
    const value: unknown = JSON.parse(line);
    return isRecord(value) ? value : undefined;
  } catch {
    return undefined;
  }
}

function pathIsInside(path: string, workspacePath: string): boolean {
  const root = normalize(workspacePath).replace(/\/+$/, "");
  const candidate = normalize(path).replace(/\/+$/, "");
  return candidate === root || candidate.startsWith(`${root}/`);
}

function isRecord(value: unknown): value is Record<string, any> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
