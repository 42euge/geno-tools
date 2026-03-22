# Configure Text-to-Speech Settings

Select and save TTS parameters (voice, speed, output format, etc.) to a config file used by genotools workflows.

## Input

`$ARGUMENTS` — Optional. Can be:
- `show` to display current config
- Empty to enter interactive selection

## Workflow

### 1. Load current config

Read the config file at `~/.genotools/tts/config.yaml`. If it doesn't exist, create the directory and file with defaults:

```yaml
engine: kokoro
voice: af_heart
speed: 1.0
language: a
sample_rate: 24000
output_format: wav
chunk_max_chars: 400
inter_chunk_silence: 0.3
inter_chapter_silence: 0.8
```

Display the current configuration to the user.

If `$ARGUMENTS` is `show`, stop here.

### 2. Select engine

Use `AskUserQuestion`:
- `kokoro` — Kokoro TTS (82M params, local, Apple Silicon) (Recommended)

Only one engine currently supported. If the user picks "Other", note the name and save it but warn that only Kokoro is integrated in the generate scripts.

### 3. Select voice

Use `AskUserQuestion` to let the user pick a voice category first:

- **Female voices** — warm, clear, professional tones
- **Male voices** — narrator, authoritative, dramatic tones

Then show the specific voices for the chosen category:

**Female voices:**

| Voice | Tone |
|-------|------|
| `af_heart` (default) | Warm, natural |
| `af_bella` | Clear, professional |
| `af_sarah` | Calm, measured |
| `af_nova` | Bright, energetic |
| `af_sky` | Light, youthful |
| `af_alloy` | Neutral, versatile |
| `af_aoede` | Melodic |
| `af_jessica` | Conversational |
| `af_kore` | Steady, composed |
| `af_nicole` | Friendly |
| `af_river` | Smooth, flowing |

**Male voices:**

| Voice | Tone |
|-------|------|
| `am_adam` | Clear narrator |
| `am_michael` | Deep, authoritative |
| `am_fenrir` | Strong, dramatic |
| `am_echo` | Resonant |
| `am_eric` | Warm, conversational |
| `am_liam` | Friendly, casual |
| `am_onyx` | Rich, deep |
| `am_puck` | Lively, expressive |

Present the voices for the chosen category using `AskUserQuestion` (max 4 options per question, so split into multiple questions if needed — show the most popular first, then offer "More voices..." as an option to see the rest). Mark the currently selected voice.

### 4. Select speed profile

Speed profiles control how the LLM varies TTS speed per chunk based on content analysis. Each profile is a YAML file in `~/.genotools/tts/profiles/` containing a prompt that instructs the LLM when to speed up and slow down.

Use `AskUserQuestion`:
- `constant` — Fixed speed, no variation (classic TTS)
- `natural` — Subtle ebb and flow (0.92x–1.08x), barely perceptible (Recommended)
- `storyteller` — Wide range for narrative content (0.80x–1.15x), dramatic pacing
- `dynamic` — Full range for mixed content (0.78x–1.22x), podcast-quality expressiveness
- `lecturer` — Teaching-optimized (0.80x–1.12x), slows for new concepts, speeds through scaffolding

After selection, offer to view/edit the profile prompt: "Would you like to view or customize the prompt for this profile?" If yes, read `~/.genotools/tts/profiles/<profile>.yaml` and let the user edit it.

### 4b. Select base speed

The base speed is the center point around which the profile varies. Use `AskUserQuestion`:
- `0.8` — Slow, deliberate (audiobooks, accessibility)
- `1.0` — Normal (Recommended)
- `1.1` — Slightly brisk (podcasts)
- `1.2` — Fast (summaries, overviews)

### 5. Select language code

Use `AskUserQuestion`:
- `a` — American English (Recommended)
- `b` — British English

These are Kokoro lang_code values passed to KPipeline.

### 6. Advanced settings

Use `AskUserQuestion` (multiSelect) to ask which advanced settings the user wants to customize:
- Sample rate (default: 24000)
- Output format (default: wav)
- Chunk max chars (default: 400)
- Inter-chunk silence (default: 0.3s)
- Inter-chapter silence (default: 0.8s)

For each selected setting, use a follow-up `AskUserQuestion` with appropriate options:

**Sample rate:** 24000 (Kokoro native, recommended), 22050, 44100, 48000

**Output format:** wav (default, lossless), mp3 (smaller, requires ffmpeg), m4a (AAC, good balance)

**Chunk max chars:** 200 (shorter chunks, more pauses), 400 (default), 600 (longer chunks, fewer pauses)

**Inter-chunk silence:** 0.1s (minimal), 0.3s (default), 0.5s (longer pauses)

**Inter-chapter silence:** 0.5s (brief), 0.8s (default), 1.2s (dramatic pause), 2.0s (clear chapter break)

If the user doesn't want to customize any, keep current values.

### 7. Save config

Write the final config to `~/.genotools/tts/config.yaml`:

```yaml
engine: <selected>
voice: <selected>
voice_pool: <if random, list of voices>
speed: <selected>
speed_profile: <selected>
language: <selected>
sample_rate: <selected>
output_format: <selected>
chunk_max_chars: <selected>
inter_chunk_silence: <selected>
inter_chapter_silence: <selected>
speed_profile_pool:
  - constant
  - natural
  - storyteller
  - dynamic
  - lecturer
```

Display the saved configuration to the user.

### 8. Update README if needed

If `~/.genotools/tts/` was newly created, update `~/.genotools/README.md`:
- Add `tts/` to the structure tree
- Add a "TTS Configuration" section explaining the config
- Add the skill to the Skills table

## Notes

- The config is consumed by `~/.genotools/audiobook/generate.py` and the `/gt-create-audiobook` skill
- Kokoro runs locally on Apple Silicon at ~36x realtime
- Kokoro's native sample rate is 24000 Hz — other rates require resampling
- The `language` field is Kokoro's lang_code, not an ISO code (`a` = American English, `b` = British English)
- Voice selection significantly affects perceived quality — encourage the user to test a short sample before committing to a long generation

## Speed Profiles

Speed profiles live in `~/.genotools/tts/profiles/<name>.yaml`. Each contains:
- `name` — profile identifier
- `description` — what it does
- `speed_range` — [min, max] multiplier bounds
- `prompt` — the LLM prompt used to annotate each chunk with a speed multiplier

The prompt is the key piece — it teaches the LLM linguistics-based rules for when to speed up and slow down. Users can edit these prompts to fine-tune pacing behavior.

Available profiles:
- **constant** — no variation (1.0x fixed)
- **natural** — subtle human-like ebb and flow (0.92x–1.08x)
- **storyteller** — wide range for narrative/fiction (0.80x–1.15x)
- **dynamic** — full range for mixed content like podcasts (0.78x–1.22x)
- **lecturer** — teaching-optimized, slows for new concepts (0.80x–1.12x)

Users can create custom profiles by adding new YAML files to the profiles directory.
