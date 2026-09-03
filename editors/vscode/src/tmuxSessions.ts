import type * as vscode from "vscode";

import type { TtTmuxSession, TtWorkspace } from "./model";

const STORAGE_KEY = "genoTools.managedTmuxSessions.v1";

export type TmuxLifecycle = "live" | "stopped" | "external";

export interface ManagedTmuxSession {
  registryHost: string;
  workspaceId: string;
  workspacePath: string;
  sessionName: string;
  paneCurrentPath: string;
  paneCurrentCommand: string;
  launch:
    | { kind: "shell" }
    | { kind: "agent-resume"; command: string };
  managedAt: string;
}

export interface TmuxSessionView extends TtTmuxSession {
  lifecycle: TmuxLifecycle;
  managed?: ManagedTmuxSession;
}

interface PersistedTmuxSessions {
  schema: 1;
  sessions: ManagedTmuxSession[];
}

type Persistence = Pick<vscode.Memento, "get" | "update">;

export class ManagedTmuxSessionStore {
  private sessions: ManagedTmuxSession[];

  constructor(private readonly state?: Persistence) {
    this.sessions = parsePersisted(state?.get<unknown>(STORAGE_KEY));
  }

  records(): ManagedTmuxSession[] {
    return this.sessions.map(copyRecord);
  }

  get(
    registryHost: string,
    sessionName: string
  ): ManagedTmuxSession | undefined {
    const record = this.sessions.find(
      (candidate) =>
        candidate.registryHost === registryHost &&
        candidate.sessionName === sessionName
    );
    return record ? copyRecord(record) : undefined;
  }

  forWorkspace(
    registryHost: string,
    workspace: TtWorkspace
  ): TmuxSessionView[] {
    const managed = this.sessions.filter(
      (record) =>
        record.registryHost === registryHost &&
        record.workspaceId === workspace.id
    );
    const recordsByName = new Map(
      managed.map((record) => [record.sessionName, record])
    );
    const views: TmuxSessionView[] = workspace.state.tmux.sessions.map(
      (session) => {
        const record = recordsByName.get(session.session_name);
        if (!record) {
          return { ...session, lifecycle: "external" };
        }
        recordsByName.delete(session.session_name);
        return {
          ...session,
          lifecycle: "live",
          managed: copyRecord(record)
        };
      }
    );
    for (const record of recordsByName.values()) {
      views.push({
        session_name: record.sessionName,
        pane_current_path: record.paneCurrentPath,
        pane_current_command: record.paneCurrentCommand,
        session_activity: 0,
        lifecycle: "stopped",
        managed: copyRecord(record)
      });
    }
    return views.sort((left, right) =>
      left.session_name.localeCompare(right.session_name)
    );
  }

  async put(record: ManagedTmuxSession): Promise<void> {
    const next = this.sessions.filter(
      (candidate) =>
        candidate.registryHost !== record.registryHost ||
        candidate.sessionName !== record.sessionName
    );
    next.push(copyRecord(record));
    await this.persist(next);
  }

  async remove(registryHost: string, sessionName: string): Promise<void> {
    const next = this.sessions.filter(
      (candidate) =>
        candidate.registryHost !== registryHost ||
        candidate.sessionName !== sessionName
    );
    await this.persist(next);
  }

  private async persist(sessions: ManagedTmuxSession[]): Promise<void> {
    const value: PersistedTmuxSessions = {
      schema: 1,
      sessions: sessions.map(copyRecord)
    };
    await this.state?.update(STORAGE_KEY, value);
    this.sessions = value.sessions;
  }
}

function parsePersisted(value: unknown): ManagedTmuxSession[] {
  if (!isRecord(value) || value.schema !== 1 || !Array.isArray(value.sessions)) {
    return [];
  }
  return value.sessions.flatMap((candidate) => {
    const record = parseRecord(candidate);
    return record ? [record] : [];
  });
}

function parseRecord(value: unknown): ManagedTmuxSession | undefined {
  if (!isRecord(value) || !isRecord(value.launch)) {
    return undefined;
  }
  const fields = [
    "registryHost",
    "workspaceId",
    "workspacePath",
    "sessionName",
    "paneCurrentPath",
    "paneCurrentCommand",
    "managedAt"
  ] as const;
  if (fields.some((field) => typeof value[field] !== "string")) {
    return undefined;
  }
  const launch = value.launch;
  if (
    launch.kind !== "shell" &&
    !(launch.kind === "agent-resume" && typeof launch.command === "string")
  ) {
    return undefined;
  }
  return copyRecord(value as unknown as ManagedTmuxSession);
}

function copyRecord(record: ManagedTmuxSession): ManagedTmuxSession {
  return {
    ...record,
    launch: record.launch.kind === "shell"
      ? { kind: "shell" }
      : { kind: "agent-resume", command: record.launch.command }
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
