"""Skill trace system — structured records of skill invocations.

Traces are the connective tissue for self-improving skills, knowledge
integration, and session mining. Every skill emits a trace on completion.

Storage: ~/.geno/traces/YYYY/YYYY-MM.jsonl (append-only, one line per trace)
Health:  ~/.geno/health/<skill-name>.yaml  (aggregated per-skill stats)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

GENO_DIR = Path.home() / ".geno"
TRACES_DIR = GENO_DIR / "traces"
HEALTH_DIR = GENO_DIR / "health"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _trace_file(dt: datetime | None = None) -> Path:
    dt = dt or _now()
    year_dir = TRACES_DIR / str(dt.year)
    year_dir.mkdir(parents=True, exist_ok=True)
    return year_dir / f"{dt.year}-{dt.month:02d}.jsonl"


def _build_trace(
    skill: str,
    status: str,
    *,
    skillset: str | None = None,
    version: str | None = None,
    error_type: str | None = None,
    error_detail: str | None = None,
    tool_calls: int = 0,
    errors: int = 0,
    thrashing_score: float = 0.0,
    user_corrections: int = 0,
    duration_turns: int = 0,
    task_id: str | None = None,
    scope: str | None = None,
    branch: str | None = None,
    consumed: list[str] | None = None,
    produced: list[str] | None = None,
    tags: list[str] | None = None,
) -> dict:
    now = _now()
    return {
        "id": f"trace-{uuid4().hex[:12]}",
        "timestamp": now.isoformat(),
        "session_id": os.environ.get("CLAUDE_SESSION_ID", ""),
        "project": os.environ.get("CLAUDE_PROJECT", os.getcwd()),
        "skill": {
            "name": skill,
            "skillset": skillset or skill.rsplit("-", 1)[0] if "-" in skill else skill,
            "version": version or "unknown",
        },
        "outcome": {
            "status": status,
            "error_type": error_type,
            "error_detail": error_detail,
        },
        "metrics": {
            "tool_calls": tool_calls,
            "errors": errors,
            "thrashing_score": thrashing_score,
            "user_corrections": user_corrections,
            "duration_turns": duration_turns,
        },
        "context": {
            "task_id": task_id,
            "scope": scope,
            "branch": branch,
        },
        "knowledge": {
            "consumed": consumed or [],
            "produced": produced or [],
        },
        "tags": tags or [],
    }


def cmd_emit(args: argparse.Namespace) -> int:
    trace = _build_trace(
        skill=args.skill,
        status=args.status,
        skillset=args.skillset,
        version=args.version,
        error_type=args.error_type,
        error_detail=args.error_detail,
        tool_calls=args.tool_calls,
        errors=args.errors,
        thrashing_score=args.thrashing_score,
        user_corrections=args.user_corrections,
        duration_turns=args.duration_turns,
        task_id=args.task,
        scope=args.scope,
        branch=args.branch,
        consumed=args.consumed,
        produced=args.produced,
        tags=args.tags,
    )

    path = _trace_file()
    with open(path, "a") as f:
        f.write(json.dumps(trace, separators=(",", ":")) + "\n")

    _queue_for_retro(trace["id"], args.skill, args.status)

    print(f"trace {trace['id']} → {path}")
    if args.status in ("failure", "partial"):
        print(f"queued for retro → {RETRO_QUEUE}")
    return 0


def _iter_traces(
    *,
    skill: str | None = None,
    since: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Read traces, newest first, with optional filters."""
    traces = []
    if not TRACES_DIR.exists():
        return traces

    files = sorted(TRACES_DIR.rglob("*.jsonl"), reverse=True)
    for f in files:
        for line in reversed(f.read_text().splitlines()):
            if not line.strip():
                continue
            try:
                t = json.loads(line)
            except json.JSONDecodeError:
                continue
            if skill and t.get("skill", {}).get("name") != skill:
                continue
            if status and t.get("outcome", {}).get("status") != status:
                continue
            if since:
                if t.get("timestamp", "") < since:
                    continue
            traces.append(t)
            if len(traces) >= limit:
                return traces
    return traces


