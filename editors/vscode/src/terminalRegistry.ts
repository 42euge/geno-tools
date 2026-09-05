const STORAGE_KEY = "genoTools.terminalRegistry.v1";
const ATTACHED_TERMINAL_NAME = /^TT: ([^/]+)\/([A-Za-z0-9][A-Za-z0-9_-]*)$/;

const GENERIC_TERMINAL_NAMES = new Set([
  "bash",
  "claude",
  "clauded",
  "cmd",
  "codex",
  "codexd",
  "command prompt",
  "csh",
  "fish",
  "gemini",
  "git bash",
  "node",
  "npm",
  "npx",
  "nu",
  "opencode",
  "powershell",
  "pwsh",
  "python",
  "python3",
  "sh",
  "wsl",
  "xonsh",
  "zsh"
]);

export type TerminalNamingProvenance = "default" | "manual" | "ai";
export type TerminalTtRole = "attached" | "origin";

export interface TerminalTtState {
  role: TerminalTtRole;
  hostAlias: string;
  sessionName: string;
  agent?: "claude" | "codex";
  agentSessionId?: string;
}

export interface TerminalState {
  initialName: string;
  currentName: string;
  naming: TerminalNamingProvenance;
  tt?: TerminalTtState;
}

export interface RegistryTerminal {
  name: string;
  creationOptions?: Readonly<{ name?: string }>;
  processId?: PromiseLike<number | undefined>;
}

export interface TerminalRegistryStorage {
  get<T>(key: string, fallback: T): T;
  update(key: string, value: unknown): PromiseLike<void>;
}

interface MutableTerminalState extends TerminalState {
  suppressTtInference?: boolean;
}

interface PersistedTerminalState {
  processId: number;
  initialName: string;
  currentName: string;
  naming: TerminalNamingProvenance;
  tt: TerminalTtState | null;
}

export class TerminalRegistry {
  private readonly states = new Map<RegistryTerminal, MutableTerminalState>();
  private readonly persisted = new Map<number, PersistedTerminalState>();

  constructor(private readonly storage?: TerminalRegistryStorage) {}

  observe(terminal: RegistryTerminal): TerminalState {
    let state = this.states.get(terminal);
    if (!state) {
      state = initialState(terminal);
      this.states.set(terminal, state);
    } else if (state.currentName !== terminal.name) {
      state.currentName = terminal.name;
      state.naming = "manual";
      void this.persist(terminal, state);
    }
    return publicState(state);
  }

  stateFor(terminal: RegistryTerminal): TerminalState {
    return this.observe(terminal);
  }

  canBulkName(terminal: RegistryTerminal): boolean {
    const state = this.observe(terminal);
    return state.naming === "default" && state.tt === undefined;
  }

  async recordAiName(
    terminal: RegistryTerminal,
    name: string
  ): Promise<void> {
    this.observe(terminal);
    const state = this.states.get(terminal);
    if (!state) {
      return;
    }
    state.currentName = name;
    state.naming = "ai";
    await this.persist(terminal, state);
  }

  async recordTtLink(
    terminal: RegistryTerminal,
    tt: TerminalTtState
  ): Promise<void> {
    this.observe(terminal);
    const state = this.states.get(terminal);
    if (!state) {
      return;
    }
    state.tt = { ...tt };
    state.suppressTtInference = false;
    await this.persist(terminal, state);
  }

  linkFor(terminal: RegistryTerminal): TerminalTtState | undefined {
    return this.observe(terminal).tt;
  }

  hasAttachedTerminal(hostAlias: string, sessionName: string): boolean {
    for (const terminal of this.states.keys()) {
      const link = this.linkFor(terminal);
      if (
        link?.role === "attached" &&
        link.hostAlias === hostAlias &&
        link.sessionName === sessionName
      ) {
        return true;
      }
    }
    return false;
  }

  attachedTerminal(
    hostAlias: string,
    sessionName: string
  ): RegistryTerminal | undefined {
    for (const terminal of this.states.keys()) {
      const link = this.linkFor(terminal);
      if (
        link?.role === "attached" &&
        link.hostAlias === hostAlias &&
        link.sessionName === sessionName
      ) {
        return terminal;
      }
    }
    return undefined;
  }

