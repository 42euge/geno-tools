#!/usr/bin/env python3
"""Generate the geno face SVG from current GitHub repo state.

Run during CI before mkdocs build. Uses `gh` CLI for API calls.
Falls back to neutral defaults if gh is unavailable or API fails.
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RepoState:
    open_prs: int = 0
    closed_prs_7d: int = 0
    open_issues: int = 0
    commits_7d: int = 0
    active_branches: int = 1
    has_conflicts: bool = False
    ci_failing: bool = False


@dataclass
class FaceParams:
    # Outer corner offset: positive = outer point moves up, negative = down
    # Pivots around the fixed inner corner
    eye_outer_dy_l: float = 0.0
    eye_outer_dy_r: float = 0.0
    # Grin scale: 0=tight smirk, 1=huge grin
    grin_scale: float = 0.5
    # Activity warmth: 0=cool purple, 1=warm pink
    warmth: float = 0.0
    # Eye color
    eye_color: str = "#e8650a"


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def gh_api(endpoint: str) -> dict | list | None:
    try:
        r = subprocess.run(
            ["gh", "api", endpoint, "--paginate"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0:
            return json.loads(r.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def fetch_state(repo: str = "42euge/geno-tools") -> RepoState:
    state = RepoState()

    prs = gh_api(f"repos/{repo}/pulls?state=open&per_page=100")
    if prs is not None:
        state.open_prs = len(prs)

    closed = gh_api(f"repos/{repo}/pulls?state=closed&per_page=30&sort=updated&direction=desc")
    if closed is not None:
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        state.closed_prs_7d = sum(
            1 for pr in closed
            if pr.get("merged_at") and datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00")) > cutoff
        )

    commits = gh_api(f"repos/{repo}/commits?per_page=30")
    if commits is not None:
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        state.commits_7d = sum(
            1 for c in commits
            if datetime.fromisoformat(
                c["commit"]["committer"]["date"].replace("Z", "+00:00")
            ) > cutoff
        )

    branches = gh_api(f"repos/{repo}/branches?per_page=100")
    if branches is not None:
        state.active_branches = len(branches)

    status = gh_api(f"repos/{repo}/commits/HEAD/status")
    if status and isinstance(status, dict):
        state.ci_failing = status.get("state") == "failure"

    return state


def state_to_params(s: RepoState) -> FaceParams:
    p = FaceParams()

    # Eye outer offset: CI failure/conflicts push outer corners down (angrier)
    if s.ci_failing:
        p.eye_outer_dy_l = 10.0
        p.eye_outer_dy_r = 10.0
    elif s.has_conflicts:
        p.eye_outer_dy_l = 6.0
        p.eye_outer_dy_r = 6.0
    elif s.open_prs > 4:
        p.eye_outer_dy_l = -5.0
        p.eye_outer_dy_r = -5.0

    # Grin scale: merge velocity makes the grin bigger
    p.grin_scale = clamp(s.closed_prs_7d / 10.0, 0, 1)

    # Warmth: commit activity
    p.warmth = clamp(s.commits_7d / 20.0, 0, 1)

    # Eye color
    if s.ci_failing:
        p.eye_color = "#cc3300"
    elif p.warmth > 0.7:
        p.eye_color = "#f07020"
    else:
        p.eye_color = "#e8650a"

    return p


def generate_svg(p: FaceParams) -> str:
    bg = "#0e0b14"

    # --- Eyes: based on grid #1 from round 3 (cubic bezier, #14 positioning) ---
    # Baseline eye coords (from the liked variations)
    # These are the "calm" (scale=0) values; scale=1 makes them bigger

    # Inner corners are FIXED anchor points; outer corners move via dy offset
    ed = 55  # fixed curve depth

    # Left eye — inner corner fixed at (228, 158)
    lx2, ly2 = 228, 158                          # inner (fixed)
    lx1 = 118                                     # outer x (fixed)
    ly1 = 140 + p.eye_outer_dy_l                  # outer y (animated)
    lc1x = lx2 - (lx2 - lx1) * 0.25
    lc1y = ly2 + ed * 0.8
    lc2x = lx1 + (lx2 - lx1) * 0.25
    lc2y = ly1 + ed * 0.8
    left_path = f"M{lx1:.0f} {ly1:.0f} L{lx2:.0f} {ly2:.0f} C{lc1x:.0f} {lc1y:.0f} {lc2x:.0f} {lc2y:.0f} {lx1:.0f} {ly1:.0f} Z"

    lpx = (lx1 + lx2) / 2 + 8
    lpy = (ly1 + ly2) / 2 + ed * 0.28

    # Right eye — inner corner fixed at (284, 158)
    rx2, ry2 = 284, 158                           # inner (fixed)
    rx1 = 394                                      # outer x (fixed)
    ry1 = 140 + p.eye_outer_dy_r                   # outer y (animated)
    rc1x = rx2 + (rx1 - rx2) * 0.25
    rc1y = ry2 + ed * 0.8
    rc2x = rx1 - (rx1 - rx2) * 0.25
    rc2y = ry1 + ed * 0.8
    right_path = f"M{rx1:.0f} {ry1:.0f} L{rx2:.0f} {ry2:.0f} C{rc1x:.0f} {rc1y:.0f} {rc2x:.0f} {rc2y:.0f} {rx1:.0f} {ry1:.0f} Z"

    rpx = (rx1 + rx2) / 2 - 8
    rpy = (ry1 + ry2) / 2 + ed * 0.28

    pr_l = 7
    pr_r = 6

    # --- Grin: based on grid #14 from round 2 / #1 from round 3 ---
    # grin_scale controls width and curl
    gw = lerp(340, 380, p.grin_scale)  # grin total width
    gy = 220                            # grin top y
    curl_h = lerp(55, 72, p.grin_scale) # how far the ends curl up above gy

    ghw = gw / 2
    # Top edge: curves up at sides, dips in middle
    # Bottom edge: curves down for the chin
    grin_path = (
        f"M{256 - ghw:.0f} {gy - curl_h:.0f} "
        f"C{256 - ghw + 8:.0f} {gy + 10:.0f} {256 - 96:.0f} {gy + 42:.0f} 256 {gy + 44:.0f} "
        f"C{256 + 96:.0f} {gy + 42:.0f} {256 + ghw - 8:.0f} {gy + 10:.0f} {256 + ghw:.0f} {gy - curl_h:.0f} "
        f"C{256 + ghw - 5:.0f} {gy + 30:.0f} {256 + 80:.0f} {gy + 95:.0f} 256 {gy + 100:.0f} "
        f"C{256 - 80:.0f} {gy + 95:.0f} {256 - ghw + 5:.0f} {gy + 30:.0f} {256 - ghw:.0f} {gy - curl_h:.0f} Z"
    )

    # Mouth color: lerp from cool purple to warm pink
    mr = int(lerp(196, 220, p.warmth))
    mg = int(lerp(168, 155, p.warmth))
    mb = int(lerp(216, 200, p.warmth))
    mouth_color = f"#{mr:02x}{mg:02x}{mb:02x}"

    # Teeth (fixed at 7, clipped to grin shape)
    teeth_top = gy - curl_h - 10
    teeth_bot = gy + 110
    tooth_xs = [148, 183, 218, 256, 294, 329, 364]
    teeth_lines = "\n".join(
        f'    <path d="M{x} {teeth_top:.0f} L{x} {teeth_bot:.0f}" '
        f'stroke="{bg}" stroke-width="3.5" stroke-linecap="round" fill="none"/>'
        for x in tooth_xs
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <clipPath id="grin-clip">
      <path d="{grin_path}"/>
    </clipPath>
  </defs>

  <rect width="512" height="512" fill="{bg}"/>

  <!-- Left eye -->
  <path d="{left_path}" fill="{p.eye_color}"/>
  <ellipse cx="{lpx:.0f}" cy="{lpy:.0f}" rx="{pr_l}" ry="{pr_l + 1}" fill="{bg}"/>
  <circle cx="{lpx - 2:.0f}" cy="{lpy - 3:.0f}" r="2.5" fill="#fff"/>

  <!-- Right eye -->
  <path d="{right_path}" fill="{p.eye_color}"/>
  <ellipse cx="{rpx:.0f}" cy="{rpy:.0f}" rx="{pr_r}" ry="{pr_r + 1}" fill="{bg}"/>
  <circle cx="{rpx - 2:.0f}" cy="{rpy - 3:.0f}" r="2" fill="#fff"/>

  <!-- Grin -->
  <path d="{grin_path}" fill="{mouth_color}" stroke="{bg}" stroke-width="2"/>

  <!-- Teeth (clipped to grin) -->
  <g clip-path="url(#grin-clip)">
{teeth_lines}
  </g>
</svg>'''


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate geno face from repo state")
    parser.add_argument("-o", "--output", default="docs/assets/logo.svg")
    parser.add_argument("--repo", default="42euge/geno-tools")
    parser.add_argument("--dry-run", action="store_true", help="Use defaults, skip API")
    parser.add_argument("--dump-state", action="store_true", help="Print state and params")
    args = parser.parse_args()

    if args.dry_run:
        state = RepoState()
    else:
        state = fetch_state(args.repo)

    params = state_to_params(state)

    if args.dump_state:
        print(f"State: {state}")
        print(f"Params: {params}")

    svg = generate_svg(params)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg)
    print(f"Generated {out} (PRs={state.open_prs}, commits_7d={state.commits_7d}, branches={state.active_branches})")


if __name__ == "__main__":
    main()