def cmd_list(args: argparse.Namespace) -> int:
    traces = _iter_traces(
        skill=args.skill,
        since=args.since,
        status=args.status,
        limit=args.limit,
    )

    if args.json:
        print(json.dumps(traces, indent=2))
        return 0

    if not traces:
        print("no traces found")
        return 0

    for t in traces:
        ts = t["timestamp"][:19]
        sk = t["skill"]["name"]
        st = t["outcome"]["status"]
        tc = t["metrics"]["tool_calls"]
        er = t["metrics"]["errors"]
        print(f"{ts}  {sk:<40s}  {st:<8s}  tools={tc}  errors={er}")
    return 0


def _compute_health(skill_name: str, traces: list[dict]) -> dict:
    """Aggregate traces into a health card for a skill."""
    if not traces:
        return {}

    total = len(traces)
    successes = sum(1 for t in traces if t["outcome"]["status"] == "success")
    tool_calls = [t["metrics"]["tool_calls"] for t in traces]
    thrashing = [t["metrics"]["thrashing_score"] for t in traces]

    error_types: dict[str, int] = {}
    for t in traces:
        et = t["outcome"].get("error_type")
        if et:
            error_types[et] = error_types.get(et, 0) + 1

    reads: set[str] = set()
    writes: set[str] = set()
    for t in traces:
        reads.update(t.get("knowledge", {}).get("consumed", []))
        writes.update(t.get("knowledge", {}).get("produced", []))

    return {
        "skill": skill_name,
        "stats": {
            "total_invocations": total,
            "success_rate": round(successes / total, 3) if total else 0,
            "avg_tool_calls": round(sum(tool_calls) / total, 1) if total else 0,
            "avg_thrashing": round(sum(thrashing) / total, 3) if total else 0,
            "last_invoked": traces[0]["timestamp"],
        },
        "error_types": error_types,
        "knowledge": {
            "reads_from": sorted(reads),
            "writes_to": sorted(writes),
        },
        "needs_retro": (successes / total < 0.7) if total >= 5 else False,
    }


RETRO_DIR = GENO_DIR / "retro"
RETRO_QUEUE = RETRO_DIR / "queue.jsonl"
ISO_DIR = GENO_DIR / "iso"
ISO_INBOX = ISO_DIR / "inbox.jsonl"


def _queue_for_retro(trace_id: str, skill: str, status: str) -> None:
    """Append a failed trace to the retro queue."""
    if status not in ("failure", "partial"):
        return
    RETRO_DIR.mkdir(parents=True, exist_ok=True)
    entry = json.dumps({
        "trace_id": trace_id,
        "skill": skill,
        "status": status,
        "queued_at": _now().isoformat(),
    }, separators=(",", ":"))
    with open(RETRO_QUEUE, "a") as f:
        f.write(entry + "\n")


def cmd_queue(args: argparse.Namespace) -> int:
    """Show or manage the retro queue."""
    if args.clear:
        if RETRO_QUEUE.exists():
            RETRO_QUEUE.unlink()
            print("retro queue cleared")
        else:
            print("retro queue already empty")
        return 0

    if not RETRO_QUEUE.exists():
        print("retro queue is empty")
        return 0

    entries = []
    for line in RETRO_QUEUE.read_text().splitlines():
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if args.json:
        print(json.dumps(entries, indent=2))
    else:
        if not entries:
            print("retro queue is empty")
            return 0
        print(f"retro queue: {len(entries)} entries")
        for e in entries:
            print(f"  {e.get('queued_at', '?')[:19]}  {e.get('skill', '?'):<40s}  {e.get('status', '?')}")
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    if args.refresh:
        return _refresh_health(args)
    if args.skill:
        return _show_health(args.skill, args.json)
    return _show_all_health(args.json)


def _refresh_health(args: argparse.Namespace) -> int:
    """Rebuild health cards from traces."""
    all_traces = _iter_traces(limit=10000)
    if not all_traces:
        print("no traces found")
        return 0

    by_skill: dict[str, list[dict]] = {}
    for t in all_traces:
        name = t["skill"]["name"]
        by_skill.setdefault(name, []).append(t)

    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    needs_retro = []

    for skill_name, traces in by_skill.items():
        card = _compute_health(skill_name, traces)
        if not card:
            continue
        path = HEALTH_DIR / f"{skill_name}.json"
        with open(path, "w") as f:
            json.dump(card, f, indent=2)
            f.write("\n")
        count += 1
        if card.get("needs_retro"):
            needs_retro.append(skill_name)

    print(f"refreshed {count} health cards")
    if needs_retro:
        print(f"needs retro: {', '.join(needs_retro)}")
    return 0


