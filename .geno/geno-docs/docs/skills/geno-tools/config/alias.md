---
title: geno-alias
description: Create, remove, and list custom slash-command aliases for geno ecosystem skills
---

# geno-alias

`/geno-alias "[add|remove|list] [source-skill] [alias-name]"`

> Create, remove, and list custom slash-command aliases for geno ecosystem skills

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

Create custom slash-command aliases for any installed geno ecosystem skill. Aliases are tracked in `~/.geno/.genorc` and registered with all agents via `npx skills`.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Argument parsing

Parse `$ARGUMENTS` into one of three operations:

| Input | Operation |
|-------|-----------|
| `list` or empty | List all aliases |
| `remove <alias>` | Remove an alias |
| `add <source> <alias>` | Create an alias |
| `<source> <alias>` (two args, first is not `add`/`remove`/`list`) | Create an alias (shorthand) |

Strip leading `/` from both source and alias names.

## Add operation

### Step 1 — Validate source skill exists

```bash
SOURCE="<source>"
if [ -f "$HOME/.agents/skills/$SOURCE/SKILL.md" ]; then
  SRC_PATH="$HOME/.agents/skills/$SOURCE/SKILL.md"
elif [ -f "$HOME/.claude/skills/$SOURCE/SKILL.md" ]; then
  SRC_PATH="$HOME/.claude/skills/$SOURCE/SKILL.md"
else
  echo "Source skill '$SOURCE' not found."
  echo "Available skills:"
  ls ~/.agents/skills/ 2>/dev/null; ls ~/.claude/skills/ 2>/dev/null
  exit 1
fi
```

### Step 2 — Validate alias doesn't shadow a non-alias skill

Check `~/.geno/.genorc` — if the alias name already exists there, it's a previously created alias and can be overwritten. If it exists in `~/.agents/skills/` or `~/.claude/skills/` but is NOT in `.genorc`, warn that creating this alias would shadow an existing skill and ask the user to confirm.

### Step 3 — Create the alias SKILL.md

Read the source SKILL.md. Create a copy with the `name:` field **removed** from the frontmatter (so `npx skills` derives the name from the directory). All other frontmatter and body content are preserved unchanged.

```bash
mkdir -p "$HOME/.geno/aliases/ALIAS_NAME"
```

Use `python3` to strip the `name:` field:

```bash
python3 -c "
import re, sys
content = open(sys.argv[1]).read()
parts = content.split('---', 2)
if len(parts) >= 3:
    fm = re.sub(r'^name:.*\n', '', parts[1], flags=re.MULTILINE)
    result = '---' + fm + '---' + parts[2]
else:
    result = content
open(sys.argv[2], 'w').write(result)
" "$SRC_PATH" "$HOME/.geno/aliases/ALIAS_NAME/SKILL.md"
```

### Step 4 — Register with npx skills

```bash
npx --yes skills add "$HOME/.geno/aliases/ALIAS_NAME" --agent "*" --global --yes
```

### Step 5 — Record in .genorc

```bash
python3 -c "
import sys
from pathlib import Path

rc = Path.home() / '.geno' / '.genorc'
# Read existing content or start fresh
lines = rc.read_text().splitlines() if rc.exists() else []

# Ensure 'aliases:' header exists
if not any(l.strip() == 'aliases:' for l in lines):
    lines.append('aliases:')

# Remove any existing entry for this alias
alias, source = sys.argv[1], sys.argv[2]
lines = [l for l in lines if not l.strip().startswith(alias + ':')]

# Find the aliases: line and insert after it
idx = next(i for i, l in enumerate(lines) if l.strip() == 'aliases:')
lines.insert(idx + 1, f'  {alias}: {source}')

rc.write_text('\n'.join(lines) + '\n')
" "ALIAS_NAME" "SOURCE"
```

### Step 6 — Report

Tell the user the alias was created. Note that it will take effect in the **next session** (since Claude Code loads skills at session start).

## Remove operation

### Step 1 — Look up alias in .genorc

```bash
python3 -c "
import sys, re
from pathlib import Path
rc = Path.home() / '.geno' / '.genorc'
if not rc.exists():
    print('No aliases configured.'); sys.exit(1)
content = rc.read_text()
alias = sys.argv[1]
m = re.search(rf'^\s+{re.escape(alias)}:\s+(.+)$', content, re.MULTILINE)
if not m:
    print(f\"'{alias}' is not a registered alias.\"); sys.exit(1)
print(m.group(1).strip())
" "ALIAS_NAME"
```

If not found, report that the alias doesn't exist and show available aliases.

### Step 2 — Unregister

```bash
npx --yes skills remove "ALIAS_NAME" --agent "*" --global --yes
```

### Step 3 — Clean up files

```bash
rm -rf "$HOME/.geno/aliases/ALIAS_NAME"
```

### Step 4 — Remove from .genorc

```bash
python3 -c "
import re, sys
from pathlib import Path
rc = Path.home() / '.geno' / '.genorc'
content = rc.read_text()
alias = sys.argv[1]
content = re.sub(rf'^\s+{re.escape(alias)}:.*\n', '', content, flags=re.MULTILINE)
# Remove 'aliases:' header if no entries remain
if re.search(r'^aliases:\s*$', content, re.MULTILINE) and not re.search(r'^  \w', content, re.MULTILINE):
    content = re.sub(r'^aliases:\s*\n', '', content, flags=re.MULTILINE)
content = content.strip()
if content:
    rc.write_text(content + '\n')
else:
    rc.unlink()
" "ALIAS_NAME"
```

### Step 5 — Report

Tell the user the alias was removed and will disappear next session.

## List operation

```bash
python3 -c "
from pathlib import Path
import re
rc = Path.home() / '.geno' / '.genorc'
if not rc.exists():
    print('No aliases configured.'); raise SystemExit
content = rc.read_text()
entries = re.findall(r'^\s+(\S+):\s+(\S+)', content, re.MULTILINE)
if not entries:
    print('No aliases configured.'); raise SystemExit
print(f'{len(entries)} alias(es):\n')
for alias, source in sorted(entries):
    installed = 'installed' if (Path.home() / '.claude/skills' / alias).exists() else 'not installed'
    print(f'  /{alias}  ->  /{source}  ({installed})')
"
```

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-alias \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = alias created, removed, or listed without errors
- `failure` = source skill not found, npx registration failed, or .genorc write error
- `abandoned` = user stopped early

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-tools](index.md)
