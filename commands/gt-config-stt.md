# Configure Speech-to-Text Settings

Select and save STT parameters (model, language, output format, etc.) to a config file used by genotools workflows.

## Input

`$ARGUMENTS` — Optional. Can be:
- `show` to display current config
- Empty to enter interactive selection

## Workflow

### 1. Load current config

Read the config file at `~/.genotools/stt/config.yaml`. If it doesn't exist, create the directory and file with defaults:

```yaml
model: large-v3-turbo
language: en
backend: mlx
output_format: yaml
beam_size: 5
temperature: 0.0
word_timestamps: true
```

Display the current configuration to the user.

If `$ARGUMENTS` is `show`, stop here.

### 2. Select model

Use `AskUserQuestion` to let the user pick a Whisper model:

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `large-v3-turbo` | ~800M | Fast (MLX) | Best balance |
| `large-v3` | ~1.5B | Slower | Highest accuracy |
| `medium` | ~769M | Fast | Good |
| `small` | ~244M | Very fast | Moderate |

Default: whatever is currently in config (or `large-v3-turbo` for new configs). Mark the current selection.

### 3. Select language

Use `AskUserQuestion`:
- `en` — English (Recommended)
- `auto` — Auto-detect (slower, useful for multilingual content)
- Other — let user type a language code

### 4. Select backend

Use `AskUserQuestion`:
- `mlx` — MLX (Apple Silicon optimized) (Recommended)
- `cpu` — CPU (portable, slower)

### 5. Advanced settings

Use `AskUserQuestion` (multiSelect) to ask which advanced settings the user wants to customize:
- Beam size (default: 5)
- Temperature (default: 0.0)
- Word timestamps (default: true)
- Output format (default: yaml)

For each selected setting, use a follow-up `AskUserQuestion` with appropriate options:

**Beam size:** 1 (fastest), 3, 5 (default), 10 (most accurate)

**Temperature:** 0.0 (deterministic, recommended), 0.2 (slight variation), 0.5 (more variation)

**Word timestamps:** true (needed for alignment workflows), false (segment-level only)

**Output format:** yaml (default, used by video pipeline), json, srt, txt

If the user doesn't want to customize any, keep current values.

### 6. Save config

Write the final config to `~/.genotools/stt/config.yaml`:

```yaml
model: <selected>
language: <selected>
backend: <selected>
output_format: <selected>
beam_size: <selected>
temperature: <selected>
word_timestamps: <selected>
```

Display the saved configuration to the user.

### 7. Update README if needed

If `~/.genotools/stt/` was newly created, update `~/.genotools/README.md`:
- Add `stt/` to the structure tree
- Add an "STT Configuration" section explaining the config
- Add the skill to the Skills table

## Notes

- The config is consumed by `~/.genotools/video/align_audio.py` and any future STT workflows
- MLX backend requires Apple Silicon (M1+)
- `large-v3-turbo` is the recommended default: nearly as accurate as `large-v3` but significantly faster on MLX
- When changing models, remind the user that the model will be downloaded on first use
