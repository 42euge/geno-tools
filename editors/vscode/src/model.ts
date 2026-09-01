export interface TtHost {
  alias: string;
  hostname: string;
  isDefault: boolean;
}

export interface TtRepo {
  name: string;
  path: string;
  last_accessed: string;
}

export interface TtTmuxSession {
  session_name: string;
  pane_current_path: string;
  pane_current_command: string;
  session_activity: number;
}

export interface TtWorkspaceState {
  tmux: {
    sessions: TtTmuxSession[];
  };
}

export interface TtWorkspace {
  id: string;
  track: string;
  domain: string;
  name: string;
  born: string;
  path: string;
  repos: TtRepo[];
  state: TtWorkspaceState;
}

export interface TtRegistry {
  schema_version: number;
  host: string;
  generated_at: string;
  workspaces: TtWorkspace[];
}

export const TRACK_ORDER = ["crit", "explore", "chore", "side"] as const;

export function parseHosts(output: string): TtHost[] {
  const hosts: TtHost[] = [];
  for (const line of output.split(/\r?\n/)) {
    const match = line.match(/^\s*(\S+)\s+->\s+(.+?)(\s+\(default\))?\s*$/);
    if (!match) {
      continue;
    }
    hosts.push({
      alias: match[1],
      hostname: match[2],
      isDefault: Boolean(match[3])
    });
  }
  return hosts.sort((left, right) => {
    if (left.isDefault !== right.isDefault) {
      return left.isDefault ? -1 : 1;
    }
    return left.alias.localeCompare(right.alias);
  });
}

export function parseRegistry(output: string): TtRegistry {
  let value: unknown;
  try {
    value = JSON.parse(output);
  } catch (error) {
    throw new Error(`TT returned an invalid workspace registry: ${messageOf(error)}`);
  }

  if (!isRecord(value) || value.schema_version !== 1) {
    throw new Error("TT returned an unsupported workspace registry schema.");
  }
  if (typeof value.host !== "string" || typeof value.generated_at !== "string") {
    throw new Error("TT workspace registry metadata is incomplete.");
  }
  if (!Array.isArray(value.workspaces)) {
    throw new Error("TT workspace registry does not contain a workspace list.");
  }

  const workspaces = value.workspaces.map(parseWorkspace);
  return {
    schema_version: 1,
    host: value.host,
    generated_at: value.generated_at,
    workspaces
  };
}

export function workspaceReference(workspace: TtWorkspace): string {
  return workspace.born ? `${workspace.name}.${workspace.born}` : workspace.name;
}

export function sortedTracks(workspaces: TtWorkspace[]): string[] {
  const present = new Set(workspaces.map((workspace) => workspace.track));
  const ranked = TRACK_ORDER.filter((track) => present.delete(track));
  return [...ranked, ...Array.from(present).sort()];
}

export function relativeAge(timestamp: string, now = Date.now()): string {
  const then = Date.parse(timestamp);
  if (!Number.isFinite(then)) {
    return "unknown";
  }
  const days = Math.max(0, Math.floor((now - then) / 86_400_000));
  if (days === 0) {
    return "today";
  }
  if (days === 1) {
    return "1d ago";
  }
  if (days < 30) {
    return `${days}d ago`;
  }
  if (days < 365) {
    return `${Math.floor(days / 30)}mo ago`;
  }
  return `${Math.floor(days / 365)}y ago`;
}

function parseWorkspace(value: unknown, index: number): TtWorkspace {
  if (!isRecord(value)) {
    throw new Error(`TT workspace registry entry ${index} is not an object.`);
  }
  const stringField = (field: string): string => {
    const fieldValue = value[field];
    if (typeof fieldValue !== "string") {
      throw new Error(`TT workspace registry entry ${index} has an invalid ${field}.`);
    }
    return fieldValue;
  };
  if (!Array.isArray(value.repos)) {
    throw new Error(`TT workspace registry entry ${index} has an invalid repos list.`);
  }
  return {
    id: stringField("id"),
    track: stringField("track"),
    domain: stringField("domain"),
    name: stringField("name"),
    born: stringField("born"),
    path: stringField("path"),
    repos: value.repos.map((repo, repoIndex) => parseRepo(repo, index, repoIndex)),
    state: parseWorkspaceState(value.state, index)
  };
}

function parseWorkspaceState(value: unknown, workspaceIndex: number): TtWorkspaceState {
  if (value === undefined) {
    return { tmux: { sessions: [] } };
  }
  if (!isRecord(value) || !isRecord(value.tmux) || !Array.isArray(value.tmux.sessions)) {
    throw new Error(
      `TT workspace registry entry ${workspaceIndex} has invalid state.`
    );
  }
  const sessions = value.tmux.sessions.map((session, sessionIndex) => {
    if (
      !isRecord(session) ||
      typeof session.session_name !== "string" ||
      typeof session.pane_current_path !== "string" ||
      typeof session.pane_current_command !== "string" ||
      typeof session.session_activity !== "number"
    ) {
      throw new Error(
        `TT workspace registry entry ${workspaceIndex} has an invalid tmux session at index ${sessionIndex}.`
      );
    }
    return {
      session_name: session.session_name,
      pane_current_path: session.pane_current_path,
      pane_current_command: session.pane_current_command,
      session_activity: session.session_activity
    };
  });
  return { tmux: { sessions } };
}

function parseRepo(value: unknown, workspaceIndex: number, repoIndex: number): TtRepo {
  if (
    !isRecord(value) ||
    typeof value.name !== "string" ||
    typeof value.path !== "string" ||
    typeof value.last_accessed !== "string"
  ) {
    throw new Error(
      `TT workspace registry entry ${workspaceIndex} has an invalid repository at index ${repoIndex}.`
    );
  }
  return {
    name: value.name,
    path: value.path,
    last_accessed: value.last_accessed
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
