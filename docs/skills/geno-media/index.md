---
title: geno-media
description: Audiobooks, animated videos, podcasts, TTS/STT config
---

# geno-media

Audiobooks, animated videos, podcasts, TTS/STT config

[:material-github: GitHub](https://github.com/42euge/geno-media){ .md-button }

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-media
    
    Media creation skills for AI coding agents. Audiobook generation (Kokoro TTS), animated
    video creation (Manim), podcast-style videos, TTS/STT configuration, and audio
    uploads. Optimized for Apple Silicon.
    
    Installed via [geno-tools](https://github.com/42euge/geno-tools):
    ```bash
    geno-tools install media
    ```
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `/geno-media-audiobook-create [folder]` | Generate audiobook from transcript using Kokoro TTS |
    | `/geno-media-audiobook-recursive [folder]` | Recursive audiobook generation across subfolders |
    | `/geno-media-video-create [folder]` | Transcript + audio → animated Manim video |
    | `/geno-media-podcast-create [folder]` | Transcript + audio → karaoke-style text-on-screen video |
    | `/geno-media-tts-config` | Configure TTS (voice, speed profile, accent) |
    | `/geno-media-stt-config` | Configure STT (Whisper model, language, backend) |
    | `/geno-media-audio-upload` | Upload audio files to Google Drive |
    
    ## Runtime
    
    Runtime lives under `~/.geno-tools/geno-media/`:
    - `venvs/media/` — shared venv (Kokoro, Manim, stable-ts, pymupdf)
    - `scripts/audiobook/generate.py`, `scripts/video/{align_audio,sync_utils}.py` — symlinks into this repo
    - `configs/tts.yaml`, `configs/stt.yaml` — user-editable (copy-once from defaults)
    - `configs/profiles/*.yaml` — TTS speed profiles (user-editable)
    
    System deps: `brew install cairo pango ffmpeg` (macOS).
