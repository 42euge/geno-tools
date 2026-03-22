# Create Podcast Video (Text-on-Screen)

You are creating a podcast-style video that displays the transcript text on screen synchronized to an audiobook narration, using Manim and the video tooling from `~/.genotools/video/`.

## Input

The user may provide a folder path as an argument: `$ARGUMENTS`

If `$ARGUMENTS` is empty or not provided, **default to the current working directory**. Before asking the user for a path, first check if `transcript.md` and `audiobook.wav` exist in the current working directory — if they do, use that directory automatically.

Inside the target folder you expect to find (output from `/gt-create-audiobook`):
- **transcript.md** — the narration text
- **audiobook.wav** — the generated audio file
- **audiobook_meta.yaml** — metadata (duration, chapters, etc.)

## Your Workflow

### 0. Ensure environment

The video venv at `~/.genotools/video/.venv` must exist. If not, create it:
```bash
python3 -m venv ~/.genotools/video/.venv
source ~/.genotools/video/.venv/bin/activate
pip install manim "stable-ts[mlx]" pyyaml
```
Also verify `ffmpeg`, `cairo`, `pango` are available (`brew install cairo pango ffmpeg` if missing).

Always activate the venv before any python/manim commands:
```bash
source ~/.genotools/video/.venv/bin/activate
```

### 1. Read and prepare inputs

Resolve the folder path: if `$ARGUMENTS` is non-empty use it, otherwise use the current working directory. Call the resolved path `FOLDER`.

- Read `FOLDER/transcript.md`
- Verify `FOLDER/audiobook.wav` exists
- Read `FOLDER/audiobook_meta.yaml` for duration/chapter info

### 2. Convert audio for alignment

The alignment tool expects `.mp3`. Convert the wav:
```bash
ffmpeg -y -i "FOLDER/audiobook.wav" -codec:a libmp3lame -qscale:a 2 "FOLDER/audiobook.mp3"
```

### 3. Segment the transcript

Break the transcript into **short segments of 1-2 sentences each** (~10-30 words). This is critical for the word-by-word streaming mode — shorter segments mean less text on screen at once and tighter word-level sync.

Guidelines for segmentation:
- Each segment should be **1-2 sentences** max
- Each heading (`#` or `##`) gets its own segment
- Each bullet/list item gets its own segment
- Break long sentences at natural clause boundaries if needed
- Aim for ~10-30 words per segment so the text fits on 2-3 lines when wrapped

Insert `<!-- segment: id -->` markers into `transcript.md` before each segment. Use short snake_case ids like `s01_title`, `s02_intro`, `s03_gap`, etc.

### 4. Run forced alignment

```bash
source ~/.genotools/video/.venv/bin/activate
python ~/.genotools/video/align_audio.py "FOLDER"
```

This produces `FOLDER/timing.yaml` with per-segment and **per-word timestamps**.

Read the resulting `timing.yaml` to verify segment boundaries look correct. The word-level timestamps are critical — they drive the word-by-word reveal.

### 5. Write the Manim scene

Create `FOLDER/scene.py` that uses a **data-driven approach**. The scene reads `timing.yaml` directly and renders all segments automatically with word-by-word karaoke-style highlighting.

**Two display modes** — controlled by `SUBTITLE_MODE` at the top of `scene.py`:

#### Mode 1: Subtitle mode (`SUBTITLE_MODE = True`) — default
- Text appears at the **bottom** of the screen with a dark translucent bar behind it
- The **top ~70% of the screen is free** for images, diagrams, and animations
- Smaller font, max 3 lines per segment
- Override `_on_segment(seg_id, ...)` to add visuals per segment in the top area
- A `self.visual_layer` VGroup persists across segments for managing top-area content

#### Mode 2: Fullscreen mode (`SUBTITLE_MODE = False`)
- Text centered on screen, fills available space
- No visual area — text is the entire content
- Good for pure audio-to-video conversion

**Visual style (both modes):**
- All segment text appears **dimmed** (`#333333`) at once — no invisible layout issues
- The **current word** highlights to bright white as it's spoken
- **Already-spoken words** fade to medium grey (`#888888`)
- Section headings use `BLUE` / `BOLD`
- Clean transitions between segments

**Structure — data-driven scene with subtitle support and visual hooks:**

