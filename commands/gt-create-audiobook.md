# Create Audiobook with Kokoro TTS

You are generating an audiobook from text/markdown files using Kokoro TTS (82M params, runs locally on Apple Silicon).

Supporting code lives in `~/.genotools/audiobook/`.

## Input

The user may provide a folder path as an argument: `$ARGUMENTS`

If `$ARGUMENTS` is empty or not provided, **default to the current working directory**. Before asking the user for a path, first check if `transcript.md` exists in the current working directory — if it does, use that directory automatically.

Inside the target folder you will find:
- **transcript.md** — the text to convert to audio

## Your Workflow

### 0. Ensure environment

Check if `~/.genotools/audiobook/.venv` exists. If not, create it and install dependencies:
```bash
python3 -m venv ~/.genotools/audiobook/.venv
source ~/.genotools/audiobook/.venv/bin/activate
pip install "kokoro>=0.9" "misaki[en]" soundfile numpy pyyaml
```

Always activate the venv before any python commands:
```bash
source ~/.genotools/audiobook/.venv/bin/activate
```

### 1. Read and analyze the input

Resolve the folder path: if `$ARGUMENTS` is non-empty use it, otherwise use the current working directory. Call the resolved path `FOLDER` for the rest of this workflow.

- Read `FOLDER/transcript.md`
- Estimate length (word count → rough audio duration at ~150 words/min)
- Identify if there are chapter headings (markdown `#` or `##`)
- Note any content that should be skipped (code blocks, images, tables)

### 2. Prepare the text (if needed)

If the text needs cleanup for better TTS output:
- Expand abbreviations that might be mispronounced
- Add commas or periods where natural pauses are needed
- Replace special characters with spoken equivalents (e.g., `→` to "leads to")
- Save the cleaned version back to `FOLDER/transcript.md` (or as `FOLDER/audiobook_script.md` if you want to preserve the original)

### 3. Choose voice and settings

Discuss with the user which voice to use. Available Kokoro English voices:

**Female voices:**
- `af_heart` (default) — warm, natural
- `af_bella` — clear, professional
- `af_sarah` — calm, measured
- `af_nova` — bright, energetic
- `af_sky` — light, youthful
- `af_alloy`, `af_aoede`, `af_jessica`, `af_kore`, `af_nicole`, `af_river`

**Male voices:**
- `am_adam` — clear narrator
- `am_michael` — deep, authoritative
- `am_fenrir` — strong, dramatic
- `am_echo`, `am_eric`, `am_liam`, `am_onyx`, `am_puck`

Speed: 0.8 (slow/deliberate) to 1.2 (brisk). Default 1.0.

If the user doesn't specify, use `af_heart` at speed `1.0`.

### 4. Generate the audiobook

Run the generation script:
```bash
source ~/.genotools/audiobook/.venv/bin/activate
python ~/.genotools/audiobook/generate.py "FOLDER" --voice VOICE_ID --speed SPEED
```

This will produce:
- `audiobook.wav` — the full audio file
- `audiobook_meta.yaml` — metadata (duration, voice, chapters)

### 5. Post-process (optional)

If the user wants MP3 output or other formats, convert with ffmpeg:
```bash
# Convert to MP3
ffmpeg -i "$ARGUMENTS/audiobook.wav" -codec:a libmp3lame -qscale:a 2 "$ARGUMENTS/audiobook.mp3"

# Convert to M4A (AAC) — smaller file, good quality
ffmpeg -i "$ARGUMENTS/audiobook.wav" -codec:a aac -b:a 128k "$ARGUMENTS/audiobook.m4a"
```

### 6. Verify output

- Check the output file exists and has reasonable duration
- Play a short sample if possible: `ffplay -autoexit -t 10 "$ARGUMENTS/audiobook.wav"`
- Report the final duration and file size to the user

## Important Notes

- Kokoro is ~82M params and runs very fast on Apple Silicon (~36x realtime)
- The model generates at 24kHz sample rate
- For very long texts (books), generation may take a few minutes — this is normal
- If a chunk sounds odd, the text can be tweaked and just that section re-generated
- The script handles markdown cleanup automatically (strips formatting, code blocks, etc.)
