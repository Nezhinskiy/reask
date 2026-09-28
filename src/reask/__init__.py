"""/reask: a Claude Code skill that re-asks a pending question as a self-contained briefing."""

from importlib.metadata import version
from importlib.resources import files

__version__ = version(__package__)


def skill_text() -> str:
    """Return the bundled SKILL.md."""
    return files(__package__).joinpath("SKILL.md").read_text(encoding="utf-8")
