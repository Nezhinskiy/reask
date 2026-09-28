"""Command line: install, print or remove the /reask skill."""

import argparse
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from reask import __version__, skill_text

DEFAULT_SKILLS_DIR = Path.home() / ".claude" / "skills"


def _target(args: argparse.Namespace) -> Path:
    if args.project:
        return Path.cwd() / ".claude" / "skills" / "reask" / "SKILL.md"
    skills_dir: Path = args.skills_dir
    return skills_dir / "reask" / "SKILL.md"


def _install(args: argparse.Namespace) -> int:
    target = _target(args)
    text = skill_text()
    if target.exists() and target.read_text(encoding="utf-8") != text and not args.force:
        print(f"{target} exists and differs; pass --force to overwrite", file=sys.stderr)
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"installed {target}")
    return 0


def _uninstall(args: argparse.Namespace) -> int:
    skill_dir = _target(args).parent
    if not skill_dir.exists():
        print(f"{skill_dir} not found", file=sys.stderr)
        return 1
    shutil.rmtree(skill_dir)
    print(f"removed {skill_dir}")
    return 0


def _print(_: argparse.Namespace) -> int:
    sys.stdout.write(skill_text())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reask", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    for name, func, help_text in (
        ("install", _install, "write SKILL.md into a Claude Code skills directory"),
        ("uninstall", _uninstall, "remove the installed skill directory"),
    ):
        cmd = sub.add_parser(name, help=help_text)
        where = cmd.add_mutually_exclusive_group()
        where.add_argument("--project", action="store_true", help="use ./.claude/skills")
        where.add_argument(
            "--skills-dir",
            type=Path,
            default=DEFAULT_SKILLS_DIR,
            help=f"skills directory (default: {DEFAULT_SKILLS_DIR})",
        )
        if name == "install":
            cmd.add_argument("--force", action="store_true", help="overwrite a modified copy")
        cmd.set_defaults(func=func)

    sub.add_parser("print", help="print SKILL.md to stdout").set_defaults(func=_print)

    args = parser.parse_args(argv)
    command: Callable[[argparse.Namespace], int] = args.func
    return command(args)


if __name__ == "__main__":
    raise SystemExit(main())
