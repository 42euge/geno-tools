#!/usr/bin/env bash
# List installed skillsets. With --available, list registry + discovery.
#
# Usage: ls.sh [--available]
#
# Replaces the Python `geno-tools ls` subcommand.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"

AVAILABLE=0
case ${1:-} in
  --available) AVAILABLE=1 ;;
  -h|--help) printf 'usage: ls.sh [--available]\n'; exit 0 ;;
  '') ;;
  *) die "unknown option: $1" ;;
esac

if [[ $AVAILABLE == 1 ]]; then
  REGISTRY=$(registry_available)
  printf '%s\n' "$REGISTRY" | awk -F'\t' '{ printf "  %-24s %s\n", $1, $2 }'
  REG_NAMES=$(printf '%s\n' "$REGISTRY" | awk -F'\t' '{ print $1 }' | LC_ALL=C sort -u)
  discovery_candidates_by_name | LC_ALL=C sort | while IFS=$'\t' read -r name url; do
    grep -qxF "$name" <<<"$REG_NAMES" && continue
    printf '  %-24s %s  (discovered)\n' "$name" "$url"
  done
  exit 0
fi

if [[ ! -d $GENO_ROOT ]]; then
  printf 'no skillsets installed\n'
  exit 0
fi

found=0
for p in "$GENO_ROOT"/*; do
  [[ -d $p ]] || continue
  full=$(basename "$p")
  [[ $full == geno-* ]] || continue
  [[ $full == geno-bootstrap ]] && continue
  active="$p/active"
  if [[ -L $active ]]; then
    target=$(readlink "$active")
    target=$(basename "$target")
  else
    target="?"
  fi
  printf '  %-24s active: %s\n' "$full" "$target"
  found=1
done

[[ $found == 0 ]] && printf 'no skillsets installed\n'
