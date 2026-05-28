# On-disk layout for geno-tools state. Source this from any resource script.
#
#   ~/.geno-tools/                  — installed skillsets
#   ~/.geno/                        — user state (config, traces, health, discovery)

: "${GENO_ROOT:=$HOME/.geno-tools}"
: "${GENO_DIR:=$HOME/.geno}"
: "${TRACES_DIR:=$GENO_DIR/traces}"
: "${HEALTH_DIR:=$GENO_DIR/health}"
: "${DISCOVERY_DIR:=$GENO_DIR/discovery}"
: "${RETRO_DIR:=$GENO_DIR/retro}"
: "${ISO_DIR:=$GENO_DIR/iso}"
: "${SYSTEM_BIN:=$HOME/.local/bin}"

# Canonicalize a name to its `geno-{name}` form.
normalize() {
  local name=$1
  case $name in
    geno-*) printf '%s\n' "$name" ;;
    *)      printf 'geno-%s\n' "$name" ;;
  esac
}

short() {
  local full=$1
  printf '%s\n' "${full#geno-}"
}

skillset_root()    { printf '%s/%s\n' "$GENO_ROOT"            "$(normalize "$1")"; }
skillset_git()     { printf '%s/%s/.git\n' "$GENO_ROOT"       "$(normalize "$1")"; }
skillset_active()  { printf '%s/%s/active\n' "$GENO_ROOT"     "$(normalize "$1")"; }
skillset_venvs()   { printf '%s/%s/venvs\n' "$GENO_ROOT"      "$(normalize "$1")"; }

# skillset_worktree NAME [VARIANT=main]
skillset_worktree() {
  local full
  full=$(normalize "$1")
  local variant=${2:-main}
  if [[ $variant == main ]]; then
    printf '%s/%s/main\n' "$GENO_ROOT" "$full"
  else
    printf '%s/%s/.worktrees/%s\n' "$GENO_ROOT" "$full" "$variant"
  fi
}
