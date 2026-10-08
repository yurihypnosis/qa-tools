"""Agent Skills 仕様（agentskills.io）に沿った構造検証。"""
import re
import unittest

from tests.helpers import ROOT

SKILLS = ROOT / "skills"
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    fields = dict(re.findall(r"^([a-z-]+):\s*(.*)$", match.group(1), re.M)) if match else {}
    return fields


class SkillStructureTest(unittest.TestCase):
    def skill_dirs(self):
        dirs = [d for d in SKILLS.iterdir() if d.is_dir()]
        self.assertTrue(dirs)
        return dirs

    def test_frontmatter_follows_spec(self):
        for skill in self.skill_dirs():
            with self.subTest(skill=skill.name):
                fields = frontmatter((skill / "SKILL.md").read_text(encoding="utf-8"))
                self.assertEqual(fields.get("name"), skill.name)
                self.assertRegex(fields["name"], NAME)
                self.assertLessEqual(len(fields["name"]), 64)
                self.assertTrue(0 < len(fields.get("description", "")) <= 1024)

    def test_skill_md_stays_under_500_lines(self):
        for skill in self.skill_dirs():
            with self.subTest(skill=skill.name):
                lines = (skill / "SKILL.md").read_text(encoding="utf-8").count("\n")
                self.assertLess(lines, 500)

    def test_relative_links_and_bundled_paths_resolve(self):
        for skill in self.skill_dirs():
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            paths = re.findall(r"\]\(((?:references|assets|scripts)/[^)]+)\)", text)
            paths += re.findall(r"`((?:references|assets|scripts)/[^`\s]+)`", text)
            for path in paths:
                with self.subTest(skill=skill.name, path=path):
                    self.assertTrue((skill / path).exists())

    def test_every_reference_declares_its_contract(self):
        for reference in SKILLS.glob("*/references/*.md"):
            with self.subTest(reference=reference.name):
                self.assertIn("\n## 契約\n", reference.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
