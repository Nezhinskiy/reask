import os
from pathlib import Path

import pytest

from reask import skill_text
from reask.cli import main


def _installed(skills_dir: Path) -> Path:
    return skills_dir / "reask" / "SKILL.md"


def _symlink(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except OSError:  # Windows without the symlink privilege
        pytest.skip("cannot create symbolic links here")


def test_install_writes_the_skill_byte_for_byte(tmp_path: Path) -> None:
    assert main(["install", "--skills-dir", str(tmp_path)]) == 0
    assert _installed(tmp_path).read_bytes() == skill_text().encode("utf-8")


def test_install_is_idempotent_over_an_identical_copy(tmp_path: Path) -> None:
    assert main(["install", "--skills-dir", str(tmp_path)]) == 0
    assert main(["install", "--skills-dir", str(tmp_path)]) == 0


def test_install_project_writes_under_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["install", "--project"]) == 0
    assert _installed(tmp_path / ".claude" / "skills").read_text(encoding="utf-8") == skill_text()


def test_the_default_directory_follows_claude_config_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))
    assert main(["install"]) == 0
    assert _installed(tmp_path / "config" / "skills").is_file()


def test_the_default_directory_is_under_the_home_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert main(["install"]) == 0
    assert _installed(tmp_path / ".claude" / "skills").is_file()


def test_a_quoted_tilde_in_skills_dir_means_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert main(["install", "--skills-dir", "~/skills"]) == 0
    assert _installed(tmp_path / "skills").is_file()


def test_install_refuses_to_replace_an_edited_copy_without_force(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _installed(tmp_path)
    target.parent.mkdir()
    target.write_text("local edits", encoding="utf-8")
    assert main(["install", "--skills-dir", str(tmp_path)]) == 1
    assert "pass --force to replace it" in capsys.readouterr().err
    assert target.read_text(encoding="utf-8") == "local edits"
    assert main(["install", "--skills-dir", str(tmp_path), "--force"]) == 0
    assert target.read_text(encoding="utf-8") == skill_text()


def test_a_directory_where_the_skill_goes_is_an_error_not_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _installed(tmp_path).mkdir(parents=True)
    assert main(["install", "--skills-dir", str(tmp_path), "--force"]) == 1
    assert "is not a file" in capsys.readouterr().err


def test_a_file_where_the_skills_directory_goes_is_an_error_not_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "file").write_text("", encoding="utf-8")
    assert main(["install", "--skills-dir", str(tmp_path / "file")]) == 1
    assert capsys.readouterr().err.startswith("reask: ")


def test_uninstall_removes_the_skill_and_its_empty_folder(tmp_path: Path) -> None:
    main(["install", "--skills-dir", str(tmp_path)])
    assert main(["uninstall", "--skills-dir", str(tmp_path)]) == 0
    assert not (tmp_path / "reask").exists()
    assert main(["uninstall", "--skills-dir", str(tmp_path)]) == 1


def test_uninstall_keeps_an_edited_copy_without_force(tmp_path: Path) -> None:
    target = _installed(tmp_path)
    target.parent.mkdir()
    target.write_text("local edits", encoding="utf-8")
    assert main(["uninstall", "--skills-dir", str(tmp_path)]) == 1
    assert target.read_text(encoding="utf-8") == "local edits"
    assert main(["uninstall", "--skills-dir", str(tmp_path), "--force"]) == 0
    assert not target.parent.exists()


def test_uninstall_never_deletes_files_it_did_not_write(tmp_path: Path) -> None:
    main(["install", "--skills-dir", str(tmp_path)])
    notes = tmp_path / "reask" / "NOTES.md"
    notes.write_text("mine", encoding="utf-8")
    assert main(["uninstall", "--skills-dir", str(tmp_path), "--force"]) == 0
    assert not _installed(tmp_path).exists()
    assert notes.read_text(encoding="utf-8") == "mine"


@pytest.mark.parametrize("command", ["install", "uninstall"])
@pytest.mark.parametrize("linked", [".claude", ".claude/skills", ".claude/skills/reask"])
def test_project_commands_refuse_a_linked_folder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    command: str,
    linked: str,
) -> None:
    # A cloned repository can ship any of these folders as a link out of the project.
    outside = tmp_path / "outside"
    (outside / "skills" / "reask").mkdir(parents=True)
    (outside / "skills" / "reask" / "SKILL.md").write_text(skill_text(), encoding="utf-8")
    (outside / "skills" / "reask" / "other").write_text("keep", encoding="utf-8")
    project = tmp_path / "project"
    depth = linked.count("/")
    _symlink(project / linked, outside / ["", "skills", "skills/reask"][depth])
    monkeypatch.chdir(project)
    assert main([command, "--project", "--force"]) == 1
    assert "symbolic link" in capsys.readouterr().err
    assert sorted(p.name for p in (outside / "skills" / "reask").iterdir()) == ["SKILL.md", "other"]


@pytest.mark.parametrize("dangling", [False, True])
def test_install_refuses_a_linked_skill_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dangling: bool
) -> None:
    victim = tmp_path / "home" / ".zshrc"
    victim.parent.mkdir()
    if not dangling:
        victim.write_text("export PATH", encoding="utf-8")
    _symlink(tmp_path / "project" / ".claude" / "skills" / "reask" / "SKILL.md", victim)
    monkeypatch.chdir(tmp_path / "project")
    assert main(["install", "--project", "--force"]) == 1
    assert victim.exists() is not dangling
    if not dangling:
        assert victim.read_text(encoding="utf-8") == "export PATH"


def test_a_skills_cli_install_is_left_to_the_skills_cli(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # `npx skills add` for several agents links ~/.claude/skills/reask to one shared folder.
    shared = tmp_path / "agents" / "reask"
    shared.mkdir(parents=True)
    (shared / "SKILL.md").write_text(skill_text(), encoding="utf-8")
    _symlink(tmp_path / "claude" / "reask", shared)
    assert main(["uninstall", "--skills-dir", str(tmp_path / "claude")]) == 1
    assert "manage it with that tool" in capsys.readouterr().err
    assert (shared / "SKILL.md").is_file()


def test_print_writes_the_skill_as_utf8_bytes(capsysbinary: pytest.CaptureFixture[bytes]) -> None:
    assert main(["print"]) == 0
    assert capsysbinary.readouterr().out == skill_text().encode("utf-8")


def test_the_symlink_check_does_not_follow_links_above_the_named_directory(
    tmp_path: Path,
) -> None:
    # A dotfiles setup often links ~/.claude itself; that is the user's choice, not a trap.
    real = tmp_path / "dotfiles" / "claude"
    real.mkdir(parents=True)
    _symlink(tmp_path / "home" / ".claude", real)
    assert main(["install", "--skills-dir", str(tmp_path / "home" / ".claude" / "skills")]) == 0
    assert _installed(real / "skills").is_file()
    assert os.path.islink(tmp_path / "home" / ".claude")
