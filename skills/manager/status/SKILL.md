---
name: geno-tools-manager-status
description: >-
  Show installed geno-* skillsets with version, commit, and drift vs remote
  main. Use when the user asks what's installed, what version, or whether
  skillsets are out of date.
allowed-tools: "Bash(geno-tools status *)"
license: MIT
metadata:
  author: 42euge
  version: "0.2.0"
---

# manager/status — installed skillsets at a glance

```
geno-tools status
```

No flags — the daily view. Per installed skillset it shows the declared version
(`genotools.yaml`), active `variant@commit`, and a drift state vs its remote
main:

```
geno-tools
── installed · 2 ───────────────────────────────
  geno-loops  0.2.0  main@94eba89  ● in-sync
  geno-notes  0.1.0  main@5f3fb1f  ▼ behind e84fa17
```

States: `● in-sync` · `▼ behind <sha>` · `▲ ahead` · `✗ diverged` · `✎ dirty`
· `· offline`. Anything behind is summarized with a hint to run
`geno-tools update`. Output is colorized on a terminal and plain ASCII when
piped or under `NO_COLOR`.

To browse what you *can* install, use `geno-tools discover`.
