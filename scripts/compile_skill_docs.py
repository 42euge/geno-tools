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
        active_dir = ss_dir / "active"
        if not active_dir.is_dir():
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

        geno_path = active_dir / "GENO.md"
        if geno_path.is_file():
            ss.geno_md = geno_path.read_text(encoding="utf-8", errors="replace")

        root_skill = active_dir / "SKILL.md"
        if root_skill.is_file():
            fm, body = parse_skill_md(root_skill)
            skill_name = fm.get("name", repo_name)
            if skill_name not in seen_skills:
                seen_skills.add(skill_name)
                si = SkillInfo(
                    name=skill_name,
                    skillset=repo_name,
                    description=extract_description(fm, body),
                    frontmatter=fm,
                    body=body,
                    source_path=root_skill,
                    is_umbrella=(skill_name == repo_name),
                )
                ss.skills.append(si)

        active_skills = active_dir / "skills"
        if active_skills.is_dir():
            for skill_dir in sorted(active_skills.iterdir()):
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

    cat_labels_list = [label for label, _ in CATEGORY_LABELS.values()]

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
        '<div class="catalog-filter" markdown>',
        '  <input type="text" id="skill-search" placeholder="Filter skills..." />',
    ]
    lines.append('  <button class="filter-btn active" data-cat="all">All</button>')
    for cat_key, (label, _) in CATEGORY_LABELS.items():
        lines.append(f'  <button class="filter-btn" data-cat="{cat_key}">{label}</button>')
    lines.extend([
        "</div>",
        '<p class="catalog-no-results" id="no-results">No skills match your filter.</p>',
        "",
    ])

    by_cat: dict[str, list[SkillsetInfo]] = defaultdict(list)
    for ss in skillsets.values():
        by_cat[ss.category].append(ss)

    for cat_key in CATEGORY_LABELS:
        cat_skillsets = by_cat.get(cat_key, [])
        if not cat_skillsets:
            continue

        label, icon = CATEGORY_LABELS[cat_key]
        lines.append(f'<div class="catalog-category" data-cat="{cat_key}" markdown>')
        lines.append("")
        lines.append(f"## {icon} {label}")
        lines.append("")
        lines.append('<div class="feature-grid" markdown>')
        lines.append("")

        for ss in sorted(cat_skillsets, key=lambda s: s.name):
            sub_skills = [s for s in ss.skills if not s.is_umbrella]
            skill_count = len(sub_skills)
            desc = ss.description or "No description"
            slug = ss.name
            skill_names = " ".join(s.name for s in sub_skills)

            lines.append(f'<div class="feature-card" data-skills="{skill_names}" markdown>')
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
        lines.append("</div>")
        lines.append("")

    lines.append('<div class="catalog-all-skills" markdown>')
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
        link = f"[`{skill.name}`]({slug}/{skill.name}.md)"
        ss_link = f"[{skill.skillset}]({slug}/index.md)"
        desc = skill.description or "—"
        lines.append(f"| {link} | {ss_link} | {desc} |")

    lines.append("")
    lines.append("</div>")
    lines.append("")
    return "\n".join(lines)


def _extract_overview_sections(body: str) -> str:
    """Extract Level 3 overview from skill body.

    Pulls Input, When to Use, Usage, and Prerequisites sections —
    everything useful for understanding without the full workflow.
    """
    heading_stripped = _strip_leading_h1(body)
    overview_headings = {"input", "when to use", "usage", "prerequisites", "options"}
    stop_headings = {"workflow", "don'ts", "what not to do", "error recovery", "runtime"}

    sections: list[str] = []
    current_section: list[str] = []
    in_overview_section = False
    found_any = False

    for line in heading_stripped.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            heading_text = stripped[3:].strip().lower()
            if in_overview_section and current_section:
                sections.append("\n".join(current_section))
                current_section = []

            if heading_text in overview_headings:
                in_overview_section = True
                found_any = True
                current_section = [line]
            elif heading_text in stop_headings:
                in_overview_section = False
            else:
                in_overview_section = False
        elif in_overview_section:
            current_section.append(line)

    if in_overview_section and current_section:
        sections.append("\n".join(current_section))

    if not found_any:
        para_lines: list[str] = []
        for line in heading_stripped.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#"):
                break
            para_lines.append(line)
        intro = "\n".join(para_lines).strip()
        if intro:
            return intro

    return "\n\n".join(sections).strip()


