"""nightjar: collects the day's order events and emails a digest to the sales team."""

import argparse
import configparser
import os
from pathlib import Path

from nightjar import commands


def data_dir(legacy_paths: bool) -> Path:
    if legacy_paths:  # deprecated in 1.6
        return Path.home() / ".nightjar"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "nightjar"


def load_settings(path: str = "nightjar.ini") -> dict:
    ini = configparser.ConfigParser()
    ini.read(path)
    return {"smtp_host": ini.get("mail", "smtp_host", fallback=None),
            "recipients": ini.get("mail", "recipients", fallback="").split(",")}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nightjar")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("collect", "send-digest", "prune"):
        c = sub.add_parser(name)
        c.add_argument("--since", default="24h")
        c.add_argument("--older-than", default="90d")
        c.add_argument("--legacy-paths", action="store_true")
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    return commands.run(args.command, args, load_settings(), data_dir(args.legacy_paths))
