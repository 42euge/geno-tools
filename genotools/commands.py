import argparse

from genotools import installer, linkdb, registry


def dispatch(args: argparse.Namespace) -> int:
    handlers = {
        "ls": _ls,
        "install": _install,
        "dev": _dev,
        "remove": _remove,
        "update": _update,
        "doctor": _doctor,
    }
    return handlers[args.cmd](args)


def _ls(args: argparse.Namespace) -> int:
    if args.available:
        for name, url in registry.available().items():
            print(f"  {name:<12} {url}")
        return 0
    installed = linkdb.load().skillsets()
    if not installed:
        print("no skillsets installed")
        return 0
    for entry in installed:
        print(f"  {entry.name:<12} {entry.source}  ({entry.mode})")
    return 0


def _install(args: argparse.Namespace) -> int:
    agents = args.agent or ["claude-code"]
    return installer.install(
        name_or_source=args.name,
        agents=agents,
        copy=args.copy,
        project=args.project,
    )


def _dev(args: argparse.Namespace) -> int:
    agents = args.agent or ["claude-code"]
    return installer.dev_link(name=args.name, local_path=args.path, agents=agents)


def _remove(args: argparse.Namespace) -> int:
    return installer.remove(name=args.name, keep_data=args.keep_data)


def _update(args: argparse.Namespace) -> int:
    return installer.update(name=args.name)


def _doctor(_: argparse.Namespace) -> int:
    return installer.doctor()
