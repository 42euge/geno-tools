"""OpenAI-compatible LLM client for the geno ecosystem.

Zero extra dependencies — uses only stdlib urllib.request + json + sqlite3.
Used by `geno-tools llm probe` (benchmark) and `geno-tools llm suggest`
(dot-notation tab name suggestion).

Probe history is stored in ~/.geno/llm.db (SQLite). Rankings are derived
from the stored runs (EMA of ttft, total, tok/sec) so they stabilise over
repeated probes instead of bouncing on network noise.
"""

from __future__ import annotations

import json
import sqlite3
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterator

DB_PATH = Path.home() / ".geno" / "llm.db"


# ---- SQLite history store --------------------------------------------------

def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS probe_runs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts        INTEGER NOT NULL,          -- unix timestamp
            model     TEXT    NOT NULL,
            endpoint  TEXT    NOT NULL,
            ttft_ms   INTEGER,
            total_ms  INTEGER,
            tok_per_sec REAL,
            samples   INTEGER,
            ok        INTEGER NOT NULL DEFAULT 1,
            error     TEXT
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_model ON probe_runs(model, endpoint, ts)")
    con.commit()
    return con


def save_run(result: dict, endpoint: str) -> None:
    """Persist one probe result to the history DB."""
    with _db() as con:
        con.execute(
            "INSERT INTO probe_runs (ts,model,endpoint,ttft_ms,total_ms,tok_per_sec,samples,ok,error) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (int(time.time()), result["model"], endpoint,
             result.get("ttft_ms"), result.get("total_ms"),
             result.get("tok_per_sec"), result.get("samples", 0),
             1 if result.get("ok") else 0, result.get("error", "")),
        )


def load_rankings(endpoint: str, limit_per_model: int = 10) -> list[dict]:
    """Return EMA-averaged rankings from the last N runs per model.

    Sorted by avg_ttft_ms ascending (fastest first). Only includes models
    that had at least one successful run against this endpoint.
    """
    with _db() as con:
        rows = con.execute("""
            SELECT model,
                   AVG(ttft_ms)     AS avg_ttft_ms,
                   AVG(total_ms)    AS avg_total_ms,
                   AVG(tok_per_sec) AS avg_tok_per_sec,
                   SUM(samples)     AS total_samples,
                   COUNT(*)         AS runs,
                   MAX(ts)          AS last_seen
            FROM (
                SELECT model, ttft_ms, total_ms, tok_per_sec, samples, ts
                FROM probe_runs
                WHERE endpoint = ? AND ok = 1
                ORDER BY ts DESC
                LIMIT ?
            )
            GROUP BY model
            ORDER BY avg_ttft_ms ASC
        """, (endpoint, limit_per_model * 200)).fetchall()
    return [
        {
            "model": r[0],
            "ttft_ms": round(r[1]) if r[1] is not None else 9999999,
            "total_ms": round(r[2]) if r[2] is not None else 9999999,
            "tok_per_sec": round(r[3], 1) if r[3] else 0.0,
            "total_samples": r[4] or 0,
            "runs": r[5],
            "last_seen": r[6],
            "ok": True,
        }
        for r in rows
    ]


# Prompt used when probing latency — short, fast to respond.
_PROBE_PROMPT = "Reply with one word: ready"

# System prompt for tab naming — model receives tab context and returns a name.
_NAME_SYSTEM = (
    "You are a workspace organiser. Given a terminal tab's context "
    "(working directory, running job, raw title), respond with ONLY a "
    "dot-notation object path like 'program.area.aspect' (2–3 segments, "
    "all lowercase-kebab, no explanation). Examples: bluebeam.rf.receiver, "
    "ngrt.ct.deploy, geno.dev.vault. Use the cwd basename and job name as "
    "strong hints. Never include spaces or uppercase."
)


def _headers(token: str) -> dict:
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _post(url: str, token: str, payload: dict, timeout: int) -> tuple[dict, float, float]:
    """POST json payload; return (response_dict, ttft_seconds, total_seconds).

    TTFT is approximated as the time to get the first byte of the response body.
    For non-streaming requests this is effectively the full latency.
    """
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=_headers(token), method="POST")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ttft = time.monotonic() - t0
            body = resp.read()
            total = time.monotonic() - t0
        return json.loads(body), ttft, total
    except urllib.error.HTTPError as e:
        body = e.read()
        raise RuntimeError(f"HTTP {e.code}: {body[:200].decode(errors='replace')}") from e


