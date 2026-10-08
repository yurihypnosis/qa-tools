import unittest

from tests.helpers import FIXTURES, run, run_json

SCRIPT = "check_viewpoints.py"


class CheckViewpointsTest(unittest.TestCase):
    def test_well_formed_file_prints_ok_and_exits_zero(self):
        code, out, _ = run(SCRIPT, FIXTURES / "viewpoints_ok.md")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "OK")

    def test_table_without_bold_cell_is_reported_with_header_line(self):
        code, out, _ = run(SCRIPT, FIXTURES / "viewpoints_bold.md")
        self.assertEqual(code, 1)
        self.assertEqual(out.strip(), "BOLD 7")

    def test_dt_title_written_as_heading_is_reported(self):
        code, out, _ = run(SCRIPT, FIXTURES / "viewpoints_heading.md")
        self.assertEqual(code, 1)
        self.assertEqual(out.strip(), "HEADING 5 #### DT-1: ロール × 操作")

    def test_json_receipt_on_success(self):
        code, receipt, _ = run_json(SCRIPT, FIXTURES / "viewpoints_ok.md")
        self.assertEqual(code, 0)
        self.assertEqual(receipt["status"], "ok")
        self.assertEqual(receipt["check"], "viewpoints")
        self.assertEqual(receipt["findings"], [])

    def test_json_receipt_on_failure(self):
        code, receipt, _ = run_json(SCRIPT, FIXTURES / "viewpoints_bold.md")
        self.assertEqual(code, 1)
        self.assertEqual(receipt["status"], "fail")
        self.assertEqual(receipt["findings"], [{"code": "BOLD", "line": 7}])

    def test_table_with_short_separator_row_is_still_checked(self):
        code, out, _ = run(SCRIPT, FIXTURES / "viewpoints_short_separator.md")
        self.assertEqual(code, 1)
        self.assertEqual(out.strip(), "BOLD 5")

    def test_bold_row_label_alone_does_not_satisfy_bold_rule(self):
        code, out, _ = run(SCRIPT, FIXTURES / "viewpoints_label_only_bold.md")
        self.assertEqual(code, 1)
        self.assertEqual(out.strip(), "BOLD 7")

    def test_missing_file_exits_two(self):
        code, _, err = run(SCRIPT, FIXTURES / "does-not-exist.md")
        self.assertEqual(code, 2)
        self.assertIn("does-not-exist.md", err)


if __name__ == "__main__":
    unittest.main()
