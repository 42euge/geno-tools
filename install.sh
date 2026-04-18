#!/bin/bash
# install.sh — Legacy installer for the commands still living in this repo.
#
# NOTE: This installer is on its way out. For the new model, use the
# `geno-tools` CLI (pipx install geno-tools) which reads each skillset's
# genotools.yaml. Audiobook/video/TTS skills moved to
# https://github.com/42euge/geno-media. Remaining commands will move to
# geno-dev, geno-research, and geno-kaggle.
#
# What this script still does:
#   1. Creates ~/.genotools/colab/ (for colab upload config)
#   2. Copies colab default config (if missing)
#   3. Symlinks remaining commands to ~/.claude/commands/

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$HOME/.genotools"

echo "geno-tools installer"
echo "  Source: $REPO_DIR"
echo "  Runtime: $RUNTIME_DIR"
echo ""

# ── Create directory structure ──────────────────────────────
mkdir -p "$RUNTIME_DIR/colab"

link_file() {
    local src="$1" dst="$2"
    if [ -L "$dst" ]; then
        rm "$dst"
    elif [ -f "$dst" ]; then
        echo "  Backing up existing $dst → ${dst}.bak"
        mv "$dst" "${dst}.bak"
    fi
    ln -s "$src" "$dst"
    echo "  Linked: $dst → $src"
}

# ── Copy default configs (only if not already present) ──────
copy_default() {
    local src="$1" dst="$2"
    if [ ! -f "$dst" ]; then
        cp "$src" "$dst"
        echo "  Created: $dst (from defaults)"
    else
        echo "  Skipped: $dst (already exists)"
    fi
}

echo "Setting up configs..."
copy_default "$REPO_DIR/config/defaults/colab.json" "$RUNTIME_DIR/colab/config.json"

# ── Install Claude Code commands ─────────────────────────────
CLAUDE_CMD_DIR="$HOME/.claude/commands"
if ls "$REPO_DIR"/commands/gt-*.md &>/dev/null; then
    mkdir -p "$CLAUDE_CMD_DIR"
    echo ""
    echo "Installing Claude Code commands..."
    for cmd_file in "$REPO_DIR"/commands/gt-*.md; do
        name="$(basename "$cmd_file")"
        link_file "$cmd_file" "$CLAUDE_CMD_DIR/$name"
    done
    echo "  Commands available as /gt-* in Claude Code."
fi

echo ""
echo "Done. (Prefer \`pipx install geno-tools\` + \`geno-tools install <skillset>\` going forward.)"
