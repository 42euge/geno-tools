#!/usr/bin/env python3
"""Compile SKILL.md + GENO.md files into MkDocs-compatible docs pages.

Scans workspace repos and installed skillsets, parses frontmatter,
and generates the skill catalog + per-skill zoom-level pages for the
geno-tools documentation hub.

Usage:
    python scripts/compile_skill_docs.py [--workspace DIR] [--install-dir DIR] [--output DIR]
"""

from __future__ import annotations

import argparse
import re
import textwrap
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE_ROOT = Path.home() / "code-red"
INSTALL_DIR = Path.home() / ".geno-tools"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "skills"

REPO_DESCRIPTIONS: dict[str, str] = {
    "geno-tools": "Meta-CLI — install, update, and manage skillsets across all agents",
    "geno-dev": "Developer utilities — commits, worktrees, workspaces, feature shipping",
    "geno-agents": "Multi-agent coordination, registration, autonomous loops",
    "geno-notes": "Project journal, task management, wiki, and site generation",
    "geno-loops": "Agentic execution loop patterns — cruise, turbocharge, autopilot",
    "geno-kaggle": "Kaggle benchmarking, notebook upload, discussion scraping",
    "geno-research": "Wiki-based research, paper generation, repo documentation",
    "geno-iso": "Docker containers for isolated Claude Code environments",
    "geno-mine": "Session mining — extract, analyze, and export agent session data",
    "geno-specs": "Execution specifications — create, validate, run, and review",
    "geno-career": "Career toolkit — job search, resume building, application tracking",
    "geno-audit": "Ecosystem compliance auditor",
    "geno-mon": "Agent observability and monitoring",
    "geno-msg": "Inter-agent messaging",
    "geno-term": "Terminal automation and session recovery",
    "geno-ws": "Workspace management",
    "geno-voice": "Voice pipeline",
    "geno-media": "Audiobooks, animated videos, podcasts, TTS/STT config",
    "geno-taxes": "Tax filing — document parsing, checklists, CPA packet prep",
    "geno-budget": "Personal budget and expense categorization",
    "geno-hoa": "HOA portal automation",
    "geno-remodel": "Home remodel toolkit",
}

CATEGORY_MAP: dict[str, str] = {
    "geno-tools": "core",
    "geno-agents": "core",
    "geno-msg": "core",
    "geno-notes": "core",
    "geno-mon": "core",
    "geno-dev": "developer",
    "geno-loops": "developer",
    "geno-specs": "developer",
    "geno-iso": "runtime",
    "geno-term": "runtime",
    "geno-ws": "runtime",
    "geno-mine": "tooling",
    "geno-audit": "tooling",
    "geno-kaggle": "data",
    "geno-research": "data",
    "geno-media": "creative",
    "geno-voice": "creative",
    "geno-career": "life",
    "geno-taxes": "life",
    "geno-budget": "life",
    "geno-hoa": "life",
    "geno-remodel": "life",
}

CATEGORY_LABELS: dict[str, tuple[str, str]] = {
    "core": ("Core", ":material-cube-outline:"),
    "developer": ("Developer", ":material-code-braces:"),
    "runtime": ("Runtime", ":material-cog-outline:"),
    "tooling": ("Tooling", ":material-wrench-outline:"),
    "data": ("Data & Research", ":material-chart-bar:"),
    "creative": ("Creative", ":material-palette-outline:"),
    "life": ("Life", ":material-home-outline:"),
}


@dataclass
class SkillInfo:
    name: str
    skillset: str
    description: str = ""
    frontmatter: dict = field(default_factory=dict)
    body: str = ""
    source_path: Path | None = None
    is_umbrella: bool = False


@dataclass
class SkillsetInfo:
    name: str
    description: str = ""
    category: str = "tooling"
    skills: list[SkillInfo] = field(default_factory=list)
    geno_md: str = ""
    repo_url: str = ""