def discover_models(endpoint: str, token: str, timeout: int = 10) -> list[str]:
    """GET /models and return the list of model IDs."""
    url = endpoint.rstrip("/") + "/models"
    req = urllib.request.Request(url, headers=_headers(token))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Could not fetch models: HTTP {e.code}") from e
    # OpenAI format: {"data": [{"id": "..."}, ...]}
    models = data.get("data", [])
    return sorted(m["id"] for m in models if "id" in m)


def probe_model(endpoint: str, token: str, model: str,
                samples: int = 3, timeout: int = 10) -> dict:
    """Fire N chat completions and return averaged latency + tok/sec.

    Returns: {model, ttft_ms, total_ms, tok_per_sec, samples, ok, error}
    tok_per_sec is output-tokens / total_seconds, averaged across samples.
    """
    url = endpoint.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": _PROBE_PROMPT}],
        "max_tokens": 8,
    }
    ttfts, totals, tps_list = [], [], []
    last_err = ""
    for _ in range(samples):
        try:
            resp, ttft, total = _post(url, token, payload, timeout)
            ttfts.append(ttft)
            totals.append(total)
            # tok/sec: completion tokens / total elapsed
            usage = resp.get("usage") or {}
            completion_tokens = usage.get("completion_tokens", 0)
            if completion_tokens and total > 0:
                tps_list.append(completion_tokens / total)
        except Exception as e:  # noqa: BLE001
            last_err = str(e)[:120]

    if not ttfts:
        return {"model": model, "ttft_ms": 9999999, "total_ms": 9999999,
                "tok_per_sec": 0.0, "samples": 0, "ok": False, "error": last_err}

    return {
        "model": model,
        "ttft_ms": round(sum(ttfts) / len(ttfts) * 1000),
        "total_ms": round(sum(totals) / len(totals) * 1000),
        "tok_per_sec": round(sum(tps_list) / len(tps_list), 1) if tps_list else 0.0,
        "samples": len(ttfts),
        "ok": True,
        "error": "",
    }


def probe_all(endpoint: str, token: str, concurrency: int = 8,
              timeout: int = 10, samples: int = 3) -> list[dict]:
    """Discover all models, benchmark each in parallel (N samples each).

    Each result is persisted to ~/.geno/llm.db. Rankings returned here
    are the fresh raw averages from this run; call load_rankings() to get
    the historical EMA-averaged view across all runs.
    Returns list sorted by ttft_ms ascending (fastest first).
    """
    models = discover_models(endpoint, token, timeout)
    results = []
    with ThreadPoolExecutor(max_workers=min(concurrency, len(models) or 1)) as pool:
        futures = {pool.submit(probe_model, endpoint, token, m, samples, timeout): m
                   for m in models}
        for fut in as_completed(futures):
            r = fut.result()
            save_run(r, endpoint)
            results.append(r)
    results.sort(key=lambda r: r["ttft_ms"])
    return results


def suggest_name(endpoint: str, token: str, model: str,
                 cwd: str = "", job: str = "", title: str = "",
                 timeout: int = 10) -> str:
    """Ask the LLM to suggest a dot-notation tab name from context.

    Returns the suggested name string, or "" on failure.
    """
    context_lines = []
    if cwd:
        context_lines.append(f"cwd: {cwd}")
    if job:
        context_lines.append(f"job: {job}")
    if title:
        context_lines.append(f"title: {title}")
    user_msg = "\n".join(context_lines) or "no context"

    url = endpoint.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _NAME_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 20,
        "temperature": 0.2,
    }
    try:
        resp, _, _ = _post(url, token, payload, timeout)
        choices = resp.get("choices") or []
        if choices:
            name = choices[0].get("message", {}).get("content", "").strip()
            # strip quotes/punctuation the model might add
            name = name.strip("\"'`.,;").strip()
            if name and "." in name:
                return name
    except Exception:  # noqa: BLE001
        pass
    return ""
