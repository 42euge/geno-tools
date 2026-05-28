#!/usr/bin/env bash
# Compile MkDocs Material skill documentation from SKILL.md frontmatter
# across all installed skillsets (and any --extra-dir checkouts).
#
# Usage: docs-build.sh [--docs-dir <path>] [--extra-dir <path> ...] [--dry-run]
#
# Replaces `geno-tools docs` / `geno-docs`.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"
require_cmd yq
require_cmd jq

DOCS_DIR=""
declare -a EXTRA=()
DRY=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --docs-dir)  DOCS_DIR=$2; shift 2 ;;
    --extra-dir) EXTRA+=("$2"); shift 2 ;;
    --dry-run)   DRY=1; shift ;;
    -h|--help)
      printf 'usage: docs-build.sh [--docs-dir <path>] [--extra-dir <path> ...] [--dry-run]\n'
      exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

# Auto-detect docs/ next to mkdocs.yml in cwd.
if [[ -z $DOCS_DIR ]]; then
  if [[ -d ./docs ]]; then
    DOCS_DIR=$(cd ./docs && pwd)
  elif [[ -f ./mkdocs.yml ]]; then
    DOCS_DIR=$(cd "$(dirname ./mkdocs.yml)/docs" 2>/dev/null && pwd) || true
  fi
fi
[[ -n $DOCS_DIR ]] || die "cannot find docs/ directory. Use --docs-dir."

# Categories — must match the Python implementation.
declare -A CATEGORY_OF=()
register_cat() {
  local cat=$1; shift
  for n in "$@"; do CATEGORY_OF[$n]=$cat; done
}
register_cat "Core"             geno-tools geno-agents geno-notes geno-mon geno-msg
register_cat "Developer"        geno-dev geno-loops geno-specs
register_cat "Runtime"          geno-iso geno-term geno-ws
register_cat "Tooling"          geno-mine geno-audit
register_cat "Data & Research"  geno-kaggle geno-research
register_cat "Creative"         geno-voice geno-media geno-bot
register_cat "Life"             geno-career geno-taxes geno-budget geno-hoa geno-remodel

CATEGORY_ORDER=("Core" "Developer" "Runtime" "Tooling" "Data & Research" "Creative" "Life" "Other")
declare -A CATEGORY_ICON=(
  [Core]=":material-cube-outline:"
  [Developer]=":material-code-braces:"
  [Runtime]=":material-cog-outline:"
  [Tooling]=":material-wrench-outline:"
  ["Data & Research"]=":material-chart-bar:"
  [Creative]=":material-palette-outline:"
  [Life]=":material-home-outline:"
  [Other]=":material-folder-outline:"
)

category_of() {
  local name=$1
  printf '%s\n' "${CATEGORY_OF[$name]:-Other}"
}