def parse_skill_md(path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter and markdown body from a SKILL.md file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}, text

    end = text.find("---", 3)
    if end == -1:
        return {}, text

    frontmatter_str = text[3:end].strip()
    body = text[end + 3 :].strip()

    fm: dict = {}
    current_key = None
    current_val_lines: list[str] = []

    for line in frontmatter_str.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue

        top_match = re.match(r"^(\w[\w-]*):\s*(.*)", line)
        if top_match and not line[0].isspace():
            if current_key is not None:
                val = "\n".join(current_val_lines).strip()
                if val.startswith(">-"):
                    val = val[2:].strip()
                elif val.startswith(">"):
                    val = val[1:].strip()
                val = re.sub(r"\s+", " ", val).strip()
                fm[current_key] = val
            current_key = top_match.group(1)
            current_val_lines = [top_match.group(2)]
        elif current_key is not None:
            current_val_lines.append(stripped)

    if current_key is not None:
        val = "\n".join(current_val_lines).strip()
        if val.startswith(">-"):
            val = val[2:].strip()
        elif val.startswith(">"):
            val = val[1:].strip()
        val = re.sub(r"\s+", " ", val).strip()
        fm[current_key] = val

    return fm, body


def extract_description(fm: dict, body: str) -> str:
    """Extract a clean one-line description from frontmatter or body."""
    desc = fm.get("description", "")
    if desc:
        first_sentence = desc.split(".")[0].split(" — ")[0].split(" - ")[0]
        first_sentence = re.sub(
            r"Use when user says.*", "", first_sentence
        ).strip()
        first_sentence = re.sub(r"TRIGGER when:.*", "", first_sentence).strip()
        if len(first_sentence) > 120:
            first_sentence = first_sentence[:117] + "..."
        return first_sentence

    for line in body.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("|"):
            return line[:120]

    return ""


