# geno-tools

A personal toolkit of workflows, scripts, and [Claude Code](https://docs.anthropic.com/en/docs/claude-code) slash commands for research, content creation, project management, and development. Optimized for Apple Silicon.

## What it does

**Research & Knowledge Management**
- `/gt-research` — Deep research with multi-resolution Obsidian knowledge graphs (L0-L3 notes, literature review, canvas maps)
- `/gt-lab-notes` — Project lab notes: tasks, timestamped notes, plans
- `/gt-start-task` — Pick up a task from lab notes, plan it, execute it, mark it done

**Content Creation**
- `/gt-create-audiobook` — Markdown to narrated audiobook using [Kokoro TTS](https://github.com/hexgrad/kokoro) (82M params, ~36x realtime)
- `/gt-create-video` — Full pipeline: transcript + audio to animated [Manim](https://www.manim.community/) video with sync
- `/gt-create-podcast-video` — Transcript + audio to karaoke-style text-on-screen video

**Configuration & Deployment**
- `/gt-config-tts` — Voice, speed profile, accent settings for TTS
- `/gt-config-stt` — Whisper model, language, backend settings for STT
- `/gt-config-colab` — Google Drive account setup for Colab uploads
- `/gt-upload-colab` — Upload notebooks to Google Colab via Drive
- `/gt-upload-kaggle` — Upload notebooks to Kaggle (API or manual)

**Developer Tools**
- `/gt-rewrite-commit` — Rewrite git history into a clean narrative (backup + soft reset + restage)

## Repository structure

```
geno-tools/
├── install.sh                  # Sets up ~/.genotools/ runtime + Claude commands
├── audiobook/
│   └── generate.py             # Text → audiobook using Kokoro TTS
├── video/
│   ├── align_audio.py          # Forced alignment: transcript + audio → timing.yaml
│   ├── sync_utils.py           # SegmentTimer for syncing Manim animations to audio
│   └── README.md               # Detailed video pipeline docs
├── tts/
│   └── profiles/               # Speed variation profiles (LLM prompts)
│       ├── constant.yaml       # Fixed 1.0x speed
│       ├── natural.yaml        # Subtle human-like variation (0.92x–1.08x)
│       ├── storyteller.yaml    # Narrative arc driven (0.80x–1.15x)
│       ├── dynamic.yaml        # Full range for podcasts (0.78x–1.22x)
│       └── lecturer.yaml       # Teaching-optimized (0.80x–1.12x)
├── commands/                   # Claude Code slash commands (skills)
│   ├── gt-research.md          # Deep research with knowledge graphs
│   ├── gt-lab-notes.md         # Lab notes / task management
│   ├── gt-start-task.md        # Task execution workflow
│   ├── gt-create-audiobook.md  # Audiobook generation
│   ├── gt-create-video.md      # Animated video creation
│   ├── gt-create-podcast-video.md # Text-on-screen video
│   ├── gt-config-tts.md        # TTS configuration
│   ├── gt-config-stt.md        # STT configuration
│   ├── gt-config-colab.md      # Google Colab setup
│   ├── gt-upload-colab.md      # Upload to Colab
│   ├── gt-upload-kaggle.md     # Upload to Kaggle
│   └── gt-rewrite-commit.md    # Git history rewriting
└── config/
    └── defaults/               # Default config templates
        ├── tts.yaml
        ├── stt.yaml
        └── colab.json
```

## Installation

### Prerequisites

- macOS with Apple Silicon (M1+) — required for MLX Whisper backend
- Python 3.10+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — for using the slash commands
- Homebrew (for system dependencies)

### Install

```bash
git clone https://github.com/42euge/geno-tools.git
cd geno-tools
./install.sh
```

This does three things:
1. **Symlinks** source files and commands to their runtime locations
2. **Copies** default configs to `~/.genotools/` (won't overwrite existing)
3. **Creates** Python virtual environments with all dependencies

System dependencies (if missing):
```bash
brew install cairo pango ffmpeg
```

### Update

After pulling new changes:
```bash
./install.sh --link  # re-symlink only, skip venv creation
```

### What goes where

| Location | Contents | Tracked? |
|----------|----------|----------|
| `~/geno-tools/` | Source code, commands, profiles, docs | Git repo |
| `~/.genotools/` | Venvs, user configs, symlinks to source | Local only |
| `~/.claude/commands/` | Symlinks to `commands/gt-*.md` | Local only |

## Claude Code commands

All commands are installed as global [slash commands](https://docs.anthropic.com/en/docs/claude-code/slash-commands) in Claude Code. Type `/gt-` to see the full list.

### Research & Project Management

| Command | Description |
|---------|-------------|
| `/gt-research <brief>` | Deep research on any topic. Builds a multi-resolution Obsidian knowledge graph with L0-L3 notes, cross-cutting concepts, literature review (paper summaries + math primers), reference docs, and a navigable canvas. Runs research agents in parallel. |
| `/gt-lab-notes <subcommand>` | Manage per-project lab notes. Subcommands: `create` (init structure), `add-task: <desc>`, `do-task: <desc>`, `done-task: <desc>`, `note: <text>`. Creates `labnotes/` with tasks, timestamped notes, and plans. |
| `/gt-start-task [description]` | Pick up a task from lab notes, assess scope, plan if needed (enters plan mode for medium/large tasks), execute, and mark done. Logs progress to lab notes throughout. |

### Content Creation

| Command | Description |
|---------|-------------|
| `/gt-create-audiobook [folder]` | Generate audiobook from `transcript.md` using Kokoro TTS. Supports multiple voices, speed profiles, per-chunk speed maps. Outputs `audiobook.wav` + metadata. |
| `/gt-create-video [folder]` | Full video pipeline: forced-align transcript to audio, write a Manim scene with `SegmentTimer` sync, render, combine with audio. |
| `/gt-create-podcast-video [folder]` | Simpler video: displays transcript text synchronized to audio with word-by-word karaoke highlighting. Subtitle mode (text at bottom) or fullscreen mode. |

### Configuration

| Command | Description |
|---------|-------------|
| `/gt-config-tts` | Interactive TTS configuration: voice selection, speed profiles, accent, chunk settings. |
| `/gt-config-stt` | Interactive STT configuration: Whisper model, language, backend (MLX/CPU). |
| `/gt-config-colab` | Set up Google Drive account for notebook uploads. Auto-detects mounted accounts. |

### Deployment

| Command | Description |
|---------|-------------|
| `/gt-upload-colab <notebook>` | Copy a `.ipynb` to Google Drive for Colab access. |
| `/gt-upload-kaggle <notebook>` | Upload notebook to Kaggle. Ensures repo is public, notebook is committed. Supports Kaggle API push. |

### Developer Tools

| Command | Description |
|---------|-------------|
| `/gt-rewrite-commit` | Rewrite git commit history into clean narrative commits. Creates backup branch, soft-resets, restages files in logical order. |

## Standalone usage

The Python scripts can also be used directly without Claude Code:

### Generate an audiobook

```bash
source ~/.genotools/audiobook/.venv/bin/activate
python ~/.genotools/audiobook/generate.py /path/to/folder --use-config
```

### Align audio to transcript

```bash
source ~/.genotools/video/.venv/bin/activate
python ~/.genotools/video/align_audio.py /path/to/folder
```

### Use sync utilities in Manim

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.genotools/video"))
from sync_utils import load_timing, SegmentTimer

class MyVideo(Scene):
    def setup(self):
        self.timing = load_timing(Path(__file__).parent / "timing.yaml")

    def construct(self):
        seg = SegmentTimer(self.timing["segment_1_intro"])
        title = Text("Hello World")
        seg.play(self, Write(title), run_time=1.5)
        seg.wait_until_word(self, "important")  # sync to spoken word
        seg.play(self, FadeIn(highlight), run_time=0.5)
        seg.wait_remaining(self)  # absorb timing slack
```

See [`video/README.md`](video/README.md) for the full video pipeline documentation.

## Speed profiles

Each profile in `tts/profiles/` is an LLM prompt that controls speech pacing. Based on research showing information density and speech rate are inversely correlated (~39 bits/sec constant).

| Profile | Range | Best for |
|---------|-------|----------|
| `constant` | 1.0x fixed | Simple TTS, no variation |
| `natural` | 0.92x-1.08x | General use, subtle human feel |
| `storyteller` | 0.80x-1.15x | Fiction, audiobooks, narrative |
| `dynamic` | 0.78x-1.22x | Podcasts, essays, mixed content |
| `lecturer` | 0.80x-1.12x | Tutorials, courses, explanations |

Add custom profiles by creating new YAML files in `tts/profiles/`.

## License

MIT
