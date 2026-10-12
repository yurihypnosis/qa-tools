import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT

sys.path.insert(0, str(ROOT / "core"))
import config  # noqa: E402
import gitinfo  # noqa: E402
import jsonl  # noqa: E402


class JsonlTest(unittest.TestCase):
    def test_round_trip_is_sorted_and_keeps_japanese(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a" / "x.jsonl"
            jsonl.write(path, [{"b": 1, "a": "日本語"}])
            self.assertEqual(path.read_text(encoding="utf-8"), '{"a": "日本語", "b": 1}\n')
            self.assertEqual(jsonl.read(path), [{"a": "日本語", "b": 1}])

    def test_missing_file_is_empty_and_blank_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(jsonl.read(Path(tmp) / "none.jsonl"), [])
            path = Path(tmp) / "x.jsonl"
            path.write_text('{"a": 1}\n\n{"a": 2}\n', encoding="utf-8")
            self.assertEqual(len(jsonl.read(path)), 2)

    def test_a_broken_line_names_the_file_and_the_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.jsonl"
            path.write_text('{"a": 1}\n{壊れた\n', encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                jsonl.read(path)
            self.assertIn("x.jsonl", str(ctx.exception))
            self.assertIn("2 行目", str(ctx.exception))


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".qa").mkdir()
        self.path = self.root / ".qa" / "demo.toml"

    def test_load_returns_the_toml_and_requires_the_four_keys(self):
        self.path.write_text('platform = "x"\n[source]\n[output]\n[checks]\n', encoding="utf-8")
        self.assertEqual(config.load(self.path)["platform"], "x")
        self.path.write_text('platform = "x"\n[source]\n', encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            config.load(self.path)
        self.assertIn("output", str(ctx.exception))

    def test_missing_and_broken_files_say_what_to_do(self):
        with self.assertRaises(ValueError) as ctx:
            config.load(self.path)
        self.assertIn("init", str(ctx.exception))
        self.path.write_text("[[[", encoding="utf-8")
        with self.assertRaises(ValueError):
            config.load(self.path)

    def test_resolve_repo_dot_is_the_project_and_names_come_from_local_toml(self):
        self.assertEqual(config.resolve_repo(self.root, "."), self.root)
        with self.assertRaises(ValueError) as ctx:
            config.resolve_repo(self.root, "other")
        self.assertIn("local.toml", str(ctx.exception))
        other = self.root / "elsewhere"
        other.mkdir()
        (self.root / ".qa" / "local.toml").write_text(f'[repos]\nother = "{other}"\n', encoding="utf-8")
        self.assertEqual(config.resolve_repo(self.root, "other"), other)
        (self.root / ".qa" / "local.toml").write_text('[repos]\nother = "/no/such/dir"\n', encoding="utf-8")
        with self.assertRaises(ValueError):
            config.resolve_repo(self.root, "other")


class GitinfoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        for args in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"]):
            subprocess.run(["git", *args], cwd=self.repo, check=True)
        (self.repo / "src").mkdir()
        (self.repo / "src" / "a.ts").write_text("export const a = 1;\n", encoding="utf-8")
        (self.repo / "other.txt").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.repo, check=True)

    def test_clean_tree_gives_the_seven_char_commit(self):
        commit = gitinfo.head(self.repo, "src")
        self.assertRegex(commit, r"^[0-9a-f]{7}$")

    def test_only_changes_under_the_subpath_make_it_dirty(self):
        (self.repo / "other.txt").write_text("y\n", encoding="utf-8")
        self.assertFalse(gitinfo.head(self.repo, "src").endswith("+dirty"))
        (self.repo / "src" / "a.ts").write_text("export const a = 2;\n", encoding="utf-8")
        self.assertTrue(gitinfo.head(self.repo, "src").endswith("+dirty"))
        (self.repo / "src" / "new.ts").write_text("x\n", encoding="utf-8")  # 追跡されていないファイルも
        self.assertTrue(gitinfo.head(self.repo, "src").endswith("+dirty"))

    def test_a_directory_that_is_not_a_git_repo_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                gitinfo.head(Path(tmp), ".")


if __name__ == "__main__":
    unittest.main()
