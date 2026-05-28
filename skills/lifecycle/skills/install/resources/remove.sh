#!/usr/bin/env bash
# Uninstall a geno-* skillset: deregister skills via npx, remove bin symlinks,
# delete the on-disk root (or only the worktree if --keep-data).
#
# Usage: remove.sh <name> [--keep-data]
#
# Replaces the Python `geno-tools remove` subcommand.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"
. "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

KEEP_DATA=0
NAME=""
for arg in "$@"; do
  case $arg in
    --keep-data) KEEP_DATA=1 ;;
    -h|--help) printf 'usage: remove.sh <name> [--keep-data]\n'; exit 0 ;;
    -*) die "unknown option: $arg" ;;
    *) NAME=$arg ;;
  esac
done

[[ -n $NAME ]] || die "name required"

FULL=$(normalize "$NAME")
ROOT=$(skillset_root "$FULL")
[[ -d $ROOT ]] || die "not installed: $FULL"

uninstall_skills_via_npx "$FULL"
remove_bin_symlinks "$FULL"

if [[ $KEEP_DATA == 1 ]]; then
  for child in "$ROOT"/*; do
    local_name=$(basename "$child")
    case $local_name in
      venvs|.worktrees) continue ;;
    esac
    if [[ -L $child || -f $child ]]; then
      rm -f "$child"
    else
      rm -rf "$child"
    fi
  done
else
  rm -rf "$ROOT"
fi

log "removed $FULL"
