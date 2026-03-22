# Video Pipeline

Automated system for creating narrated explainer videos with Manim animations synchronized to voiceover audio.

## Problem

When creating Manim videos synced to pre-recorded narration, animation `wait()` durations need to match the audio exactly. Without timing data, this requires multiple render iterations (each taking minutes) to get right. This system solves that with **forced alignment** — using Whisper to map the transcript onto the audio waveform, producing exact timestamps that drive animation timing on the first render.

## Architecture

```
                   ┌──────────────┐
                   │ transcript.md │  (with <!-- segment: id --> markers)
                   └──────┬───────┘
                          │
                          ▼
┌─────────┐     ┌──────────────────┐
│ audio.mp3│────▶│  align_audio.py  │  Whisper forced alignment (MLX)
└─────────┘     └────────┬─────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ timing.yaml │  per-segment start/end timestamps
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  scene.py   │  Manim script using SegmentTimer
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ manim render│  → silent video .mp4
                  └──────┬──────┘
                         │
                         ▼
               ┌───────────────────┐
               │  ffmpeg combine   │  video + audio → final_video.mp4
               └───────────────────┘
```

## Components

### `align_audio.py` — Forced Alignment

CLI tool that takes a folder path and produces `timing.yaml`.

**Usage:**
```bash
source ~/.genotools/video/.venv/bin/activate
python ~/.genotools/video/align_audio.py /path/to/project/folder
```

**What it does:**

1. Reads `transcript.md` from the folder
2. Parses `<!-- segment: segment_id -->` HTML comment markers to split into segments
   - Fallback: splits by double-newline if no markers found
3. Picks the best `.mp3` file (prefers files without `-2`/`-3` suffix)
4. Concatenates all segment text into one string
5. Loads Whisper `large-v3-turbo` via MLX backend (Apple Silicon GPU-accelerated)
6. Runs `model.align()` — forced alignment, not transcription. This takes the known-correct text and finds where each word occurs in the audio waveform using Whisper's cross-attention mechanism + dynamic time warping
7. Maps word-level timestamps back to segment boundaries by word count
8. Writes `timing.yaml`

**How forced alignment works:**

Unlike transcription (audio → text), forced alignment takes both audio AND text as input and finds the temporal mapping between them. It uses Whisper's cross-attention weights to determine when each word is spoken, then applies DTW (dynamic time warping) to produce monotonic, non-overlapping timestamps. This is deterministic and much more accurate than estimating timing from word count.

**Model choice:**

- `large-v3-turbo` — 809M params, nearly as accurate as `large-v3` (1.55B) but 6x faster and uses ~4GB RAM
- MLX backend runs natively on Apple Silicon GPU via Metal
- First run downloads the model (~1.6GB) to HuggingFace cache (`~/.cache/huggingface/`)
- `stable-ts` was chosen over alternatives because it has a first-class `align()` API for pre-existing transcripts. WhisperX, despite its popularity, was designed for transcribe-then-align and doesn't cleanly support aligning a known transcript (see [whisperX#1308](https://github.com/m-bain/whisperX/issues/1308))

**Output format (`timing.yaml`):**

```yaml
audio_file: narration.mp3
audio_duration: 235.47
segments:
- id: segment_1_hook
  start: 0.36
  end: 52.84
  text: "Current AI models often succeed by..."
- id: segment_2_intro
  start: 53.66
  end: 82.1
  text: "Imagine a student who gets an A+..."
```

### `sync_utils.py` — Animation Timing

Importable module used by Manim scene scripts.

**`load_timing(path)`**

Reads `timing.yaml` and returns a dict keyed by segment ID. Computes an `effective_duration` for each segment that spans from the segment's start to the *next* segment's start (or audio end for the last segment). This covers inter-segment silence so that the video doesn't accumulate timing drift from gaps between spoken segments.

**`SegmentTimer`**