  async restore(terminals: readonly RegistryTerminal[]): Promise<void> {
    const records = this.storage?.get<PersistedTerminalState[]>(STORAGE_KEY, []) ?? [];
    this.persisted.clear();
    for (const record of records) {
      if (validPersistedState(record)) {
        this.persisted.set(record.processId, record);
      }
    }

    const liveProcessIds = new Set<number>();
    await Promise.all(terminals.map(async (terminal) => {
      const processId = await terminal.processId;
      const saved = processId === undefined
        ? undefined
        : this.persisted.get(processId);
      const state = initialState(terminal);
      if (saved) {
        state.initialName = saved.initialName;
        state.currentName = terminal.name;
        state.naming = saved.currentName === terminal.name
          ? saved.naming
          : "manual";
        state.tt = saved.tt ?? undefined;
        state.suppressTtInference = saved.tt === null;
        liveProcessIds.add(saved.processId);
      }
      this.states.set(terminal, state);
    }));

    for (const processId of this.persisted.keys()) {
      if (!liveProcessIds.has(processId)) {
        this.persisted.delete(processId);
      }
    }
    await this.flush();
  }

  async forget(terminal: RegistryTerminal): Promise<void> {
    this.states.delete(terminal);
    const processId = await terminal.processId;
    if (processId !== undefined) {
      this.persisted.delete(processId);
      await this.flush();
    }
  }

  async unlinkSession(hostAlias: string, sessionName: string): Promise<void> {
    const writes: Promise<void>[] = [];
    for (const [terminal, state] of this.states) {
      if (
        state.tt?.hostAlias === hostAlias &&
        state.tt.sessionName === sessionName
      ) {
        state.tt = undefined;
        state.suppressTtInference = true;
        writes.push(this.persist(terminal, state));
      }
    }
    await Promise.all(writes);
  }

  dispose(): void {
    this.states.clear();
  }

  private async persist(
    terminal: RegistryTerminal,
    state: MutableTerminalState
  ): Promise<void> {
    const processId = await terminal.processId;
    if (processId === undefined) {
      return;
    }
    this.persisted.set(processId, {
      processId,
      initialName: state.initialName,
      currentName: state.currentName,
      naming: state.naming,
      tt: state.tt ? { ...state.tt } : null
    });
    await this.flush();
  }

  private async flush(): Promise<void> {
    await this.storage?.update(STORAGE_KEY, [...this.persisted.values()]);
  }
}

function initialState(terminal: RegistryTerminal): MutableTerminalState {
  const inferredTt = inferredAttachedLink(terminal.name);
  const naming = isGenericTerminalName(terminal.name)
    ? "default"
    : "manual";
  return {
    initialName: terminal.name,
    currentName: terminal.name,
    naming,
    tt: inferredTt
  };
}

function inferredAttachedLink(name: string): TerminalTtState | undefined {
  const match = name.match(ATTACHED_TERMINAL_NAME);
  return match
    ? {
        role: "attached",
        hostAlias: match[1],
        sessionName: match[2]
      }
    : undefined;
}

function isGenericTerminalName(name: string): boolean {
  return GENERIC_TERMINAL_NAMES.has(normalizeName(name));
}

function normalizeName(value: string): string {
  return value.trim().replace(/\s+/gu, " ").toLowerCase();
}

function publicState(state: MutableTerminalState): TerminalState {
  return {
    initialName: state.initialName,
    currentName: state.currentName,
    naming: state.naming,
    ...(state.tt ? { tt: { ...state.tt } } : {})
  };
}

function validPersistedState(value: unknown): value is PersistedTerminalState {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Partial<PersistedTerminalState>;
  return typeof record.processId === "number" &&
    typeof record.initialName === "string" &&
    typeof record.currentName === "string" &&
    (record.naming === "default" ||
      record.naming === "manual" ||
      record.naming === "ai") &&
    (record.tt === null || record.tt === undefined ||
      (typeof record.tt === "object" &&
        typeof record.tt.hostAlias === "string" &&
        typeof record.tt.sessionName === "string" &&
        (record.tt.role === "origin" || record.tt.role === "attached")));
}