def _generate_rationale(skill: SkillInfo) -> str:
    """Generate Level 5 rationale content for a skill.

    Returns a short explanation of WHY the skill is structured the way it is,
    cross-references to related skills, and LLM behavior patterns it addresses.
    For now, generates heuristic rationale from the skill body; a future pass
    can enrich this with Claude API calls.
    """
    lines: list[str] = []

    related = _find_related_skills(skill)
    if related:
        lines.append("**Related skills:** " + ", ".join(f"`{r}`" for r in related))
        lines.append("")

    has_error_recovery = any(
        h in skill.body.lower()
        for h in ["error recovery", "fallback", "if.*fails"]
    )
    has_donts = any(
        h in skill.body.lower()
        for h in ["don't", "do not", "what not to do", "never"]
    )
    has_observability = "geno-trace" in skill.body or "observability" in str(skill.frontmatter)

    if has_error_recovery:
        lines.append(
            "- **Error recovery section** — LLMs can get stuck in retry loops "
            "or abandon tasks on first failure. Explicit fallback steps prevent both."
        )
    if has_donts:
        lines.append(
            "- **Explicit don'ts** — negative constraints are crucial for LLM-driven "
            "workflows. Without them, agents drift toward plausible-but-wrong approaches."
        )
    if has_observability:
        lines.append(
            "- **Observability contract** — emitting traces at completion feeds the "
            "self-improvement loop (health cards, retro, mining)."
        )

    if not lines:
        lines.append(
            "*Rationale not yet generated. Run `geno-docs compile --rationale` "
            "to generate LLM explanations for this skill.*"
        )

    return "\n".join(lines)


def _find_related_skills(skill: SkillInfo) -> list[str]:
    """Find skill names referenced in the body text."""
    matches = re.findall(r"/geno-[\w-]+", skill.body)
    names = sorted(set(m.lstrip("/") for m in matches if m.lstrip("/") != skill.name))
    return names[:5]


def _generate_skill_page(skill: SkillInfo) -> str:
    """Generate a standalone skill page with progressive scroll depth."""
    lines: list[str] = []
    desc = skill.description or skill.name

    lines.append("---")
    lines.append(f"title: {skill.name}")
    lines.append(f"description: {desc}")
    lines.append("---")
    lines.append("")

    # L1-2: Name + description (visible on landing)
    lines.append(f"# {skill.name}")
    lines.append("")
    arg_hint = skill.frontmatter.get("argument-hint", "")
    if arg_hint:
        lines.append(f"`/{skill.name} {arg_hint}`")
    else:
        lines.append(f"`/{skill.name}`")
    lines.append("")
    lines.append(f"> {desc}")
    lines.append("")

    lines.append('<div class="zoom-depth" markdown>')
    lines.append("")

    if skill.body:
        # L3: Overview — scroll deeper
        overview = _extract_overview_sections(skill.body)
        if overview:
            lines.append('<div class="zoom-section zoom-section-3" markdown>')
            lines.append("")
            for oline in overview.split("\n"):
                lines.append(oline)
            lines.append("")
            lines.append("</div>")
            lines.append("")

        # L4: Deep content — workflow, error recovery, don'ts (excludes L3 sections)
        deep = _extract_deep_sections(skill.body)
        if deep:
            lines.append('<div class="zoom-section zoom-section-4" markdown>')
            lines.append("")
            lines.append("---")
            lines.append("")
            for bline in deep.split("\n"):
                lines.append(bline)
            lines.append("")
            lines.append("</div>")
            lines.append("")

        # L5: Rationale — bottom of page
        rationale = _generate_rationale(skill)
        lines.append('<div class="zoom-section zoom-section-5" markdown>')
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("### Rationale")
        lines.append("")
        for rline in rationale.split("\n"):
            lines.append(rline)
        lines.append("")
        lines.append("</div>")
        lines.append("")

    lines.append("</div>")
    lines.append("")

    # Back link
    lines.append(f"[:material-arrow-left: Back to {skill.skillset}](index.md)")
    lines.append("")

    return "\n".join(lines)


