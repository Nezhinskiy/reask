import shutil
from pathlib import Path

import pytest

from scripts import check_skill

ROOT = Path(__file__).resolve().parent.parent
FILES = (
    "CHANGELOG.md",
    "skills/reask/SKILL.md",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
)
SKILL = "skills/reask/SKILL.md"


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    for name in FILES:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / name, tmp_path / name)
    return tmp_path


def _version(root: Path) -> str:
    version = check_skill.versions(root)["SKILL.md metadata.version"]
    assert version is not None
    return version


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _problems(root: Path, prefix: str, tag: str | None = None) -> list[str]:
    return [p for p in check_skill.check(root, tag) if p.startswith(prefix)]


def test_repository_passes() -> None:
    assert check_skill.check(ROOT) == []


def test_matching_tag_passes(tree: Path) -> None:
    assert check_skill.check(tree, f"v{_version(tree)}") == []


@pytest.mark.parametrize("tag", ["v9.9.9", "0.1.0", "v0.1.0rc1"])
def test_wrong_tag_fails(tree: Path, tag: str) -> None:
    assert _problems(tree, "tag:", tag)


@pytest.mark.parametrize(
    ("path", "old", "new", "prefix"),
    [
        ("CHANGELOG.md", "## {v} (", "## 0.0.9 (", "CHANGELOG.md's newest release"),
        (".claude-plugin/plugin.json", '"version": "{v}"', '"version": "0.0.9"', ".claude-plugin"),
        (SKILL, 'version: "{v}"', 'version: "0.0.9"', ".claude-plugin"),
    ],
)
def test_a_stale_version_source_fails(
    tree: Path, path: str, old: str, new: str, prefix: str
) -> None:
    _edit(tree / path, old.format(v=_version(tree)), new)
    assert _problems(tree, prefix)


def test_a_release_heading_without_a_date_fails(tree: Path) -> None:
    # The release workflow reads the notes through the same parser, after the tag is pushed.
    _edit(tree / "CHANGELOG.md", f"## {_version(tree)} (", f"## {_version(tree)}\n\n(")
    assert _problems(tree, "CHANGELOG.md has no release notes")


def test_a_release_with_empty_notes_fails(tree: Path) -> None:
    changelog = tree / "CHANGELOG.md"
    heading = next(
        line
        for line in changelog.read_text(encoding="utf-8").splitlines()
        if line.startswith(f"## {_version(tree)} ")
    )
    changelog.write_text(f"# Changelog\n\n{heading}\n", encoding="utf-8")
    assert _problems(tree, "CHANGELOG.md has no release notes")


def test_a_second_skill_fails(tree: Path) -> None:
    (tree / "nested").mkdir()
    shutil.copy(tree / SKILL, tree / "nested" / "SKILL.md")
    assert _problems(tree, "expected exactly one skill")


def test_a_skill_at_the_root_fails(tree: Path) -> None:
    # The Skills CLI copies the folder holding SKILL.md, so a root skill ships the whole repository.
    (tree / SKILL).rename(tree / "SKILL.md")
    assert _problems(tree, "expected exactly one skill")


def test_a_renamed_skill_fails(tree: Path) -> None:
    _edit(tree / SKILL, "name: reask", "name: re-ask")
    assert _problems(tree, "SKILL.md name")


def test_an_overlong_description_fails(tree: Path) -> None:
    _edit(tree / SKILL, 'description: "', 'description: "' + "x" * 1024)
    assert _problems(tree, "SKILL.md description is")


def test_a_plugin_overriding_the_skills_directory_fails(tree: Path) -> None:
    _edit(tree / ".claude-plugin/plugin.json", '"license"', '"skills": ["./"],\n  "license"')
    assert _problems(tree, "plugin.json")


def test_a_marketplace_pointing_elsewhere_fails(tree: Path) -> None:
    _edit(tree / ".claude-plugin/marketplace.json", '"source": "./"', '"source": "./other"')
    assert _problems(tree, "marketplace.json")


def test_missing_frontmatter_fails(tree: Path) -> None:
    (tree / SKILL).write_text("# reask\n", encoding="utf-8")
    assert _problems(tree, "SKILL.md must begin with YAML frontmatter")


def test_a_multiline_description_fails(tree: Path) -> None:
    _edit(tree / SKILL, 'description: "', "description: >\n  ")
    assert _problems(tree, "SKILL.md description must be one double-quoted line")


def test_main_reports_success(capsys: pytest.CaptureFixture[str]) -> None:
    assert check_skill.main([]) == 0
    assert f"one version everywhere: {_version(ROOT)}" in capsys.readouterr().out


def test_main_reports_each_problem_as_a_ci_error(
    tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert check_skill.main(["--root", str(tree), "--tag", "v9.9.9"]) == 1
    assert "::error::tag:" in capsys.readouterr().err


def test_an_unreleased_section_above_the_release_is_allowed(tree: Path) -> None:
    _edit(
        tree / "CHANGELOG.md",
        f"## {_version(tree)} (",
        f"## Unreleased\n\n- Next.\n\n## {_version(tree)} (",
    )
    assert check_skill.check(tree) == []
