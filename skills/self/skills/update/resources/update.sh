#!/usr/bin/env bash
# Pull the latest main worktree for one or all installed skillsets.
# Re-installs the venv if pyproject.toml changed and re-registers skills via npx.
#
# Usage: update.sh [name]
#
# Replaces the Python `geno-tools update` subcommand.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"
# reach into install/_lib.sh for venv + npx helpers
INSTALL_LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../manager/skills/install/resources" && pwd)/_lib.sh"
. "$INSTALL_LIB"

declare -a UPDATED=() UP_TO_DATE=() SKIPPED=() ERRORS=()

# Append "$full|$old|$new|$detail" to the named array.
record() {
  local arr=$1 full=$2 old=${3:-} new=${4:-} detail=${5:-}
  eval "$arr+=(\"\$full|\$old|\$new|\$detail\")"
}

update_one() {
  local full=$1
  local bare worktree
  bare=$(skillset_git "$full")
  worktree=$(skillset_worktree "$full" main)

  if [[ ! -d $worktree ]]; then
    record ERRORS "$full" "" "" "main worktree missing"; return
  fi
  if [[ -L $worktree ]]; then
    record SKIPPED "$full" "" "" "dev mode (local symlink)"; return
  fi

  local status
  if ! status=$(git -C "$worktree" status --porcelain 2>/dev/null); then
    record ERRORS "$full" "" "" "git status failed"; return
  fi
  if [[ -n $status ]]; then
    record SKIPPED "$full" "" "" "dirty worktree"; return
  fi

  local default_branch current_branch
  default_branch=$(git -C "$bare" symbolic-ref --short HEAD 2>/dev/null || printf 'main')
  if ! current_branch=$(git -C "$worktree" branch --show-current 2>/dev/null); then
    record ERRORS "$full" "" "" "cannot detect branch"; return
  fi
  if [[ $current_branch != $default_branch ]]; then
    record SKIPPED "$full" "" "" "on branch '$current_branch', not '$default_branch'"; return
  fi

  local old_rev new_rev
  old_rev=$(git -C "$worktree" rev-parse HEAD 2>/dev/null || printf '')

  printf '  fetching %s...\n' "$full"
  if ! git -C "$bare" fetch --quiet origin 2>/dev/null; then
    record ERRORS "$full" "" "" "git fetch failed"; return
  fi
  if ! git -C "$worktree" pull --ff-only --quiet origin "$default_branch" 2>/dev/null; then
    record ERRORS "$full" "" "" "git pull --ff-only failed (diverged?)"; return
  fi

  new_rev=$(git -C "$worktree" rev-parse HEAD 2>/dev/null || printf '')

  if [[ $old_rev == $new_rev ]]; then
    record UP_TO_DATE "$full" "${old_rev:0:8}" "" ""; return
  fi

  maybe_reinstall_venv "$full" "$old_rev" "$new_rev"
  install_skills_via_npx "$full"

  record UPDATED "$full" "${old_rev:0:8}" "${new_rev:0:8}" ""
}

maybe_reinstall_venv() {
  local full=$1 old=$2 new=$3
  local worktree
  worktree=$(skillset_worktree "$full" main)
  [[ -f "$worktree/pyproject.toml" ]] || return 0
  local changed
  changed=$(git -C "$worktree" diff --name-only "$old" "$new" 2>/dev/null || printf 'pyproject.toml')
  [[ $changed == *pyproject.toml* ]] || return 0
  local venv_dir
  venv_dir="$(skillset_venvs "$full")/default"
  if [[ ! -d $venv_dir ]]; then
    create_venv_if_needed "$full" >/dev/null
    return
  fi
  printf '  pyproject.toml changed; reinstalling venv...\n'
  "$venv_dir/bin/pip" install --quiet -e "$worktree" || warn "venv reinstall failed for $full"
}

NAME=${1:-}

if [[ -n $NAME ]]; then
  FULL=$(normalize "$NAME")
  [[ -d $(skillset_root "$FULL") ]] || die "not installed: $FULL"
  update_one "$FULL"
else
  [[ -d $GENO_ROOT ]] || { printf 'no skillsets installed\n'; exit 0; }
  for p in "$GENO_ROOT"/*; do
    [[ -d $p ]] || continue
    full=$(basename "$p")
    [[ $full == geno-* ]] || continue
    [[ $full == geno-bootstrap ]] && continue
    update_one "$full"
  done
fi

print_section() {
  local title=$1; shift
  local -a entries=("$@")
  [[ ${#entries[@]} -eq 0 ]] && return
  printf '%s (%d):\n' "$title" "${#entries[@]}"
  local e full old new detail
  for e in "${entries[@]}"; do
    IFS='|' read -r full old new detail <<<"$e"
    if [[ $title == "updated" ]]; then
      printf '  %-24s %s -> %s\n' "$full" "$old" "$new"
    elif [[ $title == "already up-to-date" ]]; then
      printf '  %s\n' "$full"
    else
      printf '  %-24s %s\n' "$full" "$detail"
    fi
  done
}

printf '\n'
print_section "updated"            "${UPDATED[@]+"${UPDATED[@]}"}"
print_section "already up-to-date" "${UP_TO_DATE[@]+"${UP_TO_DATE[@]}"}"
print_section "skipped"            "${SKIPPED[@]+"${SKIPPED[@]}"}"
print_section "errors"             "${ERRORS[@]+"${ERRORS[@]}"}"

[[ ${#ERRORS[@]} -eq 0 ]] || exit 1
