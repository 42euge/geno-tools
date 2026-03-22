#!/usr/bin/env python3
"""Forced alignment of transcript segments to audio using stable-ts + MLX Whisper.

Usage:
    python align_audio.py /path/to/folder

The folder must contain:
  - transcript.md with <!-- segment: segment_id --> markers
  - One or more .mp3 audio files (picks the best one automatically)

Outputs timing.yaml in the same folder with per-segment start/end times.
"""

import re
import sys
from pathlib import Path

import yaml
import stable_whisper


def parse_transcript(text):
    """Parse transcript.md into segments using <!-- segment: id --> markers.

    Falls back to splitting by double-newline if no markers are found.
    """
    marker_pattern = re.compile(r"<!--\s*segment:\s*(\S+)\s*-->")
    markers = list(marker_pattern.finditer(text))

    if markers:
        segments = []
        for i, match in enumerate(markers):
            seg_id = match.group(1)
            start = match.end()
            end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
            seg_text = re.sub(r"<!--.*?-->", "", text[start:end]).strip()
            if seg_text:
                segments.append({"id": seg_id, "text": seg_text})
        return segments

    # Fallback: split by double newline
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return [{"id": f"segment_{i+1}", "text": p} for i, p in enumerate(paragraphs)]


def pick_audio_file(folder):
    """Pick the best audio file — prefers .mp3 without -2/-3 suffix."""
    mp3s = sorted(folder.glob("*.mp3"))
    if not mp3s:
        raise FileNotFoundError(f"No .mp3 files found in {folder}")
    primary = [f for f in mp3s if not re.search(r"-\d+\.mp3$", f.name)]
    return primary[0] if primary else mp3s[0]


def align(folder_path):
    """Run forced alignment and write timing.yaml."""
    folder = Path(folder_path)
    transcript_path = folder / "transcript.md"
    if not transcript_path.exists():
        raise FileNotFoundError(f"No transcript.md in {folder}")

    transcript_text = transcript_path.read_text()
    segments = parse_transcript(transcript_text)
    audio_file = pick_audio_file(folder)

    print(f"Audio: {audio_file.name}")
    print(f"Segments: {len(segments)}")
    for s in segments:
        preview = s["text"][:60].replace("\n", " ")
        print(f"  - {s['id']}: {preview}...")

    full_text = " ".join(seg["text"] for seg in segments)

    # Use MLX Whisper backend (optimized for Apple Silicon)
    print("\nLoading MLX Whisper large-v3-turbo...")
    model = stable_whisper.load_mlx_whisper("large-v3-turbo")
    print("Running forced alignment...")
    result = model.align(str(audio_file), full_text, language="en")

    # Collect all words
    all_words = []
    for wseg in result.segments:
        for word in wseg.words:
            all_words.append({
                "word": word.word.strip(),
                "start": round(word.start, 3),
                "end": round(word.end, 3),
            })

    audio_duration = round(all_words[-1]["end"], 3) if all_words else 0.0

    # Map words back to segments
    timing_segments = []
    word_idx = 0

    for seg in segments:
        seg_word_count = len(seg["text"].split())
        seg_aligned = all_words[word_idx:word_idx + seg_word_count]

        if seg_aligned:
            seg_start = seg_aligned[0]["start"]
            seg_end = seg_aligned[-1]["end"]
        else:
            seg_start = all_words[word_idx - 1]["end"] if word_idx > 0 else 0.0
            seg_end = seg_start

        timing_segments.append({
            "id": seg["id"],
            "text": seg["text"],
            "start": round(seg_start, 3),
            "end": round(seg_end, 3),
            "words": seg_aligned,
        })
        word_idx += seg_word_count

    # Build YAML output (convert numpy floats to plain Python floats)
    yaml_data = {
        "audio_file": audio_file.name,
        "audio_duration": float(audio_duration),
        "segments": [
            {
                "id": s["id"],
                "start": float(s["start"]),
                "end": float(s["end"]),
                "text": s["text"],
                "words": [
                    {"word": w["word"], "start": float(w["start"]), "end": float(w["end"])}
                    for w in s["words"]
                ],
            }
            for s in timing_segments
        ],
    }

    output_path = folder / "timing.yaml"
    with open(output_path, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"\nWrote {output_path}")
    print(f"Audio duration: {audio_duration:.1f}s\n")
    for s in timing_segments:
        dur = s["end"] - s["start"]
        print(f"  {s['id']}: {s['start']:.1f}s → {s['end']:.1f}s ({dur:.1f}s)")

    return yaml_data


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} /path/to/folder")
        sys.exit(1)
    align(sys.argv[1])
