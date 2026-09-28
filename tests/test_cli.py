import re
from pathlib import Path

import pytest

import reask
from reask import skill_text
from reask.cli import main

CYRILLIC = re.compile(f"[{chr(0x400)}-{chr(0x4FF)}]")


def _installed(skills_dir: Path) -> Path:
    return skills_dir / "reask" / "SKILL.md"


def test_skill_has_frontmatter_and_no_cyrillic() -> None:
    text = skill_text()
    assert text.startswith("---\nname: reask\n")
    assert not CYRILLIC.search(text)


def test_skill_text_is_the_repository_root_copy() -> None:
    root = Path(__file__).resolve().parent.parent
    assert skill_text() == (root / "SKILL.md").read_text(encoding="utf-8")


def test_install_writes_skill(tmp_path: Path) -> None:
    assert main(["install", "--skills-dir", str(tmp_path)]) == 0
    assert _installed(tmp_path).read_text(encoding="utf-8") == skill_text()


def test_install_is_idempotent_over_an_identical_copy(tmp_path: Path) -> None:
    assert main(["install", "--skills-dir", str(tmp_path)]) == 0
    assert main(["install", "--skills-dir", str(tmp_path)]) == 0


def test_install_project_writes_under_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["install", "--project"]) == 0
    assert _installed(tmp_path / ".claude" / "skills").read_text(encoding="utf-8") == skill_text()


def test_install_refuses_to_clobber_modified_copy(tmp_path: Path) -> None:
    target = _installed(tmp_path)
    target.parent.mkdir()
    target.write_text("local edits", encoding="utf-8")
    assert main(["install", "--skills-dir", str(tmp_path)]) == 1
    assert target.read_text(encoding="utf-8") == "local edits"
    assert main(["install", "--skills-dir", str(tmp_path), "--force"]) == 0
    assert target.read_text(encoding="utf-8") == skill_text()


def test_uninstall_removes_skill_dir(tmp_path: Path) -> None:
    main(["install", "--skills-dir", str(tmp_path)])
    assert main(["uninstall", "--skills-dir", str(tmp_path)]) == 0
    assert not (tmp_path / "reask").exists()
    assert main(["uninstall", "--skills-dir", str(tmp_path)]) == 1


def test_print_writes_the_skill(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["print"]) == 0
    assert capsys.readouterr().out == skill_text()


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == reask.__version__
