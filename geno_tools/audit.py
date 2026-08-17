"""Ecosystem compliance auditor — the engine behind `geno-tools audit`.

Programmatic version of the audit/run skill: checks a geno-* repo against the
skillset conventions in tiers — FAIL (required, blocks install), WARN
(recommended), INFO (advisory, e.g. the library-first convention). Returns a
list of (level, check, detail) results.
"""

import re
import tomllib
from pathlib import Path

import yaml


def _frontmatter(path: Path) -> dict:
    try:
        text = path.read_text()
        if text.startswith("---"):
            return yaml.safe_load(text.split("---", 2)[1]) or {}
    except (OSError, yaml.YAMLError, IndexError):
        pass
    return {}


def _cli_subcommand_count(root: Path, scripts: dict) -> int:
    """Heuristic subcommand count from the CLI entry module (argparse/click/typer)."""
    if not scripts:
        return 0
    module = next(iter(scripts.values())).split(":")[0]
    f = root / (module.replace(".", "/") + ".py")
    if not f.exists():
        return 0
    src = f.read_text()
    decorated = len(re.findall(r"add_parser\(|@\w+\.command\b|\.add_command\(", src))
    flat = len(re.findall(r'cmd == "', src))  # geno-tt-style flat dispatch
    return max(decorated, flat)


def audit(path: str) -> list[tuple[str, str, str]]:
    root = Path(path or ".").resolve()
    out: list[tuple[str, str, str]] = []
    def add(level, check, detail=""):
        out.append((level, check, detail))

    # ── manifest (required) ──
    gt = root / "genotools.yaml"
    manifest = {}
    if not gt.exists():
        add("FAIL", "genotools.yaml present", "missing — not installable by geno-tools")
    else:
        try:
            manifest = yaml.safe_load(gt.read_text()) or {}
        except yaml.YAMLError as e:
            add("FAIL", "genotools.yaml parses", str(e))
        add("OK" if manifest.get("name") else "FAIL", "manifest name",
            manifest.get("name", "missing"))
    mver = str(manifest.get("version", ""))
    add("OK" if re.match(r"^\d+\.\d+\.\d+", mver) else "FAIL",
        "manifest version is semver", mver or "missing")

    # ── version consistency (required where present) ──
    def ver_check(label, got):
        got = str(got or "")
        if got and mver and got != mver:
            add("FAIL", f"{label} version == manifest", f"{got} != {mver}")
        elif got:
            add("OK", f"{label} version", got)

    scripts, lib = {}, False
    pj = root / "pyproject.toml"
    if pj.exists():
        try:
            proj = tomllib.loads(pj.read_text()).get("project", {})
            ver_check("pyproject", proj.get("version"))
            scripts = proj.get("scripts", {})
            lib = True
        except tomllib.TOMLDecodeError as e:
            add("WARN", "pyproject.toml parses", str(e))
    pkg_init = root / root.name.replace("-", "_") / "__init__.py"
    if pkg_init.exists():
        m = re.search(r'__version__\s*=\s*["\']([^"\']+)', pkg_init.read_text())
        if m:
            ver_check("__init__", m.group(1))

    # ── umbrella skill (required) ──
    sk = root / "SKILL.md"
    if not sk.exists():
        add("FAIL", "umbrella SKILL.md present", "missing")
    else:
        fm = _frontmatter(sk)
        add("OK" if fm.get("name") else "FAIL", "umbrella SKILL.md name",
            fm.get("name", "missing"))
        ver_check("SKILL.md", (fm.get("metadata") or {}).get("version"))

    # ── skills structure (required) ──
    leaf_skills = 0
    skills = root / "skills"
    if skills.is_dir():
        for d in sorted(skills.rglob("*")):
            if d.is_dir() and not any(c.is_dir() for c in d.iterdir()):  # leaf dir
                if (d / "SKILL.md").exists():
                    leaf_skills += 1
                else:
                    add("FAIL", "skill leaf has SKILL.md", str(d.relative_to(root)))

    # ── monolithic-CLI check (required) ──
    subn = _cli_subcommand_count(root, scripts)
    if subn >= 3 and leaf_skills < 2:
        add("FAIL", "CLI subcommands have sub-skills",
            f"{subn} CLI subcommands but only {leaf_skills} sub-skill dir(s)")
    elif subn:
        add("OK", "CLI ↔ sub-skills", f"{subn} subcommands · {leaf_skills} sub-skills")

    # ── library-first convention (advisory) ──
    add("INFO", "library-capable (importable package)",
        "yes" if lib else "no — skill-only (add a package to compose it)")

    # ── recommended docs / plugin ──
    add("OK" if (root / "AGENTS.md").exists() else "WARN",
        "AGENTS.md (single source of truth)")
    for f in ("GENO.md", "CLAUDE.md", "GEMINI.md"):
        if (root / f).exists():
            add("WARN", f"{f} is retired — fold it into AGENTS.md")
    add("OK" if (root / ".claude-plugin" / "plugin.json").exists() else "INFO",
        "Claude Code plugin manifest")

    return out
