#!/usr/bin/env bash
# Install a geno-* skillset: clone, create venv (if pyproject), symlink bins,
# register skills via `npx skills add`. Recursively installs `requires:`.
#
# Usage: install.sh <name|url|path>
#
# Replaces the Python `geno-tools install` subcommand.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"
. "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

usage() {
  cat <<EOF
usage: install.sh <name|url|path>

  <name|url|path>  registered name (e.g. media), local path, or git URL
EOF
}

if [[ $# -lt 1 ]]; then
  usage; exit 2
fi

ARG=$1
ensure_config_dir

declare -A INSTALLING=()

install_one() {
  local arg=$1
  local source name full
  {
    read -r source
    read -r name
  } < <(resolve_source "$arg")
  if [[ -z $name ]]; then
    name=$(peek_repo_name "$source")
  fi
  full=$(normalize "$name")

  local root
  root=$(skillset_root "$full")
  if [[ -d $root ]]; then
    log "already installed: $full"
    return 0
  fi
  if [[ -n ${INSTALLING[$full]+x} ]]; then
    warn "circular dependency detected: $full; skipping"
    return 1
  fi
  INSTALLING[$full]=1

  log "installing $full from $source"
  mkdir -p "$root"
  local rc=0
  (
    set -e
    clone_and_worktree "$source" "$full"
    install_requires "$full"
    local scripts_str scripts_arr=()
    scripts_str=$(create_venv_if_needed "$full" || true)
    if [[ -n $scripts_str ]]; then
      while IFS= read -r s; do [[ -n $s ]] && scripts_arr+=("$s"); done <<<"$scripts_str"
    fi
    materialize_bin_symlinks "$full" "${scripts_arr[@]}"
    local active
    active=$(skillset_active "$full")
    [[ -L $active ]] || ln -s main "$active"
    install_skills_via_npx "$full"
  ) || rc=$?
  if [[ $rc -ne 0 ]]; then
    rm -rf "$root"
    return $rc
  fi

  log "installed $full"
}

install_requires() {
  local full=$1
  local worktree
  worktree=$(skillset_worktree "$full" main)
  local requires
  requires=$(read_requires "$worktree" || true)
  [[ -n $requires ]] || return 0
  local -a deps=()
  while IFS= read -r d; do [[ -n $d ]] && deps+=("$d"); done <<<"$requires"
  printf '  %s requires: %s\n' "$full" "${deps[*]}"
  local dep dep_full
  for dep in "${deps[@]}"; do
    dep_full=$(normalize "$dep")
    [[ -d $(skillset_root "$dep_full") ]] && continue
    printf '  installing dependency: %s\n' "$dep"
    install_one "$dep" || die "failed to install dependency $dep required by $full"
  done
}

install_one "$ARG"
