# Tenets

Architectural principles that guide all development decisions in geno-tools. When tenets conflict, earlier entries take precedence.

1. **Agent-agnostic** — geno-tools is a package manager that targets all coding agents through platform-specific adapters. It is not a CLI for one agent. Every feature must work across Claude Code, Codex, Antigravity CLI, Cursor, and OpenCode.

2. **Skill-system absorption** — external skill formats (Vercel Labs Skills, Superpowers, Ralphy Loop) are first-class import sources, not just inspiration. The plugin structure normalizes them into the `SKILL.md` + `genotools.yaml` contract so skills from any origin are managed the same way.

3. **Auditing as infrastructure** — compliance scanning gates every onboarding path: public registry, enterprise namespace, and direct URL. It is not an optional add-on. New ingestion paths must integrate with the audit checklist before shipping.

4. **Lifecycle-driven** — every skill follows discover, absorb, evaluate, govern, evolve. The tooling enforces it. Features that bypass or shortcut the lifecycle need explicit justification.

5. **Local-first, zero telemetry** — all execution is local. No call-home, no usage tracking, no analytics. Private knowledge stays inside the boundary of the machine or organization that owns it.

6. **Isolated by default** — per-skillset venvs, git worktrees for variants, nothing leaks between skillsets. A failure or compromise in one skillset must not affect another.

7. **Exact removal** — uninstall replays install in reverse. No orphaned files, no stale symlinks, no leftover agent registrations. `geno-tools remove` must leave the system as if the skill was never installed.
