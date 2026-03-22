"""Utilities for synchronizing Manim animations with narration audio."""

import yaml
from pathlib import Path


def load_timing(path):
    """Load timing.yaml and return segments keyed by id.

    Returns dict mapping segment_id -> {start, end, duration, text, words}.
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    segments = {}
    seg_list = data["segments"]
    for i, seg in enumerate(seg_list):
        # effective_end spans to the next segment's start (covers inter-segment silence)
        if i + 1 < len(seg_list):
            effective_end = seg_list[i + 1]["start"]
        else:
            effective_end = data["audio_duration"]

        segments[seg["id"]] = {
            "start": seg["start"],
            "end": seg["end"],
            "duration": round(effective_end - seg["start"], 3),
            "text": seg.get("text", ""),
            "words": seg.get("words", []),
        }
    return segments


class SegmentTimer:
    """Tracks elapsed animation time within a narration segment.

    Basic usage:
        seg = SegmentTimer(timing["s01_intro"])
        seg.play(scene, FadeIn(obj), run_time=1.5)
        seg.wait(scene, 2)
        seg.wait_remaining(scene)

    Word-cue usage (sync animation to a specific spoken word):
        seg.wait_until_word(scene, "metacognition")
        seg.play(scene, FadeIn(metacog_label), run_time=0.5)
    """

    def __init__(self, segment_data):
        self.duration = segment_data["duration"]
        self.start = segment_data["start"]
        self.words = segment_data.get("words", [])
        self.elapsed = 0.0

    def remaining(self):
        return max(0.0, self.duration - self.elapsed)

    def play(self, scene, *animations, run_time=1.0, **kwargs):
        """Play animation(s) and track elapsed time."""
        scene.play(*animations, run_time=run_time, **kwargs)
        self.elapsed += run_time

    def wait(self, scene, duration):
        """Wait and track elapsed time."""
        scene.wait(duration)
        self.elapsed += duration

    def after(self, scene, duration):
        """Record elapsed time for animations not called via seg.play()."""
        self.elapsed += duration

    def wait_remaining(self, scene):
        """Wait for remaining time in the segment (no-op if over)."""
        r = self.remaining()
        if r > 0.05:
            scene.wait(r)
            self.elapsed += r

    def wait_until_word(self, scene, word, occurrence=1):
        """Wait until the narrator speaks a specific word.

        Finds the Nth occurrence (default 1st) of a word in this segment's
        word list and waits until its start time relative to segment start.
        Case-insensitive, supports partial match (e.g. "metacog" matches
        "metacognition").

        Does nothing if already past that point or word not found.
        """
        count = 0
        for w in self.words:
            if word.lower() in w["word"].lower():
                count += 1
                if count == occurrence:
                    target = w["start"] - self.start
                    gap = target - self.elapsed
                    if gap > 0.05:
                        scene.wait(gap)
                        self.elapsed += gap
                    return
        # Word not found — no-op (caller can fall back to manual timing)

    def word_time(self, word, occurrence=1):
        """Return the start time of a word relative to segment start.

        Useful for computing run_time values:
            t = seg.word_time("benchmarks")
            seg.play(scene, Write(title), run_time=t - seg.elapsed)

        Returns None if word not found.
        """
        count = 0
        for w in self.words:
            if word.lower() in w["word"].lower():
                count += 1
                if count == occurrence:
                    return w["start"] - self.start
        return None
