# Helpers shared by install/remove/update — all the git/venv/npx plumbing.
# Source this AFTER load.sh.

# Resolve a name|url|path argument to (source_url, peeked_name).
# Prints two lines: SOURCE on line 1, NAME on line 2 (NAME may be empty).
resolve_source() {
  local arg=$1
  local url
  url=$(registry_resolve "$arg")
  if [[ -n $url ]]; then
    printf '%s\n%s\n' "$url" "$arg"
    return 0
  fi
  if [[ -d ${arg/#\~/$HOME} ]]; then
    local abs
    abs=$(cd "${arg/#\~/$HOME}" && pwd)
    printf '%s\n\n' "$abs"
    return 0
  fi
  case $arg in
    http://*|https://*|git@*|*.git)
      printf '%s\n\n' "$arg"
      return 0
      ;;
  esac
  # discovery
  local match
  match=$(discovery_candidates_by_name | awk -F'\t' -v n="$arg" '$1 == n { print $2; exit }')
  if [[ -n $match ]]; then
    printf '%s\n%s\n' "$match" "$arg"
    return 0
  fi
  die "unknown skillset: $arg (not in registry, discovery, path, or git URL)"
}

# Detect a usable name from a source path or URL when registry didn't tell us.
peek_repo_name() {
  local source=$1
  if [[ -d $source ]]; then
    if [[ -f "$source/pyproject.toml" ]] && command -v yq >/dev/null 2>&1; then
      local n
      n=$(yq -p toml -r '.project.name // ""' "$source/pyproject.toml" 2>/dev/null || true)
      [[ -n $n && $n != "null" ]] && { printf '%s\n' "$n"; return; }
    fi
    basename "$source"
    return
  fi
  # remote: shallow clone to staging, peek pyproject, fall back to slug
  local staging="$GENO_ROOT/.staging"
  rm -rf "$staging"
  mkdir -p "$staging"
  if git clone --depth 1 --quiet "$source" "$staging/repo" 2>/dev/null; then
    if [[ -f "$staging/repo/pyproject.toml" ]] && command -v yq >/dev/null 2>&1; then
      local n
      n=$(yq -p toml -r '.project.name // ""' "$staging/repo/pyproject.toml" 2>/dev/null || true)
      if [[ -n $n && $n != "null" ]]; then
        rm -rf "$staging"
        printf '%s\n' "$n"
        return
      fi
    fi
  fi
  rm -rf "$staging"
  local slug=${source%/}
  slug=${slug##*/}
  slug=${slug%.git}
  printf '%s\n' "$slug"
}

# Clone bare + add main worktree.
clone_and_worktree() {
  local source=$1
  local full=$2
  local bare worktree branch
  bare=$(skillset_git "$full")
  worktree=$(skillset_worktree "$full" main)

  git clone --bare --quiet "$source" "$bare"
  branch=$(git -C "$bare" symbolic-ref --short HEAD 2>/dev/null || printf 'main')
  git -C "$bare" worktree add "$worktree" "$branch"
}

# Create venv at venvs/default if pyproject.toml present. Echos space-separated
# script names (project.scripts keys) to stdout, empty if no venv created.
create_venv_if_needed() {
  local full=$1
  local worktree pyproject
  worktree=$(skillset_worktree "$full" main)
  pyproject="$worktree/pyproject.toml"
  [[ -f $pyproject ]] || return 0

  command -v yq >/dev/null 2>&1 || { warn "yq missing; skipping venv for $full"; return 0; }

  local has_project deps_json scripts_keys
  has_project=$(yq -p toml -r '.project | type' "$pyproject" 2>/dev/null || printf '')
  [[ $has_project == "!!map" || $has_project == "object" ]] || return 0

  deps_json=$(yq -p toml -o=json -I=0 '.project.dependencies // []' "$pyproject" 2>/dev/null || printf '[]')
  scripts_keys=$(yq -p toml -r '(.project.scripts // {}) | keys | .[]' "$pyproject" 2>/dev/null || true)

  local venv_dir
  venv_dir="$(skillset_venvs "$full")/default"
  mkdir -p "$(dirname "$venv_dir")"
  printf '  creating venv: %s\n' "$venv_dir"
  python3 -m venv "$venv_dir"
  local pip="$venv_dir/bin/pip"
  "$pip" install --quiet --upgrade pip

  local deps_count
  deps_count=$(printf '%s' "$deps_json" | jq 'length')
  if [[ $deps_count -gt 0 ]]; then
    local -a deps_arr=()
    while IFS= read -r d; do deps_arr+=("$d"); done < <(printf '%s' "$deps_json" | jq -r '.[]')
    printf '  installing deps: %s\n' "${deps_arr[*]}"
    "$pip" install --quiet "${deps_arr[@]}"
  fi
  printf '  installing package (editable)\n'
  "$pip" install --quiet -e "$worktree"

  printf '%s\n' $scripts_keys
}

# Create symlinks in $SYSTEM_BIN for each script name.
materialize_bin_symlinks() {
  local full=$1; shift
  local -a scripts=("$@")
  [[ ${#scripts[@]} -gt 0 ]] || return 0
  mkdir -p "$SYSTEM_BIN"
  local venv_bin
  venv_bin="$(skillset_venvs "$full")/default/bin"
  local name src dst
  for name in "${scripts[@]}"; do
    src="$venv_bin/$name"
    dst="$SYSTEM_BIN/$name"
    if [[ ! -e $src ]]; then
      warn "expected venv binary not found: $src"
      continue
    fi
    if [[ -e $dst || -L $dst ]]; then
      if [[ -L $dst && $(readlink "$dst") == "$src" ]]; then
        continue
      fi
      warn "$dst already exists; skipping"
      continue
    fi
    ln -s "$src" "$dst"
    printf '  -> %s -> %s\n' "$dst" "$src"
  done
}

remove_bin_symlinks() {
  local full=$1
  [[ -d $SYSTEM_BIN ]] || return 0
  local venv_bin entry target_abs
  venv_bin="$(skillset_venvs "$full")/default/bin"
  for entry in "$SYSTEM_BIN"/*; do
    [[ -L $entry ]] || continue
    target_abs=$(readlink -f "$entry" 2>/dev/null || true)
    [[ -n $target_abs ]] || continue
    if [[ $target_abs == $venv_bin/* ]]; then
      rm -f "$entry"
      printf '  -> removed %s\n' "$entry"
    fi
  done
}

# Enumerate skill dirs to register: every dir containing SKILL.md under
# active/skills/, recursively. If skills/ absent, return active/ if it has SKILL.md.
enumerate_skill_dirs() {
  local full=$1
  local active skills_dir
  active=$(skillset_active "$full")
  skills_dir="$active/skills"
  if [[ -d $skills_dir ]]; then
    local subs
    subs=$(walk_skill_dirs "$skills_dir" | LC_ALL=C sort)
    if [[ -n $subs ]]; then
      printf '%s\n' "$subs"
      return
    fi
  fi
  [[ -f "$active/SKILL.md" ]] && printf '%s\n' "$active"
}

# Names registered for npx skills remove. Includes the umbrella full name.
enumerate_skills() {
  local full=$1
  local active dirs name
  active=$(skillset_active "$full")
  dirs=$(enumerate_skill_dirs "$full")
  local -a names=()
  while IFS= read -r d; do
    [[ -z $d ]] && continue
    if [[ $d == "$active" ]]; then
      names+=("$full")
    else
      names+=("$(read_skill_name "$d")")
    fi
  done <<<"$dirs"
  if [[ -f "$active/SKILL.md" ]] && ! printf '%s\n' "${names[@]}" | grep -qxF "$full"; then
    names=("$full" "${names[@]}")
  fi
  [[ ${#names[@]} -gt 0 ]] && printf '%s\n' "${names[@]}"
}

install_skills_via_npx() {
  local full=$1
  local dirs
  dirs=$(enumerate_skill_dirs "$full")
  [[ -n $dirs ]] || return 0
  local count
  count=$(printf '%s\n' "$dirs" | wc -l | tr -d ' ')
  printf '  installing %s skill(s) via npx skills (all agents, global)\n' "$count"
  while IFS= read -r d; do
    [[ -z $d ]] && continue
    npx --yes skills add "$d" --agent '*' --global --yes
  done <<<"$dirs"
}

uninstall_skills_via_npx() {
  local full=$1
  local names
  names=$(enumerate_skills "$full")
  [[ -n $names ]] || return 0
  local count
  count=$(printf '%s\n' "$names" | wc -l | tr -d ' ')
  printf '  uninstalling %s skill(s) via npx skills\n' "$count"
  local -a arr=()
  while IFS= read -r n; do [[ -n $n ]] && arr+=("$n"); done <<<"$names"
  npx --yes skills remove --global --yes "${arr[@]}" || true
}
