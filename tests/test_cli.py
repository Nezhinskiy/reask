import re

from reask import skill_text
from reask.cli import main


def test_skill_has_frontmatter_and_no_cyrillic():
    text = skill_text()
    assert text.startswith("---\nname: reask\n")
    assert not re.search(r"[\u0400-\u04FF]", text)


def test_install_writes_skill(tmp_path):
    assert main(["install", "--skills-dir", str(tmp_path)]) == 0
    assert (tmp_path / "reask" / "SKILL.md").read_text(encoding="utf-8") == skill_text()


def test_install_refuses_to_clobber_modified_copy(tmp_path):
    target = tmp_path / "reask" / "SKILL.md"
    target.parent.mkdir()
    target.write_text("local edits", encoding="utf-8")
    assert main(["install", "--skills-dir", str(tmp_path)]) == 1
    assert target.read_text(encoding="utf-8") == "local edits"
    assert main(["install", "--skills-dir", str(tmp_path), "--force"]) == 0
    assert target.read_text(encoding="utf-8") == skill_text()


def test_uninstall_removes_skill_dir(tmp_path):
    main(["install", "--skills-dir", str(tmp_path)])
    assert main(["uninstall", "--skills-dir", str(tmp_path)]) == 0
    assert not (tmp_path / "reask").exists()
    assert main(["uninstall", "--skills-dir", str(tmp_path)]) == 1
