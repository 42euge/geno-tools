# Vision

geno-tools is the package manager **and governor** for agent skills: one tool
that discovers skills wherever they live, vets them through a trust gate
before they touch the machine, installs them into every coding agent, watches
how they perform, and provides a safe fork/use/promote loop for evolving
them — local-first, zero telemetry, policy-controlled by the user, with all
state under a single `~/.geno/` directory.

The design is documented as user-facing docs on the site:

- [`docs/how-it-works.md`](../docs/how-it-works.md) — the lifecycle end to end
- [`docs/control-surface.md`](../docs/control-surface.md) — how a user controls it (skills / CLI / config, autonomy dial, doctor)
- [`docs/meta-harness.md`](../docs/meta-harness.md) — fork / use / promote
- [`docs/trust-and-audit.md`](../docs/trust-and-audit.md) — the audit gate, boundaries, quarantine, policy
- [`docs/absorption.md`](../docs/absorption.md) — absorbing external skill systems
