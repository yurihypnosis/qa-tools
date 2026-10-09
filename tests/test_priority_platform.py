"""プラットフォーム定義 tcg-markdown と、プラットフォーム定義の分離（contracts.md の C9）。"""
import hashlib
import re
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES, ROOT

SKILL = ROOT / "skills" / "test-priority"
sys.path.insert(0, str(SKILL / "scripts"))
import _priority as pr  # noqa: E402

HEADER = ("| CaseNo. | 観点ID/Viewpoint ID | タイトル/Title | 領域/Area | 確認画面/Screen | 機能/Function | 大項目/Category | "
          "中項目/Sub category | 小項目/Item | 実施ユーザー/Execution Role | 事前条件/Precondition | 実施手順/Execution Step | "
          "期待結果/Expected Result | 重要度/Priority | 備考/Remarks |")
SEPARATOR = "| " + " | ".join(["---"] * 15) + " |"


def row(case, priority="High", area="DMY-TASK", screen="編集", feature="文字数", title="確認"):
    return (f"| {case} | TP-001 | {title} | {area} | {screen} | {feature} | 大項目1 | - | 操作 | ロール | ・前提1<br>・前提2 | "
            f"1. 開く<br>2. 保存 | ・結果 | {priority} |  |")


def write_md(directory, name, *rows):
    path = Path(directory) / name
    path.write_text("### 大項目1\n\n" + "\n".join([HEADER, SEPARATOR, *rows]) + "\n", encoding="utf-8")
    return path


class TcgMarkdownTest(unittest.TestCase):
    def setUp(self):
        self.platform = pr.load_platform("tcg-markdown")

    def test_reads_the_existing_fixture_into_normalized_records(self):
        records = self.platform.load_cases(FIXTURES / "testcases_ok.md")
        self.assertEqual(len(records), 8)
        first = records[0]
        self.assertEqual(sorted(first), ["area", "body", "case", "existing", "feature", "fingerprint", "screen", "title"])
        self.assertEqual((first["case"], first["area"], first["screen"], first["existing"]),
                         ("DUMMY-001-TC-001", "DMY-TASK", "タスク編集画面", "high"))
        self.assertIn("エラー「タスク名を入力してください」が表示される", first["body"])

    def test_priority_values_are_lowercased_and_unknown_becomes_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_md(tmp, "4-testcases.md", row("X-1", "Low"), row("X-2", "Medium"), row("X-3", ""), row("X-4", "Critical"))
            self.assertEqual([r["existing"] for r in self.platform.load_cases(path)], ["low", "medium", "", ""])

    def test_fingerprint_changes_when_the_content_changes_and_not_otherwise(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self.platform.load_cases(write_md(tmp, "a.md", row("X-1")))[0]
            b = self.platform.load_cases(write_md(tmp, "b.md", row("X-1")))[0]
            c = self.platform.load_cases(write_md(tmp, "c.md", row("X-1", title="別の確認")))[0]
            self.assertEqual(a["fingerprint"], b["fingerprint"])
            self.assertNotEqual(a["fingerprint"], c["fingerprint"])
            self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", a["fingerprint"]))
            self.assertEqual(hashlib.sha256("\x1f".join([a["title"], a["area"], a["feature"], a["screen"], a["body"]]).encode()).hexdigest(),
                             a["fingerprint"])

    def test_wrong_column_count_is_a_value_error_with_the_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_md(tmp, "4-testcases.md", row("X-1") + " 余分 |")
            with self.assertRaises(ValueError) as ctx:
                self.platform.load_cases(path)
            self.assertIn("5 行目", str(ctx.exception))

    def test_a_file_without_a_case_table_gives_no_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "4-testcases.md"
            path.write_text("# 何も無い\n", encoding="utf-8")
            self.assertEqual(self.platform.load_cases(path), [])


class PlatformSeparationTest(unittest.TestCase):
    """C9：プラットフォーム名と、テストケースの列名は platforms/ の外に書かない。"""

    FORBIDDEN = ("tcg-markdown", "CaseNo.", "確認画面/Screen", "機能/Function", "領域/Area", "重要度/Priority", "4-testcases")

    def test_nothing_outside_platforms_names_the_platform_or_its_columns(self):
        offenders = []
        for path in SKILL.rglob("*"):
            if not path.is_file() or "platforms" in path.relative_to(SKILL).parts or path.suffix in (".pyc",):
                continue
            text = path.read_text(encoding="utf-8")
            offenders += [f"{path.relative_to(ROOT)}: {word}" for word in self.FORBIDDEN if word in text]
        self.assertEqual(offenders, [])

    def test_unknown_platform_is_a_config_error_listing_the_choices(self):
        with self.assertRaises(pr.ConfigError) as ctx:
            pr.load_platform("nope")
        self.assertIn("tcg-markdown", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
