# Shared helpers for geno-tools resource scripts. Source after paths.sh.

set -euo pipefail

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

warn() {
  printf 'warn: %s\n' "$*" >&2
}

log() {
  printf '%s\n' "$*"
}

require_cmd() {
  local cmd=$1
  command -v "$cmd" >/dev/null 2>&1 || die "missing required command: $cmd"
}

# Resolve repo root of the geno-tools checkout that contains this lib.
# Caller-side helper: scripts already compute LIB_DIR; this is for completeness.
geno_tools_repo_root() {
  local lib_dir
  lib_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
  cd "$lib_dir/../../.." && pwd
}

# Walk a skills/ tree and print every directory that contains a SKILL.md.
# Usage: walk_skill_dirs <root>
walk_skill_dirs() {
  local root=$1
  [[ -d $root ]] || return 0
  local child nested
  for child in "$root"/*; do
    [[ -d $child ]] || continue
    if [[ -f "$child/SKILL.md" ]]; then
      printf '%s\n' "$child"
    fi
    nested="$child/skills"
    if [[ -d $nested ]]; then
      walk_skill_dirs "$nested"
    fi
  done
}

# Read the `name:` field from SKILL.md frontmatter; falls back to dir basename.
# Usage: read_skill_name <skill_dir>
read_skill_name() {
  local skill_dir=$1
  local skill_md="$skill_dir/SKILL.md"
  local fallback
  fallback=$(basename "$skill_dir")
  [[ -f $skill_md ]] || { printf '%s\n' "$fallback"; return; }
  if command -v yq >/dev/null 2>&1; then
    local name
    name=$(yq -r '.name // ""' "$skill_md" 2>/dev/null || true)
    if [[ -n $name && $name != "null" ]]; then
      printf '%s\n' "$name"; return
    fi
  fi
  # Fallback: grep frontmatter
  awk '
    /^---$/ { if (++c == 1) next; else exit }
    c == 1 && /^name:/ { sub(/^name:[[:space:]]*/, ""); gsub(/["'\'']/, ""); print; exit }
  ' "$skill_md" 2>/dev/null || printf '%s\n' "$fallback"
}

# Read the top-level `requires:` list from genotools.yaml. Newline-separated.
# Usage: read_requires <worktree_dir>
read_requires() {
  local worktree=$1
  local manifest="$worktree/genotools.yaml"
  [[ -f $manifest ]] || return 0
  if command -v yq >/dev/null 2>&1; then
    yq -r '.requires // [] | .[]' "$manifest" 2>/dev/null || true
  else
    # `in` is reserved in awk; use a different name.
    awk '
      /^requires:/ { inreq=1; next }
      inreq && /^[^ -]/ { inreq=0 }
      inreq && /^[[:space:]]*-[[:space:]]/ {
        sub(/^[[:space:]]*-[[:space:]]*/, "")
        gsub(/["'\'']/, "")
        print
      }
    ' "$manifest"
  fi
}
