"""Tests for genotools.trace — skill trace system."""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from genotools import trace


@pytest.fixture(autouse=True)
def _tmp_geno_dir(tmp_path, monkeypatch):
    """Redirect all trace/health/retro dirs to a temp directory."""
    geno = tmp_path / ".geno"
    geno.mkdir()
    monkeypatch.setattr(trace, "GENO_DIR", geno)
    monkeypatch.setattr(trace, "TRACES_DIR", geno / "traces")
    monkeypatch.setattr(trace, "HEALTH_DIR", geno / "health")
    monkeypatch.setattr(trace, "RETRO_DIR", geno / "retro")
    monkeypatch.setattr(trace, "RETRO_QUEUE", geno / "retro" / "queue.jsonl")
    return geno


class TestEmit:
    def test_emit_creates_trace_file(self):
        rc = trace.main(["emit", "--skill", "test-skill", "--status", "success"])
        assert rc == 0
        files = list(trace.TRACES_DIR.rglob("*.jsonl"))
        assert len(files) == 1
        lines = files[0].read_text().strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["skill"]["name"] == "test-skill"
        assert data["outcome"]["status"] == "success"

    def test_emit_failure_queues_for_retro(self):
        trace.main(["emit", "--skill", "bad-skill", "--status", "failure"])
        assert trace.RETRO_QUEUE.exists()
        entries = trace.RETRO_QUEUE.read_text().strip().splitlines()
        assert len(entries) == 1
        entry = json.loads(entries[0])
        assert entry["skill"] == "bad-skill"
        assert entry["status"] == "failure"

    def test_emit_success_does_not_queue(self):
        trace.main(["emit", "--skill", "good-skill", "--status", "success"])
        assert not trace.RETRO_QUEUE.exists()

    def test_emit_with_metrics(self):
        trace.main([
            "emit", "--skill", "test", "--status", "partial",
            "--tool-calls", "10", "--errors", "3",
            "--thrashing-score", "0.25",
        ])
        files = list(trace.TRACES_DIR.rglob("*.jsonl"))
        data = json.loads(files[0].read_text().strip())
        assert data["metrics"]["tool_calls"] == 10
        assert data["metrics"]["errors"] == 3
        assert data["metrics"]["thrashing_score"] == 0.25


class TestList:
    def test_list_empty(self, capsys):
        rc = trace.main(["list"])
        assert rc == 0
        assert "no traces" in capsys.readouterr().out

    def test_list_with_traces(self, capsys):
        trace.main(["emit", "--skill", "s1", "--status", "success"])
        trace.main(["emit", "--skill", "s2", "--status", "failure"])
        rc = trace.main(["list"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "s1" in out
        assert "s2" in out

    def test_list_filter_by_skill(self, capsys):
        trace.main(["emit", "--skill", "keep", "--status", "success"])
        trace.main(["emit", "--skill", "skip", "--status", "success"])
        trace.main(["list", "--skill", "keep"])
        out = capsys.readouterr().out
        assert "keep" in out
        assert "skip" not in out


class TestHealth:
    def test_health_refresh(self, capsys):
        for _ in range(5):
            trace.main(["emit", "--skill", "tested", "--status", "success"])
        trace.main(["emit", "--skill", "tested", "--status", "failure"])

        rc = trace.main(["health", "--refresh"])
        assert rc == 0
        assert (trace.HEALTH_DIR / "tested.json").exists()

        card = json.loads((trace.HEALTH_DIR / "tested.json").read_text())
        assert card["skill"] == "tested"
        assert card["stats"]["total_invocations"] == 6
        assert 0.8 < card["stats"]["success_rate"] < 0.9

    def test_health_needs_retro_threshold(self, capsys):
        for _ in range(3):
            trace.main(["emit", "--skill", "bad", "--status", "failure"])
        for _ in range(2):
            trace.main(["emit", "--skill", "bad", "--status", "success"])

        trace.main(["health", "--refresh"])
        card = json.loads((trace.HEALTH_DIR / "bad.json").read_text())
        assert card["needs_retro"] is True

    def test_health_show_skill(self, capsys):
        trace.main(["emit", "--skill", "demo", "--status", "success"])
        trace.main(["health", "--refresh"])
        rc = trace.main(["health", "--skill", "demo"])
        assert rc == 0
        assert "demo" in capsys.readouterr().out


class TestQueue:
    def test_queue_empty(self, capsys):
        rc = trace.main(["queue"])
        assert rc == 0
        assert "empty" in capsys.readouterr().out

    def test_queue_after_failures(self, capsys):
        trace.main(["emit", "--skill", "s1", "--status", "failure"])
        trace.main(["emit", "--skill", "s2", "--status", "partial"])
        rc = trace.main(["queue"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "2 entries" in out

    def test_queue_clear(self, capsys):
        trace.main(["emit", "--skill", "s1", "--status", "failure"])
        trace.main(["queue", "--clear"])
        out = capsys.readouterr().out
        assert "cleared" in out
        assert not trace.RETRO_QUEUE.exists()
