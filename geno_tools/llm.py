"""OpenAI-compatible LLM client for the geno ecosystem.

Zero extra dependencies — uses only stdlib urllib.request + json.
Used by `geno-tools llm probe` (benchmark) and `geno-tools llm suggest`
(dot-notation tab name suggestion).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterator


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
                timeout: int = 10) -> dict:
    """Fire a minimal chat completion and measure latency.

    Returns: {model, ttft_ms, total_ms, ok, error}
    """
    url = endpoint.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": _PROBE_PROMPT}],
        "max_tokens": 8,
    }
    try:
        _, ttft, total = _post(url, token, payload, timeout)
        return {
            "model": model,
            "ttft_ms": round(ttft * 1000),
            "total_ms": round(total * 1000),
            "ok": True,
            "error": "",
        }
    except Exception as e:  # noqa: BLE001
        return {"model": model, "ttft_ms": 9999999, "total_ms": 9999999,
                "ok": False, "error": str(e)[:120]}


def probe_all(endpoint: str, token: str,
              concurrency: int = 8, timeout: int = 10) -> list[dict]:
    """Discover all models on the endpoint and benchmark each in parallel.

    Returns list sorted by ttft_ms ascending (fastest first).
    """
    models = discover_models(endpoint, token, timeout)
    results = []
    with ThreadPoolExecutor(max_workers=min(concurrency, len(models) or 1)) as pool:
        futures = {pool.submit(probe_model, endpoint, token, m, timeout): m
                   for m in models}
        for fut in as_completed(futures):
            results.append(fut.result())
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
