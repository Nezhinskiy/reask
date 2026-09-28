import shutil
from pathlib import Path

import pytest

from scripts import check_skill

ROOT = Path(__file__).resolve().parent.parent
FILES = (
    "pyproject.toml",
    "uv.lock",
    "CHANGELOG.md",
    "SKILL.md",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
)


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    for name in FILES:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / name, tmp_path / name)
    return tmp_path


def _version(root: Path) -> str:
    version = check_skill.versions(root)["pyproject.toml"]
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
        ("CHANGELOG.md", "## {v}", "## 0.0.9", "CHANGELOG.md"),
        ("pyproject.toml", 'version = "{v}"', 'version = "9.9.9"', "uv.lock"),
        (".claude-plugin/plugin.json", '"version": "{v}"', '"version": "0.0.9"', ".claude-plugin"),
        ("SKILL.md", 'version: "{v}"', 'version: "0.0.9"', "SKILL.md metadata"),
    ],
)
def test_a_stale_version_source_fails(
    tree: Path, path: str, old: str, new: str, prefix: str
) -> None:
    _edit(tree / path, old.format(v=_version(tree)), new)
    assert _problems(tree, prefix)


def test_a_second_skill_fails(tree: Path) -> None:
    (tree / "nested").mkdir()
    shutil.copy(tree / "SKILL.md", tree / "nested" / "SKILL.md")
    assert _problems(tree, "expected one SKILL.md")


def test_a_renamed_skill_fails(tree: Path) -> None:
    _edit(tree / "SKILL.md", "name: reask", "name: re-ask")
    assert _problems(tree, "SKILL.md name")


def test_an_overlong_description_fails(tree: Path) -> None:
    _edit(tree / "SKILL.md", 'Trigger: /reask"', "x" * 1024 + ' Trigger: /reask"')
    assert _problems(tree, "SKILL.md description is")


def test_a_plugin_not_loading_the_root_fails(tree: Path) -> None:
    _edit(tree / ".claude-plugin/plugin.json", '"skills": ["./"]', '"skills": ["./skills"]')
    assert _problems(tree, "plugin.json")


def test_a_marketplace_pointing_elsewhere_fails(tree: Path) -> None:
    _edit(tree / ".claude-plugin/marketplace.json", '"source": "./"', '"source": "./other"')
    assert _problems(tree, "marketplace.json")


def test_missing_frontmatter_fails(tree: Path) -> None:
    (tree / "SKILL.md").write_text("# reask\n", encoding="utf-8")
    assert _problems(tree, "SKILL.md must begin with YAML frontmatter")


def test_a_multiline_description_fails(tree: Path) -> None:
    _edit(tree / "SKILL.md", 'description: "', "description: >\n  ")
    assert _problems(tree, "SKILL.md description must be one double-quoted line")


def test_main_reports_success(capsys: pytest.CaptureFixture[str]) -> None:
    assert check_skill.main([]) == 0
    assert "one version everywhere" in capsys.readouterr().out


def test_main_reports_each_problem_as_a_ci_error(
    tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert check_skill.main(["--root", str(tree), "--tag", "v9.9.9"]) == 1
    assert "::error::tag:" in capsys.readouterr().err


def test_an_unreleased_section_above_the_release_is_allowed(tree: Path) -> None:
    _edit(
        tree / "CHANGELOG.md",
        f"## {_version(tree)}",
        f"## Unreleased\n\n- Next.\n\n## {_version(tree)}",
    )
    assert check_skill.check(tree) == []
