"""Deterministic compliance checks for geno skillset repositories."""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml


REQUIRED_RULE_IDS = (
    "GENO-001",
    "GENO-002",
    "GENO-003",
    "GENO-004",
    "GENO-005",
    "GENO-006",
    "GENO-007",
    "GENO-010",
    "GENO-011",
    "GENO-012",
    "GENO-013",
    "GENO-014",
    "GENO-015",
    "GENO-020",
    "GENO-021",
    "GENO-022",
)

RECOMMENDED_RULE_IDS = (
    "GENO-101",
    "GENO-102",
    "GENO-103",
    "GENO-104",
    "GENO-105",
    "GENO-106",
    "GENO-107",
    "GENO-108",
    "GENO-109",
    "GENO-110",
)

RULE_IDS = REQUIRED_RULE_IDS + RECOMMENDED_RULE_IDS

_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
_REPO_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*-[a-z0-9][a-z0-9-]*$")
_TRIGGER_PREFIXES = ("use when", "use for", "use if")
_TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".yaml", ".yml"}


@dataclass(frozen=True)
class CheckResult:
    rule_id: str
    status: str
    message: str
    path: str | None = None
    remediation: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AuditReport:
    target: str
    results: tuple[CheckResult, ...]

    @property
    def verdict(self) -> str:
        if any(result.status == "FAIL" for result in self.results):
            return "FAIL"
        if any(result.status == "WARN" for result in self.results):
            return "WARN"
        return "PASS"

    @property
    def counts(self) -> dict[str, int]:
        return {
            status: sum(result.status == status for result in self.results)
            for status in ("PASS", "FAIL", "WARN", "INFO")
        }

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "verdict": self.verdict,
            "counts": self.counts,
            "results": [result.to_dict() for result in self.results],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def audit_skillset(
    path: str | Path, *, repository_name: str | None = None
) -> AuditReport:
    """Audit one local skillset checkout without modifying it."""
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")

    results: list[CheckResult] = []
    repo_name = repository_name or root.name
    manifest, manifest_error = _load_yaml_mapping(root / "genotools.yaml")
    skill_files = sorted((root / "skills").glob("**/SKILL.md"))
    skill_data = {path: _frontmatter(path) for path in skill_files}
    umbrella = root / "skills" / repo_name / "SKILL.md"

    def required(
        rule_id: str,
        passed: bool,
        message: str,
        *,
        path: str | Path | None = None,
        remediation: str | None = None,
    ) -> None:
        results.append(
            CheckResult(
                rule_id,
                "PASS" if passed else "FAIL",
                message,
                _relative(root, path),
                None if passed else remediation,
            )
        )

    def recommended(
        rule_id: str,
        passed: bool,
        message: str,
        *,
        path: str | Path | None = None,
        remediation: str | None = None,
    ) -> None:
        results.append(
            CheckResult(
                rule_id,
                "PASS" if passed else "WARN",
                message,
                _relative(root, path),
                None if passed else remediation,
            )
        )

    # Repository and manifest.
    valid_repo_name = bool(_REPO_NAME.fullmatch(repo_name))
    required(
        "GENO-001",
        valid_repo_name,
        f"repository name: {repo_name}",
        remediation="Rename the repository to {namespace}-{slug}.",
    )
    required(
        "GENO-002",
        manifest_error is None,
        "genotools.yaml is a YAML mapping" if manifest_error is None else manifest_error,
        path="genotools.yaml",
        remediation="Create or repair the root genotools.yaml mapping.",
    )
    identity_errors = []
    for field in ("name", "version", "description"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            identity_errors.append(f"missing {field}")
    if manifest.get("name") and manifest.get("name") != repo_name:
        identity_errors.append(f"name {manifest['name']!r} != {repo_name!r}")
    required(
        "GENO-003",
        not identity_errors,
        "manifest identity matches repository" if not identity_errors else "; ".join(identity_errors),
        path="genotools.yaml",
        remediation="Set non-empty name, version, and description fields; make name match the repository.",
    )
    manifest_version = str(manifest.get("version", ""))
    required(
        "GENO-004",
        bool(_SEMVER.fullmatch(manifest_version)),
        f"manifest version: {manifest_version or 'missing'}",
        path="genotools.yaml",
        remediation="Use a semantic MAJOR.MINOR.PATCH version.",
    )
    requirements = manifest.get("requires", [])
    requirements_valid = (
        requirements is None
        or (
            isinstance(requirements, list)
            and all(isinstance(item, str) and item.strip() for item in requirements)
            and repo_name not in requirements
        )
    )
    required(
        "GENO-005",
        requirements_valid,
        "dependencies are a valid list without self-reference",
        path="genotools.yaml",
        remediation="Make requires a list of non-empty skillset names and remove self-references.",
    )
    missing_sources = _missing_manifest_sources(root, manifest)
    required(
        "GENO-006",
        not missing_sources,
        "all declared source paths exist" if not missing_sources else f"missing: {', '.join(missing_sources)}",
        path="genotools.yaml",
        remediation="Add the missing source paths or remove their manifest entries.",
    )

    project, project_error = _load_pyproject(root / "pyproject.toml")
    versions = _project_versions(
        root, repo_name, project, skill_data.get(umbrella, ({}, "missing"))
    )
    disagreements = {
        source: version
        for source, version in versions.items()
        if manifest_version and version != manifest_version
    }
    version_detail = ", ".join(
        [f"manifest={manifest_version or 'missing'}"]
        + [f"{source}={version}" for source, version in sorted(versions.items())]
    )
    required(
        "GENO-007",
        project_error is None and bool(manifest_version) and not disagreements,
        version_detail if project_error is None else project_error,
        remediation="Make every project-level version agree with genotools.yaml.",
    )

    # Skill contracts.
    required(
        "GENO-010",
        bool(skill_files),
        f"found {len(skill_files)} skill contract(s)",
        path="skills",
        remediation="Add at least one skills/<name>/SKILL.md.",
    )
    invalid_skills = []
    for skill_path, (data, error) in skill_data.items():
        if error or not _nonempty(data.get("name")) or not _nonempty(data.get("description")):
            invalid_skills.append(str(skill_path.relative_to(root)))
    required(
        "GENO-011",
        not invalid_skills,
        "all skill contracts have valid name and description frontmatter"
        if not invalid_skills
        else f"invalid: {', '.join(invalid_skills)}",
        remediation="Repair YAML frontmatter and add non-empty name and description fields.",
    )
    names: dict[str, list[str]] = {}
    for skill_path, (data, _) in skill_data.items():
        if _nonempty(data.get("name")):
            names.setdefault(data["name"], []).append(str(skill_path.relative_to(root)))
    duplicates = {name: paths for name, paths in names.items() if len(paths) > 1}
    required(
        "GENO-012",
        not duplicates,
        "skill names are unique" if not duplicates else f"duplicates: {', '.join(sorted(duplicates))}",
        remediation="Give every skill contract a unique canonical name.",
    )
    umbrella_data, umbrella_error = skill_data.get(umbrella, ({}, "missing"))
    umbrella_valid = umbrella_error is None and umbrella_data.get("name") == repo_name
    required(
        "GENO-013",
        umbrella_valid,
        "umbrella skill matches repository" if umbrella_valid else "umbrella skill is missing or misnamed",
        path=umbrella,
        remediation=f"Create skills/{repo_name}/SKILL.md with name: {repo_name}.",
    )
    root_skill = root / "SKILL.md"
    bridge_valid = (
        root_skill.is_symlink()
        and root_skill.resolve() == umbrella.resolve()
        and umbrella.is_file()
    )
    required(
        "GENO-014",
        bridge_valid,
        "root SKILL.md links to the umbrella skill" if bridge_valid else "root SKILL.md is not the umbrella symlink",
        path=root_skill,
        remediation=f"Link SKILL.md to skills/{repo_name}/SKILL.md.",
    )
    shadowed = []
    for skill_path in skill_files:
        descendants = list(skill_path.parent.glob("**/SKILL.md"))
        descendants = [path for path in descendants if path != skill_path]
        if descendants:
            shadowed.append(str(skill_path.parent.relative_to(root)))
    required(
        "GENO-015",
        not shadowed,
        "no skill contract shadows descendants" if not shadowed else f"shadowing directories: {', '.join(shadowed)}",
        remediation="Move descendant skills into bare category directories with no parent SKILL.md.",
    )

    # Instructions and committed local state.
    agents_file = root / "AGENTS.md"
    retired = [name for name in ("GENO.md", "CLAUDE.md", "GEMINI.md") if (root / name).exists()]
    agents_valid = agents_file.is_file() and bool(agents_file.read_text(errors="replace").strip()) and not retired
    required(
        "GENO-020",
        agents_valid,
        "AGENTS.md is the sole instruction file" if agents_valid else f"missing/empty AGENTS.md or retired files present: {', '.join(retired) or 'none'}",
        path="AGENTS.md",
        remediation="Consolidate instructions into AGENTS.md and remove GENO.md, CLAUDE.md, and GEMINI.md.",
    )
    aliased_paths = _paths_containing(root, re.compile(r"/gt-[a-z0-9-]+", re.I))
    required(
        "GENO-021",
        not aliased_paths,
        "all slash commands use canonical names" if not aliased_paths else f"aliases found in: {', '.join(aliased_paths)}",
        remediation="Replace committed /gt-* aliases with canonical /geno-* command names.",
    )
    tracked_local = _tracked_local_state(root)
    required(
        "GENO-022",
        not tracked_local,
        "local state is not tracked" if not tracked_local else f"tracked local state: {', '.join(tracked_local)}",
        remediation="Remove .geno/ and CLAUDE.local.md from Git tracking.",
    )

    # Recommended quality checks.
    poor_descriptions = []
    broad_tools = []
    for skill_path, (data, error) in skill_data.items():
        if error:
            continue
        description = str(data.get("description", "")).strip().lower()
        if description and not description.startswith(_TRIGGER_PREFIXES):
            poor_descriptions.append(str(skill_path.relative_to(root)))
        tools = str(data.get("allowed-tools", ""))
        if "(*)" in tools or tools.strip() == "*":
            broad_tools.append(str(skill_path.relative_to(root)))
    recommended(
        "GENO-101",
        not poor_descriptions,
        "descriptions lead with triggering conditions" if not poor_descriptions else f"workflow-first descriptions: {', '.join(poor_descriptions)}",
        remediation="Rewrite descriptions to begin with when the skill should be used.",
    )
    recommended(
        "GENO-102",
        not broad_tools,
        "tool permissions are scoped" if not broad_tools else f"wildcard tools: {', '.join(broad_tools)}",
        remediation="Replace unrestricted tool wildcards with the narrowest practical patterns.",
    )
    license_present = any(root.glob("LICENSE*"))
    human_docs = (root / "README.md").is_file() and license_present
    recommended(
        "GENO-103",
        human_docs,
        "README and license are present" if human_docs else "README.md or LICENSE is missing",
        remediation="Add README.md and a license file.",
    )
    docs_paths = (root / "docs" / "index.md", root / "docs" / "getting-started.md", root / "mkdocs.yml")
    missing_docs = [str(path.relative_to(root)) for path in docs_paths if not path.is_file()]
    recommended(
        "GENO-104",
        not missing_docs,
        "documentation site files are present" if not missing_docs else f"missing: {', '.join(missing_docs)}",
        remediation="Add docs/index.md, docs/getting-started.md, and mkdocs.yml.",
    )
    raw_npx_paths = _paths_containing(root, re.compile(r"npx\s+skills\s+add", re.I))
    recommended(
        "GENO-105",
        not raw_npx_paths,
        "installation docs use geno-tools" if not raw_npx_paths else f"raw npx install instructions: {', '.join(raw_npx_paths)}",
        remediation="Replace user-facing npx skills add instructions with geno-tools install.",
    )
    exclusive_agent_paths = _paths_containing(
        root,
        re.compile(r"(?:for|requires?|prerequisites?:?)\s+Claude Code|Claude Code skill", re.I),
        include_source=True,
    )
    recommended(
        "GENO-106",
        not exclusive_agent_paths,
        "general descriptions are agent-neutral" if not exclusive_agent_paths else f"exclusive framing: {', '.join(exclusive_agent_paths)}",
        remediation="Use coding-agent language except when describing a genuinely agent-specific feature.",
    )
    runtime_present = _runtime_present(root, project)
    tests_present = any(path.is_file() for path in (root / "tests").glob("**/*")) if (root / "tests").is_dir() else False
    test_docs = _documentation_contains(root, re.compile(r"\b(pytest|npm test|cargo test|go test)\b", re.I))
    runtime_tests_ok = not runtime_present or (tests_present and test_docs)
    recommended(
        "GENO-107",
        runtime_tests_ok,
        "runtime tests and instructions are present" if runtime_tests_ok else "executable runtime lacks tests or documented test command",
        remediation="Add automated tests and document how to run them.",
    )
    cli_commands = _cli_subcommand_count(root, project)
    cli_coverage_ok = cli_commands < 3 or len(skill_files) > 1
    recommended(
        "GENO-108",
        cli_coverage_ok,
        f"{cli_commands} CLI subcommand(s), {len(skill_files)} skill contract(s)",
        remediation="Add focused skill contracts for the CLI's distinct capabilities.",
    )
    guidance_ok = agents_file.is_file() and not _contains_ecosystem_redefinition(agents_file)
    recommended(
        "GENO-109",
        guidance_ok,
        "AGENTS.md stays repository-specific" if guidance_ok else "AGENTS.md is missing or restates ecosystem-wide rules",
        path="AGENTS.md",
        remediation="Keep repository-specific guidance in AGENTS.md and link to geno-tools for ecosystem rules.",
    )
    missing_entrypoint_docs = _undocumented_entrypoints(root, project, skill_files)
    recommended(
        "GENO-110",
        not missing_entrypoint_docs,
        "runtime entry points are reflected in skill/docs contracts"
        if not missing_entrypoint_docs
        else f"undocumented entry points: {', '.join(missing_entrypoint_docs)}",
        remediation="Align the manifest, skill workflows, docs, and runtime entry points.",
    )

    if tuple(result.rule_id for result in results) != RULE_IDS:
        raise AssertionError("compliance engine rule order drifted from RULE_IDS")
    return AuditReport(str(root), tuple(results))


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _relative(root: Path, path: str | Path | None) -> str | None:
    if path is None:
        return None
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            return str(candidate.relative_to(root))
        except ValueError:
            return str(candidate)
    return str(candidate)


def _load_yaml_mapping(path: Path) -> tuple[dict, str | None]:
    if not path.is_file():
        return {}, "genotools.yaml is missing"
    try:
        data = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as error:
        return {}, f"genotools.yaml does not parse: {error}"
    if not isinstance(data, dict):
        return {}, "genotools.yaml must contain a YAML mapping"
    return data, None


def _load_pyproject(path: Path) -> tuple[dict, str | None]:
    if not path.is_file():
        return {}, None
    try:
        return tomllib.loads(path.read_text()).get("project", {}), None
    except (OSError, tomllib.TOMLDecodeError) as error:
        return {}, f"pyproject.toml does not parse: {error}"


def _frontmatter(path: Path) -> tuple[dict, str | None]:
    try:
        text = path.read_text()
    except OSError as error:
        return {}, str(error)
    match = re.match(r"^---\s*\n(.*?)\n---(?:\s*\n|$)", text, re.DOTALL)
    if not match:
        return {}, "missing YAML frontmatter"
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        return {}, f"invalid YAML frontmatter: {error}"
    if not isinstance(data, dict):
        return {}, "frontmatter must contain a YAML mapping"
    return data, None


def _missing_manifest_sources(root: Path, manifest: dict) -> list[str]:
    sources: list[str] = []
    for section in ("config", "runtime"):
        entries = manifest.get(section, [])
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and isinstance(entry.get("src"), str):
                    sources.append(entry["src"])
    skills = manifest.get("skills")
    if isinstance(skills, dict) and isinstance(skills.get("source"), str):
        sources.append(skills["source"])
    return [source for source in sources if not (root / source).exists()]


def _project_versions(root: Path, repo_name: str, project: dict, umbrella: tuple[dict, str | None]) -> dict[str, str]:
    versions: dict[str, str] = {}
    if _nonempty(project.get("version")):
        versions["pyproject"] = project["version"]
    package_json = root / "package.json"
    if package_json.is_file():
        try:
            package_version = json.loads(package_json.read_text()).get("version")
            if _nonempty(package_version):
                versions["package.json"] = package_version
        except (OSError, json.JSONDecodeError):
            versions["package.json"] = "<invalid>"
    init_file = root / repo_name.replace("-", "_") / "__init__.py"
    if init_file.is_file():
        match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", init_file.read_text())
        if match:
            versions["__version__"] = match.group(1)
    umbrella_data, umbrella_error = umbrella
    if umbrella_error is None:
        skill_version = (umbrella_data.get("metadata") or {}).get("version")
        if _nonempty(skill_version):
            versions["umbrella skill"] = skill_version
    return versions


def _candidate_text_paths(root: Path, *, include_source: bool = False) -> list[Path]:
    candidates: set[Path] = set()
    for name in ("README.md", "AGENTS.md", "GENO.md", "CLAUDE.md", "GEMINI.md", "SKILL.md"):
        path = root / name
        if path.is_file():
            candidates.add(path)
    for directory in (root / "docs", root / "skills"):
        if directory.is_dir():
            candidates.update(path for path in directory.rglob("*") if path.is_file() and path.suffix in _TEXT_SUFFIXES)
    if include_source:
        candidates.update(path for path in root.rglob("*.py") if ".git" not in path.parts)
    return sorted(candidates)


def _paths_containing(root: Path, pattern: re.Pattern, *, include_source: bool = False) -> list[str]:
    matches = []
    for path in _candidate_text_paths(root, include_source=include_source):
        try:
            if pattern.search(path.read_text(errors="replace")):
                matches.append(str(path.relative_to(root)))
        except OSError:
            continue
    return matches


def _tracked_local_state(root: Path) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "--", ".geno", ".geno/**", "CLAUDE.local.md"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return ["<not a Git repository>"]
    return [line for line in output.splitlines() if line]


def _runtime_present(root: Path, project: dict) -> bool:
    if project.get("scripts"):
        return True
    return any(
        path.is_file()
        for path in root.iterdir()
        if path.suffix in {".py", ".js", ".ts", ".go", ".rs"}
    )


def _documentation_contains(root: Path, pattern: re.Pattern) -> bool:
    return any(
        pattern.search(path.read_text(errors="replace"))
        for path in _candidate_text_paths(root)
    )


def _cli_subcommand_count(root: Path, project: dict) -> int:
    scripts = project.get("scripts", {}) if isinstance(project, dict) else {}
    count = 0
    for entrypoint in scripts.values() if isinstance(scripts, dict) else []:
        module = str(entrypoint).split(":", 1)[0]
        source = root / f"{module.replace('.', '/')}.py"
        if not source.is_file():
            continue
        text = source.read_text(errors="replace")
        count = max(
            count,
            len(re.findall(r"\.add_parser\(", text)),
            len(re.findall(r"@\w+\.command\b|\.add_command\(", text)),
            len(set(re.findall(r"argv\[0\]\s*(?:==|!=|in)\s*['\"]([^'\"]+)", text))),
        )
    return count


def _contains_ecosystem_redefinition(path: Path) -> bool:
    text = path.read_text(errors="replace")
    patterns = (
        r"(?im)^#+\s+(?:ecosystem\s+)?(?:compliance|nomenclature|required files)",
        r"every\s+geno-[*a-z]",
        r"\{skillset\}-\{sub-skillset\}-\{skill\}",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _undocumented_entrypoints(root: Path, project: dict, skill_files: list[Path]) -> list[str]:
    scripts = project.get("scripts", {}) if isinstance(project, dict) else {}
    if not isinstance(scripts, dict) or not scripts:
        return []
    text_paths = [root / "README.md", *skill_files]
    corpus = "\n".join(path.read_text(errors="replace") for path in text_paths if path.is_file())
    missing = []
    for script in scripts:
        pattern = re.compile(rf"(?m)(?:^|[`/]){re.escape(script)}(?:\s|`|$)")
        if not pattern.search(corpus):
            missing.append(script)
    return missing


__all__ = [
    "AuditReport",
    "CheckResult",
    "RECOMMENDED_RULE_IDS",
    "REQUIRED_RULE_IDS",
    "RULE_IDS",
    "audit_skillset",
]
