import zipfile
from pathlib import Path

import pytest

from scripts import release_notes, skill_zip

ROOT = Path(__file__).resolve().parent.parent

CHANGELOG = """# Changelog

## 0.2.0 (2026-10-01)

- Second.

## 0.1.0 (2026-09-29)

- First.
"""


def test_notes_are_the_section_body_without_its_heading() -> None:
    assert release_notes.notes(CHANGELOG, "v0.2.0") == "- Second."
    assert release_notes.notes(CHANGELOG, "v0.1.0") == "- First."


def test_notes_for_an_unknown_version_are_none() -> None:
    assert release_notes.notes(CHANGELOG, "v0.3.0") is None


def test_notes_do_not_match_a_version_prefix() -> None:
    assert release_notes.notes(CHANGELOG, "v0.1") is None


def test_release_notes_main_prints_or_refuses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(CHANGELOG, encoding="utf-8")
    assert release_notes.main(["v0.2.0", "--changelog", str(changelog)]) == 0
    assert capsys.readouterr().out.strip() == "- Second."
    assert release_notes.main(["v9.9.9", "--changelog", str(changelog)]) == 1
    assert "::error::" in capsys.readouterr().err


def test_the_repository_changelog_has_the_current_release() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert release_notes.notes(changelog, "v0.1.0")


def test_skill_zip_holds_the_skill_folder(tmp_path: Path) -> None:
    destination = tmp_path / "out" / "reask-skill.zip"
    assert skill_zip.main([str(destination)]) == 0
    with zipfile.ZipFile(destination) as archive:
        assert archive.namelist() == ["reask/SKILL.md", "reask/LICENSE"]
        assert archive.read("reask/SKILL.md") == (ROOT / "SKILL.md").read_bytes()


def test_skill_zip_is_reproducible(tmp_path: Path) -> None:
    first, second = tmp_path / "a.zip", tmp_path / "b.zip"
    skill_zip.build(first)
    skill_zip.build(second)
    assert first.read_bytes() == second.read_bytes()