def discover_skillsets(
    workspace_root: Path, install_dir: Path
) -> dict[str, SkillsetInfo]:
    """Discover all skillsets from workspace repos and installed directory."""
    skillsets: dict[str, SkillsetInfo] = {}
    seen_skills: set[str] = set()

    ws_dirs = sorted(workspace_root.glob("geno-*-ws"))
    for ws_dir in ws_dirs:
        repo_name = ws_dir.name.replace("-ws", "")
        repo_dir = ws_dir / repo_name
        skills_dir = repo_dir / "skills"
        if not skills_dir.is_dir():
            continue

        ss = SkillsetInfo(
            name=repo_name,
            description=REPO_DESCRIPTIONS.get(repo_name, ""),
            category=CATEGORY_MAP.get(repo_name, "tooling"),
            repo_url=f"https://github.com/42euge/{repo_name}",
        )

        geno_path = repo_dir / "GENO.md"
        if geno_path.is_file():
            ss.geno_md = geno_path.read_text(encoding="utf-8", errors="replace")

        for skill_dir in sorted(skills_dir.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue

            fm, body = parse_skill_md(skill_md)
            skill_name = fm.get("name", skill_dir.name)
            if skill_name in seen_skills:
                continue
            seen_skills.add(skill_name)

            is_umbrella = skill_name == repo_name

            si = SkillInfo(
                name=skill_name,
                skillset=repo_name,
                description=extract_description(fm, body),
                frontmatter=fm,
                body=body,
                source_path=skill_md,
                is_umbrella=is_umbrella,
            )
            ss.skills.append(si)

        if ss.skills:
            skillsets[repo_name] = ss

    local_ws = workspace_root / "geno-tools-ws"
    for repo_dir in sorted(local_ws.iterdir()):
        if not repo_dir.is_dir() or repo_dir.name.startswith("."):
            continue
        skills_dir = repo_dir / "skills"
        if not skills_dir.is_dir():
            continue

        repo_name = repo_dir.name
        if repo_name in skillsets:
            continue

        ss = SkillsetInfo(
            name=repo_name,
            description=REPO_DESCRIPTIONS.get(repo_name, ""),
            category=CATEGORY_MAP.get(repo_name, "tooling"),
            repo_url=f"https://github.com/42euge/{repo_name}",
        )

        geno_path = repo_dir / "GENO.md"
        if geno_path.is_file():
            ss.geno_md = geno_path.read_text(encoding="utf-8", errors="replace")

        for skill_dir in sorted(skills_dir.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue

            fm, body = parse_skill_md(skill_md)
            skill_name = fm.get("name", skill_dir.name)
            if skill_name in seen_skills:
                continue
            seen_skills.add(skill_name)

            si = SkillInfo(
                name=skill_name,
                skillset=repo_name,
                description=extract_description(fm, body),
                frontmatter=fm,
                body=body,
                source_path=skill_md,
                is_umbrella=(skill_name == repo_name),
            )
            ss.skills.append(si)

        if ss.skills:
            skillsets[repo_name] = ss

    for ss_dir in sorted(install_dir.glob("geno-*")):
        active = ss_dir / "active" / "skills"
        if not active.is_dir():
            continue

        repo_name = ss_dir.name
        if repo_name in skillsets:
            continue

        ss = SkillsetInfo(
            name=repo_name,
            description=REPO_DESCRIPTIONS.get(repo_name, ""),
            category=CATEGORY_MAP.get(repo_name, "tooling"),
            repo_url=f"https://github.com/42euge/{repo_name}",
        )

        geno_path = ss_dir / "active" / "GENO.md"
        if geno_path.is_file():
            ss.geno_md = geno_path.read_text(encoding="utf-8", errors="replace")

        for skill_dir in sorted(active.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue

            fm, body = parse_skill_md(skill_md)
            skill_name = fm.get("name", skill_dir.name)
            if skill_name in seen_skills:
                continue
            seen_skills.add(skill_name)

            si = SkillInfo(
                name=skill_name,
                skillset=repo_name,
                description=extract_description(fm, body),
                frontmatter=fm,
                body=body,
                source_path=skill_md,
                is_umbrella=(skill_name == repo_name),
            )
            ss.skills.append(si)

        if ss.skills:
            skillsets[repo_name] = ss

    return skillsets


def generate_catalog_page(skillsets: dict[str, SkillsetInfo]) -> str:
    """Generate the main skill catalog page (Level 1-2)."""
    total_skills = sum(
        len([s for s in ss.skills if not s.is_umbrella]) for ss in skillsets.values()
    )
    total_skillsets = len(skillsets)

    lines = [
        "---",
        "title: Skill Catalog",
        "description: Browse all skills in the geno ecosystem",
        "---",
        "",
        "# Skill Catalog",
        "",
        f"**{total_skillsets} skillsets** · **{total_skills} skills** across the geno ecosystem.",
        "",
        "Browse by category, search for a skill, or drill into any skillset for full documentation.",
        "",
    ]

    by_cat: dict[str, list[SkillsetInfo]] = defaultdict(list)
    for ss in skillsets.values():
        by_cat[ss.category].append(ss)

    for cat_key in CATEGORY_LABELS:
        cat_skillsets = by_cat.get(cat_key, [])
        if not cat_skillsets:
            continue

        label, icon = CATEGORY_LABELS[cat_key]
        lines.append(f"## {icon} {label}")
        lines.append("")
        lines.append('<div class="feature-grid" markdown>')
        lines.append("")

        for ss in sorted(cat_skillsets, key=lambda s: s.name):
            sub_skills = [s for s in ss.skills if not s.is_umbrella]
            skill_count = len(sub_skills)
            desc = ss.description or "No description"
            slug = ss.name

            lines.append('<div class="feature-card" markdown>')
            lines.append("")
            lines.append(f"### [{ss.name}]({slug}/index.md)")
            lines.append("")
            lines.append(f"{desc}")
            lines.append("")
            if skill_count > 0:
                lines.append(
                    f'<span class="skill-count">{skill_count} skill{"s" if skill_count != 1 else ""}</span>'
                )
                lines.append("")
            lines.append("</div>")
            lines.append("")

        lines.append("</div>")
        lines.append("")

    lines.append("## All skills")
    lines.append("")
    lines.append("| Skill | Skillset | Description |")
    lines.append("|-------|----------|-------------|")

    all_skills: list[SkillInfo] = []
    for ss in skillsets.values():
        for skill in ss.skills:
            if not skill.is_umbrella:
                all_skills.append(skill)

    for skill in sorted(all_skills, key=lambda s: s.name):
        slug = skill.skillset
        link = f"[`{skill.name}`]({slug}/index.md#{skill.name})"
        ss_link = f"[{skill.skillset}]({slug}/index.md)"
        desc = skill.description or "—"
        lines.append(f"| {link} | {ss_link} | {desc} |")

    lines.append("")
    return "\n".join(lines)


def generate_skillset_page(ss: SkillsetInfo) -> str:
    """Generate a per-skillset page with zoom levels (Level 3-4)."""
    sub_skills = [s for s in ss.skills if not s.is_umbrella]
    umbrella = next((s for s in ss.skills if s.is_umbrella), None)

    lines = [
        "---",
        f"title: {ss.name}",
        f"description: {ss.description}",
        "---",
        "",
        f"# {ss.name}",
        "",
        f"{ss.description}",
        "",
    ]

    if ss.repo_url:
        lines.append(
            f"[:material-github: GitHub]({ss.repo_url}){{ .md-button }}"
        )
        lines.append("")

    if sub_skills:
        lines.append("## Skills")
        lines.append("")
        lines.append("| Skill | Slash command | Description |")
        lines.append("|-------|--------------|-------------|")
        for skill in sorted(sub_skills, key=lambda s: s.name):
            slash = f"`/{skill.name}`"
            desc = skill.description or "—"
            anchor = skill.name
            lines.append(
                f"| [{skill.name}](#{anchor}) | {slash} | {desc} |"
            )
        lines.append("")

    if umbrella and umbrella.body:
        lines.append("## Overview")
        lines.append("")
        lines.append(
            '??? abstract "Skillset overview (from SKILL.md)"'
        )
        lines.append("")
        for bline in umbrella.body.split("\n"):
            lines.append(f"    {bline}")
        lines.append("")

    for skill in sorted(sub_skills, key=lambda s: s.name):
        lines.append(f"## {skill.name}")
        lines.append("")
        lines.append(f"**Slash command:** `/{skill.name}`")
        lines.append("")

        if skill.description:
            lines.append(f"> {skill.description}")
            lines.append("")

        obs = skill.frontmatter.get("observability", "")
        if obs:
            lines.append(
                '??? info "Observability"'
            )
            lines.append("")
            lines.append(f"    {obs}")
            lines.append("")

        if skill.body:
            heading_stripped = _strip_leading_h1(skill.body)
            lines.append(
                f'??? example "Full skill definition (Level 4)"'
            )
            lines.append("")
            for bline in heading_stripped.split("\n"):
                lines.append(f"    {bline}")
            lines.append("")

    return "\n".join(lines)


def _strip_leading_h1(body: str) -> str:
    """Remove a leading H1 heading if present (it duplicates the section title)."""
    body_lines = body.split("\n")
    for i, line in enumerate(body_lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# ") and not stripped.startswith("## "):
            return "\n".join(body_lines[i + 1 :]).lstrip("\n")
        break
    return body


def generate_ecosystem_overview(skillsets: dict[str, SkillsetInfo]) -> str:
    """Generate the updated ecosystem page with skill counts."""
    total_skills = sum(
        len([s for s in ss.skills if not s.is_umbrella]) for ss in skillsets.values()
    )
    total_skillsets = len(skillsets)

    lines = [
        "---",
        "title: Ecosystem",
        "description: The geno-* ecosystem at a glance",
        "---",
        "",
        "# Ecosystem",
        "",
        f"The geno ecosystem spans **{total_skillsets} skillsets** and **{total_skills} skills**.",
        "",
        "Browse the full [Skill Catalog](skills/index.md) or explore individual skillsets below.",
        "",
        "## Skillsets",
        "",
        "| Skillset | Category | Skills | Description |",
        "|----------|----------|--------|-------------|",
    ]

    for ss in sorted(skillsets.values(), key=lambda s: s.name):
        cat_label, cat_icon = CATEGORY_LABELS.get(
            ss.category, ("Other", ":material-help:")
        )
        sub_count = len([s for s in ss.skills if not s.is_umbrella])
        desc = ss.description or "—"
        lines.append(
            f"| [{ss.name}](skills/{ss.name}/index.md) | {cat_icon} {cat_label} | {sub_count} | {desc} |"
        )

    lines.append("")
    lines.append("## Architecture")
    lines.append("")
    lines.append("```")
    lines.append(
        textwrap.dedent("""\
              ┌──────────────────────────────────────┐
              │          geno-tools                   │
              │    (meta package manager)             │
              └──────────────┬───────────────────────-┘
                             │
        discover ──→ absorb ──→ evaluate ──→ govern ──→ evolve
           │            │          │            │          │
      registry.py    install    fork/use    geno-audit  promote
      discovery.py   normalize  worktrees   audit.md    merge → main
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         geno-<name>   geno-<name>   geno-<name>  ...
              │              │              │
              └──────────────┼──────────────┘
                             │
                       Coding CLIs
           (Claude Code, Codex, Gemini CLI, Cursor, OpenCode)
                             │
                  geno-agents (coordination)
                  geno-msg    (messaging)
                  geno-notes  (project state)
                  geno-mon    (monitoring)""")
    )
    lines.append("```")
    lines.append("")
    lines.append(
        "Each skillset is independent — install only what you need. "
        "The coordination layer (agents, msg, notes, mon) is optional "
        "but enables multi-agent workflows."
    )
    lines.append("")

    return "\n".join(lines)


def compile_docs(
    workspace_root: Path, install_dir: Path, output_dir: Path
) -> None:
    """Main entry point: discover skills and generate all docs pages."""
    print(f"Discovering skillsets from {workspace_root} and {install_dir}...")
    skillsets = discover_skillsets(workspace_root, install_dir)

    total_skills = sum(len(ss.skills) for ss in skillsets.values())
    print(f"Found {len(skillsets)} skillsets with {total_skills} total skills.")

    output_dir.mkdir(parents=True, exist_ok=True)

    catalog = generate_catalog_page(skillsets)
    catalog_path = output_dir / "index.md"
    catalog_path.write_text(catalog, encoding="utf-8")
    print(f"  Wrote {catalog_path}")

    for ss in skillsets.values():
        ss_dir = output_dir / ss.name
        ss_dir.mkdir(parents=True, exist_ok=True)
        page = generate_skillset_page(ss)
        page_path = ss_dir / "index.md"
        page_path.write_text(page, encoding="utf-8")
        print(f"  Wrote {page_path}")

    eco_page = generate_ecosystem_overview(skillsets)
    eco_path = output_dir.parent / "ecosystem.md"
    eco_path.write_text(eco_page, encoding="utf-8")
    print(f"  Wrote {eco_path}")

    print("Done.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=WORKSPACE_ROOT,
        help="Root directory containing geno-*-ws workspace dirs",
    )
    parser.add_argument(
        "--install-dir",
        type=Path,
        default=INSTALL_DIR,
        help="geno-tools install directory (~/.geno-tools)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for generated docs (docs/skills/)",
    )
    args = parser.parse_args()
    compile_docs(args.workspace, args.install_dir, args.output)


if __name__ == "__main__":
    main()
