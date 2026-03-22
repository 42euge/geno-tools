#!/bin/bash
# install.sh — Set up ~/.genotools runtime environment from the geno-tools repo.
#
# What it does:
#   1. Creates ~/.genotools/ directory structure
#   2. Symlinks source files (scripts, profiles) from this repo
#   3. Copies default configs (only if they don't already exist)
#   4. Creates Python virtual environments with required packages
#   5. Installs Claude Code commands (skills) to ~/.claude/commands/
#
# Usage:
#   ./install.sh           # full install (venvs + symlinks + configs + commands)
#   ./install.sh --link    # symlinks + configs + commands only (skip venv creation)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$HOME/.genotools"

echo "geno-tools installer"
echo "  Source: $REPO_DIR"
echo "  Runtime: $RUNTIME_DIR"
echo ""

# ── Create directory structure ──────────────────────────────
mkdir -p "$RUNTIME_DIR"/{audiobook,video,tts/profiles,stt,colab}

# ── Symlink source files ────────────────────────────────────
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

echo "Linking source files..."
link_file "$REPO_DIR/audiobook/generate.py" "$RUNTIME_DIR/audiobook/generate.py"
link_file "$REPO_DIR/video/align_audio.py"  "$RUNTIME_DIR/video/align_audio.py"
link_file "$REPO_DIR/video/sync_utils.py"   "$RUNTIME_DIR/video/sync_utils.py"
link_file "$REPO_DIR/video/README.md"       "$RUNTIME_DIR/video/README.md"

# Symlink all TTS profiles
for profile in "$REPO_DIR"/tts/profiles/*.yaml; do
    name="$(basename "$profile")"
    link_file "$profile" "$RUNTIME_DIR/tts/profiles/$name"
done

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

echo ""
echo "Setting up configs..."
copy_default "$REPO_DIR/config/defaults/tts.yaml"   "$RUNTIME_DIR/tts/config.yaml"
copy_default "$REPO_DIR/config/defaults/stt.yaml"   "$RUNTIME_DIR/stt/config.yaml"
copy_default "$REPO_DIR/config/defaults/colab.json"  "$RUNTIME_DIR/colab/config.json"

# ── Create virtual environments ─────────────────────────────
if [ "${1:-}" = "--link" ]; then
    echo ""
    echo "Skipping venv creation (--link mode)."
else
    echo ""
    echo "Setting up virtual environments..."

    # Audiobook venv
    if [ ! -d "$RUNTIME_DIR/audiobook/.venv" ]; then
        echo "  Creating audiobook venv..."
        python3 -m venv "$RUNTIME_DIR/audiobook/.venv"
        "$RUNTIME_DIR/audiobook/.venv/bin/pip" install -q \
            "kokoro>=0.9" "misaki[en]" soundfile numpy pyyaml
        echo "  Audiobook venv ready."
    else
        echo "  Audiobook venv already exists."
    fi

    # Video venv
    if [ ! -d "$RUNTIME_DIR/video/.venv" ]; then
        echo "  Creating video venv..."
        python3 -m venv "$RUNTIME_DIR/video/.venv"
        "$RUNTIME_DIR/video/.venv/bin/pip" install -q \
            manim "stable-ts[mlx]" pyyaml
        echo "  Video venv ready."
    else
        echo "  Video venv already exists."
    fi
fi

# ── Install Claude Code commands ─────────────────────────────
CLAUDE_CMD_DIR="$HOME/.claude/commands"
if [ -d "$REPO_DIR/commands" ] && ls "$REPO_DIR"/commands/*.md &>/dev/null; then
    mkdir -p "$CLAUDE_CMD_DIR"
    echo ""
    echo "Installing Claude Code commands..."
    for cmd_file in "$REPO_DIR"/commands/gt-*.md; do
        name="$(basename "$cmd_file")"
        link_file "$cmd_file" "$CLAUDE_CMD_DIR/$name"
    done
    echo "  Commands available as /gt-* in Claude Code."
else
    echo ""
    echo "No commands found in $REPO_DIR/commands/ — skipping."
fi

# ── System dependencies check ───────────────────────────────
echo ""
echo "Checking system dependencies..."
missing=()
for cmd in ffmpeg cairo-trace pango-view; do
    if ! command -v "$cmd" &>/dev/null; then
        case "$cmd" in
            cairo-trace) missing+=("cairo") ;;
            pango-view)  missing+=("pango") ;;
            *)           missing+=("$cmd") ;;
        esac
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo "  Missing: ${missing[*]}"
    echo "  Install with: brew install ${missing[*]}"
else
    echo "  All system dependencies found."
fi

echo ""
echo "Done! Runtime environment is at $RUNTIME_DIR"
