import importlib.util
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("check_version", ROOT / "scripts" / "check_version.py")
assert _spec is not None and _spec.loader is not None
check_version = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_version)


@pytest.fixture
def tree(tmp_path):
    for name in ("pyproject.toml", "uv.lock", "CHANGELOG.md"):
        shutil.copy(ROOT / name, tmp_path / name)
    return tmp_path


def _version(root):
    return check_version.sources(root)["pyproject.toml"]


def test_repository_agrees_with_itself():
    assert check_version.check(ROOT) == []


def test_matching_tag_passes(tree):
    assert check_version.check(tree, f"v{_version(tree)}") == []


@pytest.mark.parametrize("tag", ["v9.9.9", "0.1.0", "v0.1.0rc1"])
def test_wrong_tag_fails(tree, tag):
    assert [p for p in check_version.check(tree, tag) if p.startswith("tag:")]


def test_stale_changelog_fails(tree):
    path = tree / "CHANGELOG.md"
    path.write_text(path.read_text().replace(f"## {_version(tree)}", "## 0.0.9"))
    assert [p for p in check_version.check(tree) if p.startswith("CHANGELOG.md")]


def test_stale_lock_fails(tree):
    path = tree / "pyproject.toml"
    path.write_text(path.read_text().replace(f'version = "{_version(tree)}"', 'version = "9.9.9"'))
    assert [p for p in check_version.check(tree) if p.startswith("uv.lock")]
