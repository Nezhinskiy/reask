import importlib.util
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("check_skill", ROOT / "scripts" / "check_skill.py")
assert _spec is not None and _spec.loader is not None
check_skill = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_skill)

FILES = ("pyproject.toml", "uv.lock", "CHANGELOG.md", "SKILL.md", ".claude-plugin/plugin.json",
         ".claude-plugin/marketplace.json")


@pytest.fixture
def tree(tmp_path):
    for name in FILES:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / name, tmp_path / name)
    return tmp_path


def _version(root):
    return check_skill.versions(root)["pyproject.toml"]


def _edit(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _problems(root, prefix, tag=None):
    return [p for p in check_skill.check(root, tag) if p.startswith(prefix)]


def test_repository_passes():
    assert check_skill.check(ROOT) == []


def test_matching_tag_passes(tree):
    assert check_skill.check(tree, f"v{_version(tree)}") == []


@pytest.mark.parametrize("tag", ["v9.9.9", "0.1.0", "v0.1.0rc1"])
def test_wrong_tag_fails(tree, tag):
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
def test_a_stale_version_source_fails(tree, path, old, new, prefix):
    v = _version(tree)
    _edit(tree / path, old.format(v=v), new)
    assert _problems(tree, prefix)


def test_a_second_skill_fails(tree):
    (tree / "nested").mkdir()
    shutil.copy(tree / "SKILL.md", tree / "nested" / "SKILL.md")
    assert _problems(tree, "expected one SKILL.md")


def test_a_renamed_skill_fails(tree):
    _edit(tree / "SKILL.md", "name: reask", "name: re-ask")
    assert _problems(tree, "SKILL.md name")


def test_an_overlong_description_fails(tree):
    _edit(tree / "SKILL.md", 'Trigger: /reask"', "x" * 1024 + ' Trigger: /reask"')
    assert _problems(tree, "SKILL.md description is")


def test_a_plugin_not_loading_the_root_fails(tree):
    _edit(tree / ".claude-plugin/plugin.json", '"skills": ["./"]', '"skills": ["./skills"]')
    assert _problems(tree, "plugin.json")


def test_a_marketplace_pointing_elsewhere_fails(tree):
    _edit(tree / ".claude-plugin/marketplace.json", '"source": "./"', '"source": "./other"')
    assert _problems(tree, "marketplace.json")
