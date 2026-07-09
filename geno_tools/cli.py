import argparse
import sys

from geno_tools import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geno-tools")
    parser.add_argument("--version", action="version", version=f"geno-tools {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # status — installed skillsets, versions, and drift vs remote main
    sub.add_parser("status", help="installed skillsets: version, commit, drift vs remote")
    # ls — back-compat alias for status (supports the old --available/--check flags)
    p_ls = sub.add_parser("ls", help="alias for status (deprecated)")
    p_ls.add_argument("--available", action="store_true", help="alias for `discover`")
    p_ls.add_argument("--check", action="store_true",
                      help="deprecated no-op (status always checks remote)")

    p_install = sub.add_parser("install", help="install a skillset")
    p_install.add_argument("name", help="full repo name (e.g. geno-<name>), git URL, or local path")
    p_install.add_argument("--here", action="store_true",
                           help="materialize cwd alias symlinks for this skillset")

    p_dev = sub.add_parser("dev", help="symlink a local checkout as the main worktree")
    p_dev.add_argument("name")
    p_dev.add_argument("path")

    p_fork = sub.add_parser("fork", help="create a variant worktree off main")
    p_fork.add_argument("name")
    p_fork.add_argument("variant", help="variant id (becomes the worktree dir + git branch name)")
    p_fork.add_argument("--isolated-venv", action="store_true",
                        help="create a fresh venv for this variant instead of sharing")

    p_use = sub.add_parser("use", help="select a variant")
    p_use.add_argument("spec", help="<name>@<variant> (e.g. geno-<name>@exp-1)")
    p_use.add_argument("--here", action="store_true",
                       help="cwd-only override; otherwise repoint global active symlink")

    p_promote = sub.add_parser("promote", help="merge variant into main (no upstream push)")
    p_promote.add_argument("name")
    p_promote.add_argument("variant")

    # update — update geno-tools ITSELF to the latest version
    sub.add_parser("update", help="update geno-tools itself to the latest version")
    # upgrade — upgrade installed skillset(s) to latest (git pull + re-register)
    p_upgrade = sub.add_parser("upgrade", help="upgrade installed skillset(s) to latest")
    p_upgrade.add_argument("name", nargs="?", help="skillset to upgrade; omit for all")

    p_rm = sub.add_parser("remove", help="uninstall a skillset")
    p_rm.add_argument("name")
    p_rm.add_argument("--keep-data", action="store_true",
                      help="preserve venvs/ and worktrees")

    p_deps = sub.add_parser("deps", help="show dependency tree for a skillset")
    p_deps.add_argument("name", help="skillset name")

    sub.add_parser("doctor", help="verify symlinks, worktrees, venvs")

    # durability layer for the audit/run skill — deterministic checks the skill delegates to
    p_audit = sub.add_parser("audit", help="check a repo for ecosystem compliance (backs the audit skill)")
    p_audit.add_argument("path", nargs="?", default=".", help="repo path (default: cwd)")

    p_disc = sub.add_parser("discover", help="find & list installable skillsets, by category")
    p_disc.add_argument("--refresh", action="store_true",
                        help="force a network refresh (otherwise auto-refreshes if >30min stale)")

    p_scan = sub.add_parser("scan", help="scan for new uninstalled skillsets and queue candidates")
    p_scan.add_argument("--namespace", help="filter by namespace prefix (e.g. 'geno', 'acme')")
    p_scan.add_argument("--dry-run", action="store_true", help="list candidates without writing to queue")

    p_docs = sub.add_parser("docs", help="compile skill documentation from SKILL.md files")
    p_docs.add_argument("--docs-dir", type=str, default=None,
                        help="MkDocs docs/ directory (default: auto-detect)")
    p_docs.add_argument("--extra-dir", type=str, action="append", default=[],
                        help="additional directory to scan for skills")
    p_docs.add_argument("--dry-run", action="store_true",
                        help="print without writing files")

    # config — read/write ~/.geno/config.yaml (and settings.json for secrets)
    p_cfg = sub.add_parser("config", help="show or set geno ecosystem config values")
    cfg_sub = p_cfg.add_subparsers(dest="config_cmd")
    cfg_sub.add_parser("show", help="print current config (token redacted)")
    p_cfg_set = cfg_sub.add_parser("set", help="set a config key (dot-path, e.g. llm.endpoint)")
    p_cfg_set.add_argument("key", help="dot-path key (e.g. llm.endpoint, llm.token, llm.model)")
    p_cfg_set.add_argument("value", help="value to set")

    # llm — LLM endpoint management and smart features
    p_llm = sub.add_parser("llm", help="LLM endpoint management (probe, suggest)")
    llm_sub = p_llm.add_subparsers(dest="llm_cmd")
    llm_sub.add_parser("probe", help="discover and benchmark all models on the configured endpoint")
    p_llm_suggest = llm_sub.add_parser("suggest", help="suggest a dot-notation tab name from context")
    p_llm_suggest.add_argument("--cwd", default="", help="working directory")
    p_llm_suggest.add_argument("--job", default="", help="running job/process name")
    p_llm_suggest.add_argument("--title", default="", help="raw tab title")
    p_llm_suggest.add_argument("--model", default="", help="override model (default: top ranked)")

    # workspace — find, open, and create VS Code workspace files
    p_ws = sub.add_parser("workspace", help="manage VS Code .code-workspace files")
    ws_sub = p_ws.add_subparsers(dest="ws_cmd")
    p_ws_ls = ws_sub.add_parser("ls", help="list all .code-workspace files under ~/code")
    p_ws_ls.add_argument("--root", default=None, help="search root (default: ~/code)")
    p_ws_open = ws_sub.add_parser("open", help="open a workspace in VS Code")
    p_ws_open.add_argument("target", help="workspace name, index from ls, or path")
    p_ws_open.add_argument("--root", default=None, help="search root (default: ~/code)")
    p_ws_create = ws_sub.add_parser("create", help="create a new .code-workspace file")
    p_ws_create.add_argument("name", help="workspace name (becomes <name>.code-workspace)")
    p_ws_create.add_argument("paths", nargs="*", help="folders to include")
    p_ws_create.add_argument("--output", default=".", help="output directory (default: cwd)")

    args = parser.parse_args(argv)

    from geno_tools import commands
    return commands.dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
