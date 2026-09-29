"""Command line: install, print or remove the reask skill."""

import argparse
import os
import sys
from collections.abc import Callable
from pathlib import Path

from reask import __version__, skill_text

NAME = "reask"


class RefusedError(Exception):
    """An operation reask will not perform; the message says why and what to do instead."""


def _default_skills_dir() -> Path:
    config = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(config).expanduser() if config else Path.home() / ".claude") / "skills"


def _locate(args: argparse.Namespace) -> tuple[Path, Path]:
    """Return the directory the user named, and the SKILL.md reask manages below it."""
    if args.project:
        base = Path.cwd()
        return base, base / ".claude" / "skills" / NAME / "SKILL.md"
    base = args.skills_dir.expanduser() if args.skills_dir else _default_skills_dir()
    return base, base / NAME / "SKILL.md"


def _refuse_links(base: Path, target: Path) -> None:
    # Everything under a project is whatever the cloned repository put there, so a link below
    # the named directory could aim a write or a delete anywhere. Below it, reask follows none.
    path = base
    for part in target.relative_to(base).parts:
        path /= part
        if path.is_symlink():
            raise RefusedError(
                f"{path} is a symbolic link, and reask does not write or delete through links. "
                "If another tool installed the skill there (the Skills CLI links its folders), "
                "manage it with that tool."
            )


def _refuse_edited(target: Path, data: bytes, force: bool, verb: str) -> None:
    if not target.is_file():
        raise RefusedError(f"{target} is not a file")
    if not force and target.read_bytes() != data:
        raise RefusedError(
            f"{target} differs from reask {__version__}'s copy (edited, or another version); "
            f"pass --force to {verb} it"
        )


def _install(args: argparse.Namespace) -> int:
    base, target = _locate(args)
    _refuse_links(base, target)
    data = skill_text().encode("utf-8")
    if target.exists():
        _refuse_edited(target, data, args.force, "replace")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    print(f"installed {target}")
    return 0


def _uninstall(args: argparse.Namespace) -> int:
    base, target = _locate(args)
    _refuse_links(base, target)
    if not target.exists():
        raise RefusedError(f"{target} not found; nothing to remove")
    _refuse_edited(target, skill_text().encode("utf-8"), args.force, "remove")
    target.unlink()
    folder = target.parent
    if any(folder.iterdir()):
        print(f"removed {target}; kept {folder}, which holds other files")
    else:
        folder.rmdir()
        print(f"removed {folder}")
    return 0


def _print(_: argparse.Namespace) -> int:
    # Bytes, not text: the console's encoding (cp1252 on Windows) and newline translation must
    # not change the skill on its way to `reask print > SKILL.md`.
    sys.stdout.flush()
    sys.stdout.buffer.write(skill_text().encode("utf-8"))
    sys.stdout.buffer.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reask", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    for name, func, help_text, force_help in (
        ("install", _install, "write SKILL.md into a skills directory", "replace an edited copy"),
        ("uninstall", _uninstall, "remove the installed SKILL.md", "remove an edited copy"),
    ):
        cmd = sub.add_parser(name, help=help_text)
        where = cmd.add_mutually_exclusive_group()
        where.add_argument("--project", action="store_true", help="use ./.claude/skills")
        where.add_argument(
            "--skills-dir",
            type=Path,
            help="skills directory (default: $CLAUDE_CONFIG_DIR/skills, else ~/.claude/skills)",
        )
        cmd.add_argument("--force", action="store_true", help=force_help)
        cmd.set_defaults(func=func)

    sub.add_parser("print", help="print SKILL.md to stdout").set_defaults(func=_print)

    args = parser.parse_args(argv)
    command: Callable[[argparse.Namespace], int] = args.func
    try:
        return command(args)
    except (RefusedError, OSError) as error:
        print(f"reask: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
