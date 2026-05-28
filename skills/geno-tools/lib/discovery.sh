# Discovery providers — GitHub orgs, GitLab groups, Gitea, Bitbucket,
# and a community search via `gh search repos`. Translated from the Python
# discovery module to shell using gh + jq + curl.
# Source after paths.sh, config.sh.

CANDIDATES_FILE="$DISCOVERY_DIR/candidates.jsonl"

# discovery_candidates → tab-separated lines: name<TAB>url<TAB>source<TAB>has_skill_md
discovery_candidates() {
  local sources_json
  sources_json=$(config_discovery_sources_json)
  [[ $sources_json == "[]" ]] && return 0
  command -v jq >/dev/null 2>&1 || { warn "discovery requires jq"; return 0; }

  local len i kind
  len=$(printf '%s' "$sources_json" | jq 'length')
  for ((i=0; i<len; i++)); do
    local src
    src=$(printf '%s' "$sources_json" | jq -c ".[$i]")
    kind=$(printf '%s' "$src" | jq -r '.kind // ""')
    case $kind in
      github)    _provider_github    "$src" ;;
      gitlab)    _provider_gitlab    "$src" ;;
      gitea)     _provider_gitea     "$src" ;;
      bitbucket) _provider_bitbucket "$src" ;;
      community) _provider_community "$src" ;;
      *)         warn "unknown discovery kind: $kind" ;;
    esac
  done
}

discovery_candidates_by_name() {
  discovery_candidates | awk -F'\t' '$4 == "true" { print $1 "\t" $2 }'
}

