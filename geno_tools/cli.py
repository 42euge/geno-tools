import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from geno_tools import __version__
from geno_tools.core import add_parser as add_core_parser
from geno_tools.skills_manager import add_parser as add_skillset_parsers
from geno_tools.sync.commands import add_parser as add_sync_parser


SKILLSET_LIFECYCLE_COMMANDS = [
    ("install REF", "Install by name, git URL, or local path"),
    ("uninstall NAME", "Uninstall one skillset"),
    ("update [NAME]", "Update one installed skillset, or all"),
    ("dev COMMAND", "Activate or restore a local development checkout"),
]

SKILLSET_INSPECTION_COMMANDS = [
    ("status", "Show installed skillsets and update status"),
    ("discover", "Browse skillsets available to install"),
    ("scan", "Find new skillset repositories"),
    ("audit check [TARGET]", "Check a repository against the compliance spec"),
]

OTHER_COMMANDS = [
    ("sync COMMAND", "Compare or reconcile installations across hosts"),
    ("system", "Update or uninstall geno-tools itself"),
    ("config", "Show or set ecosystem configuration"),
]


def _command_table(commands: list[tuple[str, str]]) -> Table:
    table = Table.grid(padding=(0, 3))
    table.add_column(style="bold magenta", no_wrap=True)
    table.add_column()
    for command, description in commands:
        table.add_row(command, description)
    return table


def _print_root_help() -> None:
    console = Console(highlight=False)
    console.print("[bold]geno-tools[/bold] — manage agent skills and their tooling")
    console.print("\n[dim]Usage:[/dim] geno-tools COMMAND [OPTIONS]\n")
    console.print(
        Panel.fit(
            _command_table(SKILLSET_LIFECYCLE_COMMANDS),
            title="[bold]Manage skillsets[/bold]",
            subtitle="Install, uninstall, and update agent skills",
            border_style="magenta",
            padding=(0, 1),
        )
    )
    console.print(
        Panel.fit(
            _command_table(SKILLSET_INSPECTION_COMMANDS),
            title="[bold]Find and inspect skillsets[/bold]",
            border_style="magenta",
            padding=(0, 1),
        )
    )
    console.print(
        Panel.fit(
            _command_table(OTHER_COMMANDS),
            title="[bold]Other commands[/bold]",
            border_style="dim",
            padding=(0, 1),
        )
    )
    console.print("\n[dim]Run 'geno-tools COMMAND --help' for command details.[/dim]")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="geno-tools",
        description="Manage agent skillsets and the geno-tools installation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"geno-tools {__version__}")
    sub = parser.add_subparsers(
        dest="cmd", required=True, title="commands", metavar="COMMAND"
    )

    add_skillset_parsers(sub)
    add_core_parser(sub)
    add_sync_parser(sub)

    arguments = sys.argv[1:] if argv is None else argv
    if not arguments:
        _print_root_help()
        return 0
    if arguments in (["-h"], ["--help"]):
        _print_root_help()
        parser.exit()
    if arguments[0] == "skills":
        old_command = arguments[1] if len(arguments) > 1 else None
        if old_command == "uninstall":
            parser.error(
                "'geno-tools skills uninstall' moved to "
                "'geno-tools system uninstall'"
            )
        if old_command == "remove":
            parser.error(
                "'geno-tools skills remove' moved to 'geno-tools uninstall'"
            )
        if old_command == "upgrade":
            parser.error("'geno-tools skills upgrade' moved to 'geno-tools update'")
        if old_command in {"install", "discover", "scan"}:
            parser.error(
                f"'geno-tools skills {old_command}' moved to "
                f"'geno-tools {old_command}'"
            )
        parser.error(
            "'geno-tools skills' was removed; skillset commands are top level"
        )
    if arguments[0] == "upgrade":
        parser.error("'geno-tools upgrade' moved to 'geno-tools update'")
    if arguments[0] == "remove":
        parser.error("'geno-tools remove' moved to 'geno-tools uninstall'")

    args = parser.parse_args(arguments)

    return args._dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