def _show_health(skill: str, as_json: bool) -> int:
    path = HEALTH_DIR / f"{skill}.json"
    if not path.exists():
        print(f"no health card for {skill}")
        return 1

    card = json.loads(path.read_text())
    if as_json:
        print(json.dumps(card, indent=2))
    else:
        s = card["stats"]
        print(f"{card['skill']}")
        print(f"  invocations: {s['total_invocations']}")
        print(f"  success rate: {s['success_rate']:.0%}")
        print(f"  avg tool calls: {s['avg_tool_calls']}")
        print(f"  avg thrashing: {s['avg_thrashing']:.3f}")
        print(f"  last invoked: {s['last_invoked'][:19]}")
        if card.get("needs_retro"):
            print(f"  ⚠ needs retro (success rate < 70%)")
    return 0


def _show_all_health(as_json: bool) -> int:
    if not HEALTH_DIR.exists():
        print("no health cards — run `geno-trace health --refresh` first")
        return 0

    cards = []
    for p in sorted(HEALTH_DIR.glob("*.json")):
        cards.append(json.loads(p.read_text()))

    if as_json:
        print(json.dumps(cards, indent=2))
        return 0

    if not cards:
        print("no health cards")
        return 0

    print(f"{'skill':<40s}  {'rate':>5s}  {'n':>4s}  {'tools':>5s}  {'retro':>5s}")
    print("-" * 65)
    for c in cards:
        s = c["stats"]
        retro = "YES" if c.get("needs_retro") else ""
        print(
            f"{c['skill']:<40s}  {s['success_rate']:>5.0%}  "
            f"{s['total_invocations']:>4d}  {s['avg_tool_calls']:>5.1f}  {retro:>5s}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geno-trace", description="Skill trace system")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # emit
    p_emit = sub.add_parser("emit", help="record a skill trace")
    p_emit.add_argument("--skill", required=True)
    p_emit.add_argument("--status", required=True, choices=["success", "partial", "failure", "abandoned"])
    p_emit.add_argument("--skillset")
    p_emit.add_argument("--version")
    p_emit.add_argument("--error-type")
    p_emit.add_argument("--error-detail")
    p_emit.add_argument("--tool-calls", type=int, default=0)
    p_emit.add_argument("--errors", type=int, default=0)
    p_emit.add_argument("--thrashing-score", type=float, default=0.0)
    p_emit.add_argument("--user-corrections", type=int, default=0)
    p_emit.add_argument("--duration-turns", type=int, default=0)
    p_emit.add_argument("--task")
    p_emit.add_argument("--scope")
    p_emit.add_argument("--branch")
    p_emit.add_argument("--consumed", nargs="*", default=[])
    p_emit.add_argument("--produced", nargs="*", default=[])
    p_emit.add_argument("--tags", nargs="*", default=[])
    p_emit.set_defaults(func=cmd_emit)

    # list
    p_list = sub.add_parser("list", help="query stored traces")
    p_list.add_argument("--skill")
    p_list.add_argument("--status")
    p_list.add_argument("--since", help="ISO timestamp cutoff")
    p_list.add_argument("--limit", type=int, default=50)
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=cmd_list)

    # health
    p_health = sub.add_parser("health", help="view or refresh skill health cards")
    p_health.add_argument("--refresh", action="store_true", help="rebuild health cards from traces")
    p_health.add_argument("--skill", help="show health for a specific skill")
    p_health.add_argument("--json", action="store_true")
    p_health.set_defaults(func=cmd_health)

    # queue
    p_queue = sub.add_parser("queue", help="view or manage the retro queue")
    p_queue.add_argument("--clear", action="store_true", help="clear the retro queue")
    p_queue.add_argument("--json", action="store_true")
    p_queue.set_defaults(func=cmd_queue)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
