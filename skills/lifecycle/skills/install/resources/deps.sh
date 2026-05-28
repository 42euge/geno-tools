#!/usr/bin/env bash
# Print the recursive dependency tree for an installed skillset.
#
# Usage: deps.sh <name>
#
# Replaces the Python `geno-tools deps` subcommand.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"

[[ $# -ge 1 ]] || die "usage: deps.sh <name>"

FULL=$(normalize "$1")
[[ -d $(skillset_root "$FULL") ]] || die "not installed: $FULL"

declare -A SEEN=()

print_tree() {
  local full=$1
  local indent=$2
  local prefix=""
  local i=0
  while [[ $i -lt $indent ]]; do prefix+="  "; i=$((i+1)); done

  local marker=""
  [[ -d $(skillset_root "$full") ]] || marker=" (missing)"
  printf '%s%s%s\n' "$prefix" "$full" "$marker"

  if [[ -n ${SEEN[$full]+x} ]]; then
    local worktree
    worktree=$(skillset_worktree "$full" main)
    local req
    req=$(read_requires "$worktree" || true)
    [[ -n $req ]] && printf '%s  (circular, skipped)\n' "$prefix"
    return
  fi
  SEEN[$full]=1

  [[ -d $(skillset_root "$full") ]] || return

  local worktree
  worktree=$(skillset_worktree "$full" main)
  local req
  req=$(read_requires "$worktree" || true)
  [[ -n $req ]] || return
  while IFS= read -r dep; do
    [[ -n $dep ]] || continue
    print_tree "$(normalize "$dep")" $((indent+1))
  done <<<"$req"
}

print_tree "$FULL" 0