```python
import sys, os, re
from pathlib import Path
sys.path.insert(0, os.path.expanduser("~/.genotools/video"))
import yaml
from manim import *

# ── Configuration ──
SUBTITLE_MODE = True  # True = bottom subtitles + free top area; False = centered fullscreen

DIMMED = "#333333"
SPOKEN = "#888888"
ACTIVE = WHITE
HEADING_COLOR = BLUE

SUBTITLE_BOTTOM_BUFF = 0.4
SUBTITLE_BG_OPACITY = 0.6
SUBTITLE_FONT_SIZE = 28
SUBTITLE_LINE_WIDTH = 60

FULL_FONT_SIZE = 26
FULL_LINE_WIDTH = 52

class PodcastScene(Scene):
    def setup(self):
        with open(Path(__file__).parent / "timing.yaml") as f:
            self.data = yaml.safe_load(f)
        self.visual_layer = VGroup()  # persistent top-area visuals
        self.add(self.visual_layer)

    def construct(self):
        segments = self.data["segments"]
        audio_duration = self.data["audio_duration"]
        prev_sub = None
        prev_sub_bg = None

        for i, seg in enumerate(segments):
            # ... data-driven loop over all segments
            # - cleans words, wraps into lines
            # - creates dimmed word mobjects
            # - positions at bottom (subtitle) or center (fullscreen)
            # - adds dark background bar in subtitle mode
            # - calls _on_segment() hook for adding top-area visuals
            # - streams word highlights using timestamps
            pass

    def _on_segment(self, seg_id, seg_start, seg_duration):
        """Hook: add visuals to the top area during a segment.

        Override to show images, diagrams, or animations above the subtitles.
        The visual_layer VGroup persists across segments.

        Example:
            if seg_id == "s22_tax_heading":
                img = ImageMobject("taxonomy.png").scale(1.5)
                img.to_edge(UP, buff=0.5)
                self.play(FadeIn(img), run_time=0.5)
                self.visual_layer.add(img)
            elif seg_id == "s27_fac_heading":
                self.play(FadeOut(self.visual_layer), run_time=0.5)
                self.visual_layer = VGroup()
                self.add(self.visual_layer)
        """
        pass
```

**Key rules:**
- The scene is fully data-driven — reads `timing.yaml`, no per-segment methods needed
- All text starts **dimmed** (visible) so layout is correct — no invisible placeholders
- Current word highlights to white, spoken words fade to grey — karaoke effect
- Headings detected by `"heading"` in the segment id
- In subtitle mode, a dark translucent bar sits behind the text
- Override `_on_segment()` to add images/diagrams/animations to the top area
- `self.visual_layer` is a persistent VGroup for managing top-area content across segments

### 6. Render the video

```bash
cd "FOLDER"
source ~/.genotools/video/.venv/bin/activate
manim render -qh scene.py PodcastScene  # 1080p 60fps
```

### 7. Combine video with audio

```bash
ffmpeg -y -i "FOLDER/media/videos/scene/1080p60/PodcastScene.mp4" \
  -i "FOLDER/audiobook.wav" \
  -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 \
  -shortest "FOLDER/podcast_video.mp4"
```

### 8. Verify and finalize

- Run `ffprobe` on both the video and audio to confirm durations match (within ~1s)
- The final output should be `FOLDER/podcast_video.mp4`
- Report duration and file size to the user

## Important Notes

- This skill is designed to run **after** `/gt-create-audiobook` has already generated the audio
- **Subtitle mode** (`SUBTITLE_MODE = True`) is the default — text at bottom, top area free for visuals
- **Fullscreen mode** (`SUBTITLE_MODE = False`) — centered text, no visual area
- For a fully custom animated video, use `/gt-create-video` instead
- Uses the same `~/.genotools/video/` tooling (align_audio.py, sync_utils.py, Manim) as `/gt-create-video`
- The data-driven approach means you do NOT need to write individual segment methods — the scene reads timing.yaml and generates everything automatically
- To add visuals, override `_on_segment(seg_id, seg_start, seg_duration)` in the scene — use `self.visual_layer` to manage persistent top-area content
- Prefer `Text()` over `Paragraph()` — Manim's Paragraph can be buggy
- If word timestamps look off, re-run alignment or adjust segment boundaries
