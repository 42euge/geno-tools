---
title: geno-voice
description: Voice pipeline
---

# geno-voice

Voice pipeline

[:material-github: GitHub](https://github.com/42euge/geno-voice){ .md-button }

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-voice — Umbrella Skill
    
    Local voice pipeline for offline, privacy-first AI voice interaction. Provides
    on-device STT, TTS, and VAD for geno-ecosystem projects.
    
    ## Components
    
    - **STT (Speech-to-Text):** Whisper.cpp — local transcription
    - **TTS (Text-to-Speech):** Kokoro / Piper — local speech synthesis
    - **VAD (Voice Activity Detection):** Silero VAD — detect when the user starts/stops speaking
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-voice \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = voice pipeline component initialized or audio processed successfully
    - `failure` = model not found, engine unavailable, or audio device inaccessible
    - `abandoned` = user stopped early