Tracks how much animation time has elapsed within a segment. Provides wrapper methods that call Manim's `scene.play()` / `scene.wait()` while bookkeeping the elapsed time.

| Method | What it does |
|--------|-------------|
| `seg.play(scene, *anims, run_time=1.0)` | Plays animation(s) and records `run_time` as elapsed |
| `seg.wait(scene, duration)` | Waits and records elapsed |
| `seg.after(scene, duration)` | Records elapsed for animations called directly on `scene` (not through `seg`) |
| `seg.wait_remaining(scene)` | Waits for `duration - elapsed`, absorbing any timing slack. No-op if over budget. **Must be the last call in each segment method.** |
| `seg.remaining()` | Returns time left (clamped to >= 0) |

**Usage pattern in scene.py:**

```python
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.expanduser("~/.genotools/video"))
from manim import *
from sync_utils import load_timing, SegmentTimer

class MyVideo(Scene):
    def setup(self):
        self.timing = load_timing(Path(__file__).parent / "timing.yaml")

    def construct(self):
        self.segment_1_hook()
        self.segment_2_body()

    def segment_1_hook(self):
        seg = SegmentTimer(self.timing["segment_1_hook"])

        title = Text("Hello", font_size=48)
        seg.play(self, Write(title), run_time=1.5)
        seg.wait(self, 2)
        seg.play(self, FadeOut(title), run_time=0.5)
        seg.wait_remaining(self)  # ← always last

    def segment_2_body(self):
        seg = SegmentTimer(self.timing["segment_2_body"])

        # For animations called directly on self (e.g. unpacking lists):
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1)
        seg.after(self, 1)  # ← manually track

        seg.wait_remaining(self)
```

**Critical rule:** `seg.wait_remaining(self)` must be the very last call in each segment method. If a FadeOut transition or cleanup animation comes after it, that time won't be accounted for and the video will run long.

## Transcript Format

Transcripts use HTML comments as segment markers:

```markdown
<!-- segment: segment_1_hook -->
First paragraph of narration that maps to the first visual segment...

<!-- segment: segment_2_body -->
Second paragraph...
```

- IDs are snake_case, typically `segment_N_description`
- Each segment maps to one method in the Manim scene class
- Text between markers is what gets aligned to the audio
- Other HTML comments within segments are stripped before alignment

## Project Folder Layout

Each video project lives in its own folder:

```
project-folder/
├── transcript.md          ← input: narration script with segment markers
├── audio.mp3              ← input: voiceover recording
├── timing.yaml            ← generated: alignment timestamps
├── scene.py               ← generated: Manim animation script
├── media/                 ← generated: Manim render output
│   └── videos/scene/1080p60/
│       └── MyVideo.mp4
└── final_video.mp4        ← output: video + audio combined
```

## Dependencies

**Python packages** (in `.venv`):
- `manim` — animation engine (Community Edition)
- `stable-ts[mlx]` — Whisper forced alignment with MLX backend
  - Includes: `mlx`, `mlx-whisper`, `mlx-metal`, `openai-whisper`, `torch`
- `pyyaml` — YAML serialization

**System packages** (via Homebrew):
- `ffmpeg` — video/audio processing
- `cairo` — 2D graphics (Manim dependency)
- `pango` — text rendering (Manim dependency)

## Troubleshooting

**"Failed to align the last N words"** — Warning from stable-ts when the very end of the transcript doesn't perfectly match the audio tail. Usually harmless; check that the last segment's end time is close to the audio duration.

**"N segments failed to align"** — Some internal Whisper segments couldn't be matched. Usually still produces usable output. If many segments fail, the transcript text may not match the audio (typos, ad-libs, etc).

**numpy serialization in YAML** — If `timing.yaml` contains `!!python/object` tags instead of plain numbers, the floats weren't converted from numpy. The `align_audio.py` script wraps all values in `float()` to prevent this.

**Video too long/short** — Check that `wait_remaining()` is the last call in every segment method. Any animations after it add untracked time.
