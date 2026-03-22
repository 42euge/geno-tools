# Create Explanatory Video with Manim

You are creating an explanatory video using Python and the Manim library (3Blue1Brown's animation engine) synchronized to a voiceover audio track.

Supporting code and templates live in `~/.genotools/video/`.

## Input

The user provides a folder path as an argument: `$ARGUMENTS`

Inside that folder you will find:
- **transcript.md** — the narration script for the video
- **One or more .mp3 audio files** — the voiceover recording (if multiple generations exist, pick the latest/highest quality one, usually the one without a `-2` suffix unless the user specifies otherwise)

## Your Workflow

### 0. Ensure environment
Check if `~/.genotools/video/.venv` exists. If not, create it and install dependencies:
```bash
python3 -m venv ~/.genotools/video/.venv
source ~/.genotools/video/.venv/bin/activate
pip install manim "stable-ts[mlx]" pyyaml
```
Also verify system deps (`ffmpeg`, `cairo`, `pango`) are available. On macOS: `brew install cairo pango ffmpeg`.

Always activate the venv before any python/manim commands:
```bash
source ~/.genotools/video/.venv/bin/activate
```

### 1. Read the inputs
- Read the transcript from `$ARGUMENTS/transcript.md`
- Identify the audio file(s) in the folder via `ls`

### 2. Break the transcript into segments with markers

Break the transcript into segments at **natural visual boundaries** — wherever the visuals should change. Segments can range from ~2s (a single short sentence) to ~15s (a longer thought), depending on what makes sense for the content. A new segment should start whenever:
- A new visual concept is introduced
- The topic shifts
- A list item is being enumerated (each item = its own segment so it appears when spoken)
- A key phrase deserves its own visual emphasis

Insert `<!-- segment: id -->` markers into `transcript.md` before each segment. Use short snake_case ids like `s01_hook`, `s02_challenge`, `s03_five_tracks`, etc.

**Example — a list being enumerated should be split per item:**
```markdown
<!-- segment: s04_track_learning -->
learning,

<!-- segment: s05_track_metacognition -->
metacognition,

<!-- segment: s06_track_attention -->
attention,

<!-- segment: s07_track_executive -->
executive functions,

<!-- segment: s08_track_social -->
and social cognition.
```

### 2b. Run forced alignment to get precise timing
```bash
source ~/.genotools/video/.venv/bin/activate
python ~/.genotools/video/align_audio.py "$ARGUMENTS"
```
This uses Whisper forced alignment (via `stable-ts` with MLX on Apple Silicon) to produce `timing.yaml` with:
- Per-segment start/end timestamps
- **Per-word timestamps** within each segment

Read the resulting `timing.yaml` to verify segment boundaries and review word timestamps. These word timestamps are critical for tight visual sync.

### 3. Design the visual plan
Before writing any code, outline a visual plan for each segment:
- What visual elements will appear (text, shapes, diagrams, equations, icons, charts)
- What animations/transitions will be used
- How the visuals reinforce the narration
- **Which specific words should trigger visual changes** (use word-cue sync)

Design principles:
- **Clean and minimal** — use the 3Blue1Brown aesthetic (dark background, bright colored elements)
- **One idea per screen** — don't overcrowd
- **Smooth transitions** — use FadeIn, FadeOut, Transform, etc.
- **Visual hierarchy** — key concepts should be visually prominent
- **Color coding** — use consistent colors for recurring concepts
- **Progressive reveal** — build up complex ideas step by step

### 4. Write the Manim Python script

Create a single Python file at `$ARGUMENTS/scene.py` with the following structure:

```python
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.expanduser("~/.genotools/video"))
from manim import *
from sync_utils import load_timing, SegmentTimer

class VideoScene(Scene):
    def setup(self):
        self.timing = load_timing(Path(__file__).parent / "timing.yaml")

    def construct(self):
        self.s01_hook()
        self.s02_challenge()
        # ...
```

**Each segment method uses a SegmentTimer to stay in sync with the audio.**

#### Basic timing (segment-level)
```python
def s01_hook(self):
    seg = SegmentTimer(self.timing["s01_hook"])
    title = Text("Title", font_size=48)
    seg.play(self, Write(title), run_time=1.5)
    seg.wait(self, 2)
    seg.play(self, FadeOut(title), run_time=0.5)
    seg.wait_remaining(self)  # MUST be last — pads to fill segment
```

#### Word-cue timing (sub-segment precision)
Use `seg.wait_until_word()` to trigger animations exactly when a word is spoken. This is how you get tight visual-audio sync:

```python
def s04_five_tracks(self):
    seg = SegmentTimer(self.timing["s04_five_tracks"])
    # "The five tracks are: learning, metacognition, attention, ..."

    tracks = ["Learning", "Metacognition", "Attention", "Executive Functions", "Social Cognition"]
    words  = ["learning", "metacognition", "attention", "executive", "social"]
    colors = [BLUE, ORANGE, GREEN, PURPLE, RED]

    labels = VGroup()
    for track, word, color in zip(tracks, words, colors):
        label = Text(track, font_size=28, color=color)
        labels.add(label)
    labels.arrange(DOWN, buff=0.4).move_to(ORIGIN)

    for label, word in zip(labels, words):
        seg.wait_until_word(self, word)       # wait until narrator says the word
        seg.play(self, FadeIn(label), run_time=0.4)

    seg.wait_remaining(self)
```

#### SegmentTimer API reference
| Method | Description |
|--------|-------------|
| `seg.play(scene, *anims, run_time=1.0)` | Play + track time |
| `seg.wait(scene, duration)` | Wait + track time |
| `seg.after(scene, duration)` | Track time for `self.play()` calls not routed through seg |
| `seg.wait_remaining(scene)` | Pad remaining time. **Must be last call in segment.** |
| `seg.wait_until_word(scene, word)` | Wait until narrator speaks `word` (case-insensitive partial match, e.g. "metacog" matches "metacognition") |
| `seg.wait_until_word(scene, word, occurrence=2)` | Wait for 2nd occurrence of a word |
| `seg.word_time(word)` | Get the time (relative to segment start) when a word is spoken. Returns `None` if not found. Useful for computing `run_time` values. |

**Important timing rules:**
- `seg.wait_remaining(self)` must be the very last call in each segment method
- For `self.play()` calls not routed through `seg.play()`, track them with `seg.after(self, run_time)`
- The SegmentTimer's duration spans from this segment's start to the next segment's start (covering inter-segment silence)
- Use `seg.wait_until_word()` whenever a visual should appear in sync with a specific spoken word — this is the key to tight alignment

### 5. Render the video
```bash
cd "$ARGUMENTS"
source ~/.genotools/video/.venv/bin/activate
manim render -qh scene.py VideoScene  # -qh = high quality 1080p
```

System deps if missing: `brew install cairo pango ffmpeg`

### 6. Combine video with audio
```bash
ffmpeg -i media/videos/scene/1080p60/VideoScene.mp4 -i "audio_file.mp3" \
  -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 \
  -shortest output_with_audio.mp4
```

### 7. Verify and finalize
- `ffprobe` both files — durations should be within ~1s
- The final output file should be named `$ARGUMENTS/final_video.mp4`

## Important Notes
- Always read the transcript FIRST to understand the content before designing visuals
- Prefer simple, elegant animations over complex ones
- Use `Text()` for regular text, `MathTex()` for LaTeX math
- Group related elements with `VGroup()` for easier manipulation
- Use `.animate` syntax for property animations: `self.play(obj.animate.shift(RIGHT))`
- Keep font sizes readable: 48 for titles, 36 for subtitles, 28-32 for body text
- Use Manim's built-in colors: BLUE, RED, GREEN, YELLOW, PURPLE, ORANGE, WHITE, GREY
- If the script is very long, consider splitting into multiple scene classes and rendering separately, then concatenating with ffmpeg
