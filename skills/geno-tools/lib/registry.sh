# Curated registry of geno-* skillsets. Discovers from GitHub via `gh`,
# falls back to a hardcoded list when gh is unavailable.
# Source after paths.sh.

REGISTRY_OWNER="42euge"
REGISTRY_PREFIX="geno-"
REGISTRY_EXCLUDE_DEFAULT="geno-tools"

# Print "name<TAB>url" lines for available repos.
registry_available() {
  if command -v gh >/dev/null 2>&1; then
    local out
    if out=$(gh repo list "$REGISTRY_OWNER" \
              --json name,url --limit 100 --no-archived 2>/dev/null); then
      if [[ -n $out ]] && command -v jq >/dev/null 2>&1; then
        printf '%s' "$out" | jq -r --arg p "$REGISTRY_PREFIX" --arg ex "$REGISTRY_EXCLUDE_DEFAULT" '
          .[] | select(.name | startswith($p)) | select(.name != $ex)
            | "\(.name)\t\(.url).git"' 2>/dev/null && return
      fi
    fi
  fi
  # fallback
  cat <<EOF
geno-agents	https://github.com/${REGISTRY_OWNER}/geno-agents.git
geno-media	https://github.com/${REGISTRY_OWNER}/geno-media.git
geno-research	https://github.com/${REGISTRY_OWNER}/geno-research.git
geno-taxes	https://github.com/${REGISTRY_OWNER}/geno-taxes.git
geno-kaggle	https://github.com/${REGISTRY_OWNER}/geno-kaggle.git
geno-dev	https://github.com/${REGISTRY_OWNER}/geno-dev.git
geno-specs	https://github.com/${REGISTRY_OWNER}/geno-specs.git
EOF
}

# Resolve a name (full or bare slug) to a git URL. Empty if unknown.
registry_resolve() {
  local name=$1
  local full
  full=$(normalize "$name")
  registry_available | awk -v n="$full" '$1 == n { print $2; exit }'
}