def generate_skillset_page(ss: SkillsetInfo) -> str:
    """Generate a per-skillset index page linking to individual skill pages."""
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
            lines.append(
                f"| [{skill.name}]({skill.name}.md) | {slash} | {desc} |"
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

    return "\n".join(lines)


def _extract_deep_sections(body: str) -> str:
    """Extract Level 4 content: everything beyond the overview sections.

    Strips the overview headings (Input, When to Use, Usage, Prerequisites)
    to avoid repetition with Level 3 in progressive scroll.
    """
    heading_stripped = _strip_leading_h1(body)
    overview_headings = {"input", "when to use", "usage", "prerequisites", "options"}

    result: list[str] = []
    skip = False
    intro_done = False

    for line in heading_stripped.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            heading_text = stripped[3:].strip().lower()
            if heading_text in overview_headings:
                skip = True
                intro_done = True
                continue
            else:
                skip = False
                intro_done = True
        elif not intro_done and not stripped.startswith("#"):
            skip = True
            continue

        if not skip:
            result.append(line)

    text = "\n".join(result).strip()
    return text if text else heading_stripped


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


def generate_nav_yaml(skillsets: dict[str, SkillsetInfo]) -> str:
    """Generate the Skills Catalog nav section for mkdocs.yml."""
    by_cat: dict[str, list[SkillsetInfo]] = defaultdict(list)
    for ss in skillsets.values():
        by_cat[ss.category].append(ss)

    lines = [
        "  - Skills Catalog:",
        "      - skills/index.md",
    ]

    for cat_key in CATEGORY_LABELS:
        cat_skillsets = by_cat.get(cat_key, [])
        if not cat_skillsets:
            continue
        label, _ = CATEGORY_LABELS[cat_key]
        lines.append(f"      - {label}:")
        for ss in sorted(cat_skillsets, key=lambda s: s.name):
            sub_skills = [s for s in ss.skills if not s.is_umbrella]
            if sub_skills:
                lines.append(f"          - {ss.name}:")
                lines.append(f"              - skills/{ss.name}/index.md")
                for skill in sorted(sub_skills, key=lambda s: s.name):
                    lines.append(
                        f"              - {skill.name}: skills/{ss.name}/{skill.name}.md"
                    )
            else:
                lines.append(f"          - {ss.name}: skills/{ss.name}/index.md")

    return "\n".join(lines)


def compile_docs(
    workspace_root: Path, install_dir: Path, output_dir: Path,
    update_nav: bool = False,
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

    skill_page_count = 0
    for ss in skillsets.values():
        ss_dir = output_dir / ss.name
        ss_dir.mkdir(parents=True, exist_ok=True)

        page = generate_skillset_page(ss)
        page_path = ss_dir / "index.md"
        page_path.write_text(page, encoding="utf-8")
        print(f"  Wrote {page_path}")

        sub_skills = [s for s in ss.skills if not s.is_umbrella]
        for skill in sub_skills:
            skill_page = _generate_skill_page(skill)
            skill_path = ss_dir / f"{skill.name}.md"
            skill_path.write_text(skill_page, encoding="utf-8")
            skill_page_count += 1

    print(f"  Generated {skill_page_count} individual skill pages")

    eco_page = generate_ecosystem_overview(skillsets)
    eco_path = output_dir.parent / "ecosystem.md"
    eco_path.write_text(eco_page, encoding="utf-8")
    print(f"  Wrote {eco_path}")

    if update_nav:
        nav_yaml = generate_nav_yaml(skillsets)
        print("\n--- Generated nav section (paste into mkdocs.yml) ---")
        print(nav_yaml)
        print("--- end ---")

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
    parser.add_argument(
        "--update-nav",
        action="store_true",
        help="Print the generated nav YAML for mkdocs.yml",
    )
    args = parser.parse_args()
    compile_docs(args.workspace, args.install_dir, args.output, args.update_nav)


if __name__ == "__main__":
    main()