# ── parse a SKILL.md → emit JSON {name, description, body, ...}
parse_skill_md() {
  local path=$1
  local skillset=$2
  [[ -f $path ]] || return 1
  # Split frontmatter from body.
  local fm body
  fm=$(awk 'BEGIN{p=0} /^---$/{ if(++c==2) exit; p=1; next } p' "$path")
  body=$(awk 'BEGIN{c=0} /^---$/{c++; next} c>=2' "$path")
  [[ -n $fm ]] || return 1
  local meta
  meta=$(printf '%s\n' "$fm" | yq -p yaml -o json '.' 2>/dev/null) || return 1
  printf '%s' "$meta" | jq -c \
    --arg body "$body" --arg skillset "$skillset" --arg path "$path" '
    {
      name: (.name // ""),
      description: (.description // ""),
      license: (.license // ""),
      version: ((.metadata.version) // ""),
      author: ((.metadata.author) // ""),
      argument_hint: (."argument-hint" // ""),
      skillset: $skillset,
      source_path: $path,
      body: $body
    } | select(.name != "")'
}

short_description() {
  local desc=$1 body=$2 name=$3
  if [[ -z $desc ]]; then
    desc=$(printf '%s\n' "$body" | awk '
      /^# /  { sub(/^# +/, ""); print; exit }
    ')
    if [[ -z $desc || $desc == "$name" ]]; then
      desc=$(printf '%s\n' "$body" | awk '/^[^#[:space:]]/ { print; exit }')
    fi
  fi
  for sep in "Use when user says" "Use when the user says" "Use when user wants" \
             "Use when user asks" "Use when the user wants" "Use when the user asks"; do
    desc=${desc%%${sep}*}
  done
  desc=${desc%.}; desc=${desc%—}; desc=${desc%-}
  desc=${desc## }; desc=${desc%% }
  if [[ -n $desc ]]; then
    printf '%s.\n' "$desc"
  else
    printf '%s\n' "$name"
  fi
}

overview_section() {
  local body=$1
  printf '%s\n' "$body" | awk '
    BEGIN{cap=0}
    /^# /  { next }
    /^## / {
      h = tolower($0); sub(/^## +/, "", h)
      if (h == "input" || h == "when to use" || h == "commands" || h == "overview") {
        cap = 1; print; next
      } else { cap = 0; next }
    }
    cap { print }
  '
}

# ── discover skillsets ────────────────────────────────────────────────────────
declare -a SEARCH_NAMES=() SEARCH_DIRS=()
if [[ -d $GENO_ROOT ]]; then
  for d in "$GENO_ROOT"/*; do
    [[ -d $d ]] || continue
    n=$(basename "$d")
    [[ $n == .* ]] && continue
    main_dir="$d/main"
    if [[ -d $main_dir ]]; then
      SEARCH_NAMES+=("$n"); SEARCH_DIRS+=("$main_dir")
    fi
  done
fi
for e in "${EXTRA[@]+"${EXTRA[@]}"}"; do
  resolved=$(cd "$e" 2>/dev/null && pwd) || continue
  n=$(basename "$resolved")
  SEARCH_NAMES+=("$n"); SEARCH_DIRS+=("$resolved")
done

# Build skillsets list as JSON array.
SKILLSETS_JSON='[]'
declare -A SEEN=()

for i in "${!SEARCH_NAMES[@]}"; do
  name=${SEARCH_NAMES[$i]}
  base=${SEARCH_DIRS[$i]}
  [[ -n ${SEEN[$name]+x} ]] && continue
  SEEN[$name]=1

  manifest="$base/genotools.yaml"
  desc="" version=""
  if [[ -f $manifest ]]; then
    desc=$(yq -r '.description // ""' "$manifest" 2>/dev/null || printf '')
    version=$(yq -r '.version // ""' "$manifest" 2>/dev/null || printf '')
  fi

  # Collect skills under this skillset.
  declare -a SKILL_JSONS=()

  # Root SKILL.md (or skills/<name>/SKILL.md if no root).
  if [[ -f "$base/SKILL.md" ]]; then
    s=$(parse_skill_md "$base/SKILL.md" "$name") && SKILL_JSONS+=("$s")
  elif [[ -f "$base/skills/$name/SKILL.md" ]]; then
    s=$(parse_skill_md "$base/skills/$name/SKILL.md" "$name") && SKILL_JSONS+=("$s")
  fi

  if [[ -d "$base/skills" ]]; then
    for sd in "$base/skills"/*; do
      [[ -d $sd ]] || continue
      [[ -f "$sd/SKILL.md" ]] || continue
      s=$(parse_skill_md "$sd/SKILL.md" "$name") || continue
      SKILL_JSONS+=("$s")
    done
  fi

  [[ ${#SKILL_JSONS[@]} -eq 0 ]] && continue

  # Dedupe by .name and pull umbrella description.
  SKILLS_ARR=$(printf '%s\n' "${SKILL_JSONS[@]}" \
                | jq -s 'unique_by(.name)')
  if [[ -z $desc ]]; then
    umbrella_body=$(printf '%s' "$SKILLS_ARR" | jq -r --arg n "$name" '.[] | select(.name == $n) | .body // ""')
    umbrella_desc=$(printf '%s' "$SKILLS_ARR" | jq -r --arg n "$name" '.[] | select(.name == $n) | .description // ""')
    desc=$(short_description "$umbrella_desc" "$umbrella_body" "$name")
  fi

  cat=$(category_of "$name")
  ss=$(jq -nc \
        --arg name "$name" \
        --arg desc "$desc" \
        --arg version "$version" \
        --arg category "$cat" \
        --argjson skills "$SKILLS_ARR" '
        {name:$name, description:$desc, version:$version,
         github_url:("https://github.com/42euge/" + $name),
         category:$category, skills:$skills}')
  SKILLSETS_JSON=$(jq -c --argjson ss "$ss" '. + [$ss]' <<<"$SKILLSETS_JSON")
done

[[ $(jq 'length' <<<"$SKILLSETS_JSON") -gt 0 ]] || die "no skillsets discovered"

total_skillsets=$(jq 'length' <<<"$SKILLSETS_JSON")
total_skills=$(jq '[.[].skills | map(select(.name != ..namespace)) | length] | add // 0' <<<"$SKILLSETS_JSON" 2>/dev/null || printf 0)
# simpler total: skills minus umbrella-self per skillset
total_skills=$(jq '[.[] as $s | $s.skills | map(select(.name != $s.name)) | length] | add // 0' <<<"$SKILLSETS_JSON")

# ── helpers to build output ──────────────────────────────────────────────────
write_or_print() {
  local rel=$1
  local content=$2
  if [[ $DRY == 1 ]]; then
    printf '\n--- %s ---\n%s\n' "$rel" "$content"
  else
    local out="$DOCS_DIR/$rel"
    mkdir -p "$(dirname "$out")"
    printf '%s\n' "$content" >"$out"
  fi
}

# ── catalog page ──────────────────────────────────────────────────────────────
build_catalog() {
  local out
  out="---
title: Skill Catalog
description: Browse all skills in the geno ecosystem
---

# Skill Catalog

**${total_skillsets} skillsets** · **${total_skills} skills** across the geno ecosystem.

Browse by category, search for a skill, or drill into any skillset for full documentation.
"
  for cat in "${CATEGORY_ORDER[@]}"; do
    members=$(jq -c --arg c "$cat" '[.[] | select(.category == $c)]' <<<"$SKILLSETS_JSON")
    [[ $(jq 'length' <<<"$members") -gt 0 ]] || continue
    out+="
## ${CATEGORY_ICON[$cat]} $cat

<div class=\"feature-grid\" markdown>
"
    while IFS= read -r ss; do
      n=$(jq -r '.name' <<<"$ss")
      d=$(jq -r '.description' <<<"$ss" | tr '\n' ' ')
      [[ ${#d} -gt 120 ]] && d="${d:0:117}..."
      sc=$(jq --arg n "$n" '[.skills[] | select(.name != $n)] | length' <<<"$ss")
      out+="
<div class=\"feature-card\" markdown>

### [$n]($n/index.md)

$d
"
      if [[ $sc -gt 0 ]]; then
        noun=skills; [[ $sc == 1 ]] && noun=skill
        out+="
<span class=\"skill-count\">$sc $noun</span>
"
      fi
      out+="
</div>
"
    done < <(jq -c '.[]' <<<"$members")
    out+="
</div>
"
  done

  out+="
## All skills

| Skill | Skillset | Description |
|-------|----------|-------------|
"
  while IFS= read -r row; do
    out+="$row
"
  done < <(jq -r '
    .[] as $ss | $ss.skills[] | select(.name != $ss.name)
    | [.name, $ss.name, .description] | @tsv' <<<"$SKILLSETS_JSON" \
    | sort | awk -F'\t' '{
        d=$3; gsub(/\n/, " ", d)
        if (length(d) > 100) d = substr(d, 1, 97) "..."
        printf "| [`%s`](%s/index.md#%s) | [%s](%s/index.md) | %s |\n", $1, $2, $1, $2, $2, d
      }')
  printf '%s' "$out"
}

# ── per-skillset page ─────────────────────────────────────────────────────────
build_skillset_page() {
  local ss=$1
  local n d ver gh
  n=$(jq -r '.name' <<<"$ss")
  d=$(jq -r '.description' <<<"$ss" | tr '\n' ' ')
  [[ ${#d} -gt 120 ]] && d="${d:0:117}..."
  gh=$(jq -r '.github_url' <<<"$ss")

  local out="---
title: $n
description: $d
---

# $n

$d

[:material-github: GitHub]($gh){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
"
  while IFS=$'\t' read -r sn sd; do
    [[ $sn == "$n" ]] && continue
    short=$(short_description "$sd" "" "$sn")
    [[ ${#short} -gt 100 ]] && short="${short:0:97}..."
    out+="| [$sn](#$sn) | \`/$sn\` | $short |
"
  done < <(jq -r '.skills[] | [.name, .description] | @tsv' <<<"$ss")
  out+="
"

  # Umbrella overview block.
  umbrella=$(jq -c --arg n "$n" '.skills[] | select(.name == $n)' <<<"$ss")
  if [[ -n $umbrella && $umbrella != null ]]; then
    body=$(jq -r '.body' <<<"$umbrella")
    out+="## Overview

??? abstract \"Skillset overview (from SKILL.md)\"

"
    while IFS= read -r line; do
      out+="    $line
"
    done <<<"$body"
    out+="
"
  fi

  while IFS= read -r sk; do
    sn=$(jq -r '.name' <<<"$sk")
    [[ $sn == "$n" ]] && continue
    sd=$(jq -r '.description' <<<"$sk")
    body=$(jq -r '.body' <<<"$sk")
    arg_hint=$(jq -r '.argument_hint // ""' <<<"$sk")
    short=$(short_description "$sd" "$body" "$sn")
    out+="## $sn

**Slash command:** \`/$sn\`
"
    [[ -n $arg_hint ]] && out+="  **Arguments:** \`$arg_hint\`
"
    out+="
> $short

"
    overview=$(overview_section "$body")
    if [[ -n $overview ]]; then
      out+="??? info \"Overview (Level 3)\"

"
      while IFS= read -r line; do
        out+="    $line
"
      done <<<"$overview"
      out+="
"
    fi
    out+="??? example \"Full skill definition (Level 4)\"

"
    while IFS= read -r line; do
      out+="    $line
"
    done <<<"$body"
    out+="
"
  done < <(jq -c '.skills[]' <<<"$ss")

  printf '%s' "$out"
}

# ── nav YAML ─────────────────────────────────────────────────────────────────
build_nav() {
  printf -- '- Catalog: skills/index.md\n'
  for cat in "${CATEGORY_ORDER[@]}"; do
    members=$(jq -c --arg c "$cat" '[.[] | select(.category == $c)] | sort_by(.name)' <<<"$SKILLSETS_JSON")
    [[ $(jq 'length' <<<"$members") -gt 0 ]] || continue
    printf -- '- %s:\n' "$cat"
    while IFS= read -r n; do
      printf -- '    - %s: skills/%s/index.md\n' "$n" "$n"
    done < <(jq -r '.[].name' <<<"$members")
  done
}

# ── emit ─────────────────────────────────────────────────────────────────────
catalog=$(build_catalog)
write_or_print "skills/index.md" "$catalog"

while IFS= read -r ss; do
  n=$(jq -r '.name' <<<"$ss")
  page=$(build_skillset_page "$ss")
  write_or_print "skills/$n/index.md" "$page"
done < <(jq -c '.[]' <<<"$SKILLSETS_JSON")

pages=$((total_skillsets + 1))
printf 'Compiled %d skillsets, %d skills → %d pages\n' "$total_skillsets" "$total_skills" "$pages"
[[ $DRY == 0 ]] && printf 'Output: %s/skills/\n' "$DOCS_DIR"

printf '\n# Paste into mkdocs.yml nav > Skills Catalog:\n'
build_nav