# ── github ────────────────────────────────────────────────────────────────────
_provider_github() {
  local src=$1
  local org prefix base label auth_env tok
  org=$(printf '%s' "$src" | jq -r '.org // ""')
  [[ -z $org ]] && return 0
  prefix=$(printf '%s' "$src" | jq -r '.prefix // "geno-"')
  base=$(printf '%s' "$src" | jq -r '.base_url // ""')
  auth_env=$(printf '%s' "$src" | jq -r '.auth_env // ""')
  label="github:$org"

  local env_prefix=""
  if [[ -n $auth_env ]]; then
    tok=$(printenv "$auth_env" 2>/dev/null || true)
    [[ -n $tok ]] && env_prefix="GH_TOKEN=$tok "
  fi
  if [[ -n $base ]]; then
    local host=${base#https://}; host=${host#http://}; host=${host%/}
    env_prefix+="GH_HOST=$host "
  fi

  command -v gh >/dev/null 2>&1 || return 0

  local repos
  repos=$(env $env_prefix gh repo list "$org" \
            --json name,url --limit 200 --no-archived 2>/dev/null) || return 0
  [[ -z $repos ]] && return 0

  printf '%s' "$repos" | jq -r --arg p "$prefix" --arg label "$label" '
    .[] | select(.name | startswith($p))
        | [.name, (.url + ".git"), $label] | @tsv' \
  | while IFS=$'\t' read -r name url source_label; do
      if env $env_prefix gh api --silent "/repos/$org/$name/contents/SKILL.md" >/dev/null 2>&1; then
        printf '%s\t%s\t%s\ttrue\n'  "$name" "$url" "$source_label"
      else
        printf '%s\t%s\t%s\tfalse\n' "$name" "$url" "$source_label"
      fi
    done
}

# ── gitlab ────────────────────────────────────────────────────────────────────
_provider_gitlab() {
  local src=$1
  local group base prefix auth_env tok label
  group=$(printf '%s' "$src" | jq -r '.group // ""')
  [[ -z $group ]] && return 0
  base=$(printf '%s' "$src" | jq -r '.base_url // "https://gitlab.com"')
  base=${base%/}
  prefix=$(printf '%s' "$src" | jq -r '.prefix // "geno-"')
  auth_env=$(printf '%s' "$src" | jq -r '.auth_env // ""')
  label="gitlab:$group"

  command -v curl >/dev/null 2>&1 || return 0
  local hdr=()
  if [[ -n $auth_env ]]; then
    tok=$(printenv "$auth_env" 2>/dev/null || true)
    [[ -n $tok ]] && hdr=(-H "PRIVATE-TOKEN: $tok")
  fi

  local enc_group="${group//\//%2F}"
  local resp
  resp=$(curl -sf "${hdr[@]}" \
        "$base/api/v4/groups/$enc_group/projects?per_page=100&include_subgroups=true" 2>/dev/null) || return 0

  printf '%s' "$resp" | jq -r --arg p "$prefix" --arg label "$label" --arg base "$base" '
    .[] | select(.path | startswith($p))
        | [.path, .http_url_to_repo, (.id|tostring), $label] | @tsv' \
  | while IFS=$'\t' read -r name url pid source_label; do
      local has=false
      if [[ -n $pid ]]; then
        if curl -sfI "${hdr[@]}" \
              "$base/api/v4/projects/$pid/repository/files/SKILL.md?ref=HEAD" >/dev/null 2>&1; then
          has=true
        fi
      fi
      printf '%s\t%s\t%s\t%s\n' "$name" "$url" "$source_label" "$has"
    done
}

# ── gitea ─────────────────────────────────────────────────────────────────────
_provider_gitea() {
  local src=$1
  local org base prefix auth_env tok label
  org=$(printf '%s' "$src" | jq -r '.org // ""')
  [[ -z $org ]] && return 0
  base=$(printf '%s' "$src" | jq -r '.base_url // "https://gitea.com"')
  base=${base%/}
  prefix=$(printf '%s' "$src" | jq -r '.prefix // "geno-"')
  auth_env=$(printf '%s' "$src" | jq -r '.auth_env // ""')
  label="gitea:$org"

  command -v curl >/dev/null 2>&1 || return 0
  local hdr=()
  if [[ -n $auth_env ]]; then
    tok=$(printenv "$auth_env" 2>/dev/null || true)
    [[ -n $tok ]] && hdr=(-H "Authorization: token $tok")
  fi

  local resp
  resp=$(curl -sf "${hdr[@]}" "$base/api/v1/orgs/$org/repos?limit=100" 2>/dev/null) || return 0

  printf '%s' "$resp" | jq -r --arg p "$prefix" --arg label "$label" '
    .[] | select(.name | startswith($p))
        | [.name, .clone_url, $label] | @tsv' \
  | while IFS=$'\t' read -r name url source_label; do
      local has=false
      if curl -sfI "${hdr[@]}" "$base/api/v1/repos/$org/$name/contents/SKILL.md" >/dev/null 2>&1; then
        has=true
      fi
      printf '%s\t%s\t%s\t%s\n' "$name" "$url" "$source_label" "$has"
    done
}

# ── bitbucket ─────────────────────────────────────────────────────────────────
_provider_bitbucket() {
  local src=$1
  local ws prefix auth_env tok label
  ws=$(printf '%s' "$src" | jq -r '.workspace // ""')
  [[ -z $ws ]] && return 0
  prefix=$(printf '%s' "$src" | jq -r '.prefix // "geno-"')
  auth_env=$(printf '%s' "$src" | jq -r '.auth_env // ""')
  label="bitbucket:$ws"

  command -v curl >/dev/null 2>&1 || return 0
  local hdr=()
  if [[ -n $auth_env ]]; then
    tok=$(printenv "$auth_env" 2>/dev/null || true)
    [[ -n $tok ]] && hdr=(-H "Authorization: Bearer $tok")
  fi

  local resp
  resp=$(curl -sf "${hdr[@]}" "https://api.bitbucket.org/2.0/repositories/$ws?pagelen=100" 2>/dev/null) || return 0

  printf '%s' "$resp" | jq -r --arg p "$prefix" --arg label "$label" '
    .values[] | select(.slug | startswith($p))
              | . as $r
              | [.slug,
                 ([.links.clone[]? | select(.name == "https") | .href] | first // ""),
                 $label] | @tsv' \
  | while IFS=$'\t' read -r name url source_label; do
      local has=false
      if curl -sfI "${hdr[@]}" "https://api.bitbucket.org/2.0/repositories/$ws/$name/src/HEAD/SKILL.md" >/dev/null 2>&1; then
        has=true
      fi
      printf '%s\t%s\t%s\t%s\n' "$name" "$url" "$source_label" "$has"
    done
}

# ── community ─────────────────────────────────────────────────────────────────
_provider_community() {
  local src=$1
  local query limit label
  query=$(printf '%s' "$src" | jq -r '.query // "SKILL.md in:path filename:SKILL.md"')
  limit=$(printf '%s' "$src" | jq -r '.limit // 50')
  label="community:github-search"

  command -v gh >/dev/null 2>&1 || return 0

  local repos
  repos=$(gh search repos "$query" --json name,url,fullName --limit "$limit" 2>/dev/null) || return 0
  [[ -z $repos ]] && return 0

  printf '%s' "$repos" | jq -r --arg label "$label" '
    .[] | [.name, ((.url // "") + ".git"), ($label + ":" + (.fullName // ""))]
        | @tsv' \
  | awk -F'\t' '{ printf "%s\t%s\t%s\ttrue\n", $1, $2, $3 }'
}

# Get currently-installed skillset names (basenames under $GENO_ROOT).
_installed_names() {
  [[ -d $GENO_ROOT ]] || return 0
  local p
  for p in "$GENO_ROOT"/*; do
    [[ -d $p ]] || continue
    local n
    n=$(basename "$p")
    [[ $n == geno-* ]] && printf '%s\n' "$n"
  done
}

# Names already in the candidate queue.
_queued_names() {
  [[ -f $CANDIDATES_FILE ]] || return 0
  command -v jq >/dev/null 2>&1 || return 0
  jq -r '.name // empty' "$CANDIDATES_FILE" 2>/dev/null || true
}

# discovery_scan [namespace] [dry_run(0|1)]
# Prints new candidates as TSV; appends to candidates.jsonl unless dry_run=1.
discovery_scan() {
  local ns=${1:-}
  local dry=${2:-0}

  local installed_set queued_set
  installed_set=$(_installed_names | sort -u)
  queued_set=$(_queued_names | sort -u)

  local now
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  mkdir -p "$DISCOVERY_DIR"

  local found=0
  while IFS=$'\t' read -r name url src has_skill; do
    [[ $has_skill == "true" ]] || continue
    if [[ -n $ns ]]; then
      local pfx=$ns
      [[ $pfx != *- ]] && pfx="${pfx}-"
      [[ $name == ${pfx}* ]] || continue
    fi
    grep -qxF "$name" <<<"$installed_set" && continue
    grep -qxF "$name" <<<"$queued_set"    && continue
    printf '%s\t%s\t%s\n' "$name" "$url" "$src"
    found=$((found+1))
    if [[ $dry == 0 ]]; then
      jq -nc --arg n "$name" --arg u "$url" --arg s "$src" --arg t "$now" \
        '{name:$n, url:$u, source:$s, discovered:$t, has_skill_md:true}' \
        >>"$CANDIDATES_FILE"
    fi
  done < <(discovery_candidates)

  if [[ $found -gt 0 && $dry == 0 ]]; then
    printf '%s\n' "$now" >"$DISCOVERY_DIR/last_scan"
  fi
}
