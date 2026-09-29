"""reask: an agent skill that re-asks a pending question as a self-contained briefing."""

from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

__version__ = version("reask")

# skills/reask/SKILL.md is the one copy; the wheel carries it as reask/SKILL.md
# (pyproject.toml, force-include). An editable install has no such copy, so it reads the source.
_CHECKOUT_SKILL = Path(__file__).resolve().parents[2] / "skills" / "reask" / "SKILL.md"


def skill_text() -> str:
    """Return the bundled SKILL.md."""
    bundled = files("reask").joinpath("SKILL.md")
    source = bundled if bundled.is_file() else _CHECKOUT_SKILL
    return source.read_text(encoding="utf-8")
