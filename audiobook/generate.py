#!/usr/bin/env python3
"""Generate audiobook from transcript.md using Kokoro TTS (82M params).

Usage:
    python generate.py /path/to/folder [--voice af_heart] [--speed 1.0]
    python generate.py /path/to/folder --use-config          # use ~/.genotools/tts/config.yaml
    python generate.py /path/to/folder --use-config --speed-map speed_map.yaml

The folder must contain a transcript.md file with the narration text.

Outputs:
    audiobook.wav  — full audiobook audio
    audiobook_meta.yaml  — metadata (duration, voice, chapters, speed profile)

Kokoro voices (English):
    af_heart (default), af_alloy, af_aoede, af_bella, af_jessica, af_kore,
    af_nicole, af_nova, af_river, af_sarah, af_sky,
    am_adam, am_echo, am_eric, am_fenrir, am_liam, am_michael, am_onyx, am_puck
"""

import argparse
import random
import re
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml


CONFIG_PATH = Path.home() / ".genotools" / "tts" / "config.yaml"
PROFILES_DIR = Path.home() / ".genotools" / "tts" / "profiles"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load TTS config from ~/.genotools/tts/config.yaml."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}


def resolve_voice(config: dict) -> str:
    """Resolve voice from config, handling random selection."""
    voice = config.get("voice", "af_heart")
    if voice in ("af_random", "am_random"):
        pool = config.get("voice_pool", [])
        if not pool:
            prefix = voice[:2]
            # Fallback pools
            pool = {
                "af": ["af_heart", "af_bella", "af_sarah", "af_nova", "af_sky",
                        "af_alloy", "af_aoede", "af_jessica", "af_kore",
                        "af_nicole", "af_river"],
                "am": ["am_adam", "am_michael", "am_fenrir", "am_echo",
                        "am_eric", "am_liam", "am_onyx", "am_puck"],
            }.get(prefix, ["af_heart"])
        voice = random.choice(pool)
        print(f"Random voice selected: {voice}")
    return voice


def load_speed_map(path: Path) -> dict[int, float] | None:
    """Load a pre-generated speed map (chunk_index -> speed multiplier)."""
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    if not data or "chunks" not in data:
        return None
    return {c["index"]: c["speed"] for c in data["chunks"]}


# ---------------------------------------------------------------------------
# Text processing
# ---------------------------------------------------------------------------

def read_transcript(folder: Path) -> str:
    """Read transcript.md from the folder."""
    transcript_path = folder / "transcript.md"
    if not transcript_path.exists():
        raise FileNotFoundError(f"No transcript.md found in {folder}")
    print(f"Input: {transcript_path}")
    return transcript_path.read_text()


def extract_chapters(text: str) -> list[dict]:
    """Extract chapter boundaries from markdown headings (# or ##)."""
    chapters = []
    lines = text.split("\n")
    current_pos = 0
    for line in lines:
        match = re.match(r"^#{1,2}\s+(.+)", line)
        if match:
            chapters.append({"title": match.group(1).strip(), "char_offset": current_pos})
        current_pos += len(line) + 1  # +1 for newline
    return chapters


