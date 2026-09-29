import zipfile
from pathlib import Path

import pytest

from scripts import release_notes, skill_zip

ROOT = Path(__file__).resolve().parent.parent

CHANGELOG = """# Changelog

## Unreleased

- Next.

## 0.2.0 (2026-10-01)

- Second.

## 0.1.0 (2026-09-29)

- First.
"""


def test_latest_is_the_first_release_heading() -> None:
    assert release_notes.latest(CHANGELOG) == "0.2.0"
    assert release_notes.latest("# Changelog\n\n## Unreleased\n") is None


def test_notes_are_the_section_body_without_its_heading() -> None:
    assert release_notes.notes(CHANGELOG, "0.2.0") == "- Second."
    assert release_notes.notes(CHANGELOG, "0.1.0") == "- First."


@pytest.mark.parametrize("version", ["0.3.0", "0.1", "Unreleased"])
def test_notes_for_anything_but_a_release_are_none(version: str) -> None:
    assert release_notes.notes(CHANGELOG, version) is None


def test_a_heading_at_the_end_of_the_file_is_no_release() -> None:
    assert release_notes.notes("## 0.1.0 (2026-09-29)", "0.1.0") is None


def test_release_notes_main_prints_or_refuses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(CHANGELOG, encoding="utf-8")
    assert release_notes.main(["v0.2.0", "--changelog", str(changelog)]) == 0
    assert capsys.readouterr().out.strip() == "- Second."
    assert release_notes.main(["v9.9.9", "--changelog", str(changelog)]) == 1
    assert "::error::" in capsys.readouterr().err


def test_skill_zip_holds_the_skill_folder_and_licence(tmp_path: Path) -> None:
    destination = tmp_path / "out" / "reask-skill.zip"
    assert skill_zip.main([str(destination)]) == 0
    with zipfile.ZipFile(destination) as archive:
        assert archive.namelist() == ["reask/LICENSE", "reask/SKILL.md"]
        assert archive.read("reask/SKILL.md") == (ROOT / "skills/reask/SKILL.md").read_bytes()
        assert archive.read("reask/LICENSE") == (ROOT / "LICENSE").read_bytes()
