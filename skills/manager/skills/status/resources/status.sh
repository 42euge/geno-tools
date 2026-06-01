#!/usr/bin/env bash
# Verify the on-disk geno-tools install: report installed skillsets, the
# active variant per skillset, broken/missing components, and dangling
# bin symlinks.
#
# Usage: status.sh

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"

if [[ ! -d $GENO_ROOT ]]; then
  printf 'GENO_ROOT not present: %s\n' "$GENO_ROOT"
  printf 'no skillsets installed\n'
  exit 0
fi

ok=0
bad=0
warn=0

printf 'GENO_ROOT: %s\n' "$GENO_ROOT"
printf 'GENO_DIR:  %s\n' "$GENO_DIR"
printf '\n'

for d in "$GENO_ROOT"/*; do
  [[ -d $d ]] || continue
  full=$(basename "$d")
  [[ $full == geno-* ]] || continue
  printf '%-24s ' "$full"

  problems=()
  [[ -d "$d/.git" ]] || problems+=("missing .git")
  [[ -d "$d/main" ]] || problems+=("missing main worktree")
  if [[ -L "$d/active" ]]; then
    target=$(readlink "$d/active")
    [[ -d "$d/$target" ]] || problems+=("active -> $target (broken)")
  else
    problems+=("missing active symlink")
  fi

  if [[ ${#problems[@]} -eq 0 ]]; then
    target=$(readlink "$d/active")
    printf 'OK (active: %s)\n' "$target"
    ok=$((ok+1))
  else
    printf 'PROBLEMS\n'
    for p in "${problems[@]}"; do
      printf '  - %s\n' "$p"
    done
    bad=$((bad+1))
  fi
done

# Dangling bin symlinks.
if [[ -d $SYSTEM_BIN ]]; then
  for entry in "$SYSTEM_BIN"/*; do
    [[ -L $entry ]] || continue
    target=$(readlink -f "$entry" 2>/dev/null || true)
    if [[ $target == "$GENO_ROOT"/* && ! -e $target ]]; then
      printf 'dangling bin symlink: %s -> %s (missing)\n' "$entry" "$target"
      warn=$((warn+1))
    fi
  done
fi

printf '\nsummary: %d ok, %d with problems, %d warnings\n' "$ok" "$bad" "$warn"
[[ $bad -gt 0 ]] && exit 1
exit 0