def clean_text(text: str) -> str:
    """Strip markdown formatting, HTML comments, and other non-speech content."""
    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Remove markdown images
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Remove markdown links but keep text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove markdown formatting chars
    text = re.sub(r"[*_`~]", "", text)
    # Remove heading markers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_chunks(text: str, max_chars: int = 400) -> list[str]:
    """Split text into chunks suitable for TTS (respecting sentence boundaries).

    Kokoro handles up to ~510 tokens per pass. We chunk by sentences
    to keep each pass well within limits and produce natural pauses.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(current) + len(sentence) + 1 > max_chars and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = f"{current} {sentence}" if current else sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


# ---------------------------------------------------------------------------
# TTS generation
# ---------------------------------------------------------------------------

def generate_audio(text: str, voice: str = "af_heart", speed: float = 1.0,
                   lang_code: str = "a", sample_rate: int = 24000,
                   max_chars: int = 400,
                   inter_chunk_secs: float = 0.3,
                   inter_chapter_secs: float = 0.8,
                   speed_map: dict[int, float] | None = None,
                   ) -> tuple[np.ndarray, list[dict]]:
    """Generate audio from text using Kokoro TTS.

    Args:
        speed_map: Optional dict mapping chunk index to per-chunk speed multiplier.
                   If provided, overrides the global speed for each mapped chunk.

    Returns (audio_array, chunk_metadata).
    """
    # Import here so the module loads fast for --help etc.
    from kokoro import KPipeline

    pipeline = KPipeline(lang_code=lang_code)

    cleaned = clean_text(text)
    chapters = extract_chapters(text)
    chunks = split_into_chunks(cleaned, max_chars=max_chars)

    using_profile = speed_map is not None
    print(f"\nGenerating audio for {len(chunks)} chunks...")
    print(f"Voice: {voice} | Base speed: {speed}x"
          f"{' | Speed profile: active' if using_profile else ''}\n")

    all_audio = []
    chunk_meta = []
    current_sample = 0

    # Silence buffers
    silence_chunk = np.zeros(int(inter_chunk_secs * sample_rate), dtype=np.float32)
    silence_chapter = np.zeros(int(inter_chapter_secs * sample_rate), dtype=np.float32)

    start_time = time.time()

    for i, chunk in enumerate(chunks):
        # Determine speed for this chunk
        chunk_speed = speed
        if speed_map and i in speed_map:
            chunk_speed = speed * speed_map[i]

        # Generate audio for this chunk
        chunk_audio_parts = []
        for _gs, _ps, audio in pipeline(chunk, voice=voice, speed=chunk_speed):
            if audio is not None:
                chunk_audio_parts.append(audio)

        if not chunk_audio_parts:
            continue

        chunk_audio = np.concatenate(chunk_audio_parts)

        chunk_start = current_sample / sample_rate
        chunk_meta.append({
            "index": i,
            "start": round(chunk_start, 3),
            "duration": round(len(chunk_audio) / sample_rate, 3),
            "speed": round(chunk_speed, 3),
            "text": chunk[:80] + ("..." if len(chunk) > 80 else ""),
        })

        all_audio.append(chunk_audio)
        current_sample += len(chunk_audio)

        # Add appropriate silence
        all_audio.append(silence_chunk)
        current_sample += len(silence_chunk)

        # Progress
        elapsed = time.time() - start_time
        pct = (i + 1) / len(chunks) * 100
        speed_info = f" @ {chunk_speed:.2f}x" if using_profile else ""
        print(f"  [{i+1}/{len(chunks)}] {pct:.0f}%{speed_info} — {elapsed:.1f}s elapsed",
              end="\r")

    print()  # newline after progress

    if not all_audio:
        raise RuntimeError("No audio was generated — check input text.")

    audio = np.concatenate(all_audio)
    total_duration = len(audio) / sample_rate
    gen_time = time.time() - start_time
    print(f"\nDone: {total_duration:.1f}s of audio generated in {gen_time:.1f}s "
          f"({total_duration/gen_time:.1f}x realtime)")

    return audio, chunk_meta


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate audiobook from text/markdown using Kokoro TTS"
    )
    parser.add_argument("folder", help="Folder containing transcript.md")
    parser.add_argument("--voice", default=None,
                        help="Kokoro voice ID (default: from config or af_heart)")
    parser.add_argument("--speed", type=float, default=None,
                        help="Speech speed multiplier (default: from config or 1.0)")
    parser.add_argument("--output", default=None,
                        help="Output filename (default: audiobook.wav)")
    parser.add_argument("--use-config", action="store_true",
                        help="Read settings from ~/.genotools/tts/config.yaml")
    parser.add_argument("--speed-map", default=None,
                        help="Path to speed_map.yaml with per-chunk speed multipliers")
    args = parser.parse_args()

    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        print(f"Error: {folder} is not a directory")
        sys.exit(1)

    # Resolve settings: CLI args > config > defaults
    config = load_config() if args.use_config else {}

    voice = args.voice or resolve_voice(config) if config else (args.voice or "af_heart")
    speed = args.speed if args.speed is not None else config.get("speed", 1.0)
    lang_code = config.get("language", "a")
    sample_rate = config.get("sample_rate", 24000)
    max_chars = config.get("chunk_max_chars", 400)
    inter_chunk = config.get("inter_chunk_silence", 0.3)
    inter_chapter = config.get("inter_chapter_silence", 0.8)
    profile_name = config.get("speed_profile", "constant")

    # Load speed map if provided
    speed_map = None
    if args.speed_map:
        speed_map_path = Path(args.speed_map)
        if not speed_map_path.is_absolute():
            speed_map_path = folder / speed_map_path
        speed_map = load_speed_map(speed_map_path)
        if speed_map:
            print(f"Speed map loaded: {len(speed_map)} chunk overrides from {speed_map_path}")
        else:
            print(f"Warning: Could not load speed map from {speed_map_path}")

    text = read_transcript(folder)
    chapters = extract_chapters(text)
    audio, chunk_meta = generate_audio(
        text, voice=voice, speed=speed, lang_code=lang_code,
        sample_rate=sample_rate, max_chars=max_chars,
        inter_chunk_secs=inter_chunk, inter_chapter_secs=inter_chapter,
        speed_map=speed_map,
    )

    # Write audio
    output_name = args.output or "audiobook.wav"
    output_path = folder / output_name
    sf.write(str(output_path), audio, sample_rate)
    print(f"\nWrote: {output_path}")

    # Write metadata
    meta = {
        "voice": voice,
        "speed": speed,
        "speed_profile": profile_name,
        "sample_rate": sample_rate,
        "duration": round(len(audio) / sample_rate, 3),
        "chunks": len(chunk_meta),
    }
    if speed_map:
        meta["speed_map_used"] = True
        speeds = [c["speed"] for c in chunk_meta]
        meta["speed_stats"] = {
            "min": round(min(speeds), 3),
            "max": round(max(speeds), 3),
            "mean": round(sum(speeds) / len(speeds), 3),
        }
    if chapters:
        meta["chapters"] = [c["title"] for c in chapters]

    meta_path = folder / "audiobook_meta.yaml"
    with open(meta_path, "w") as f:
        yaml.dump(meta, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"Wrote: {meta_path}")


if __name__ == "__main__":
    main()
