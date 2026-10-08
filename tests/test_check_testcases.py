import unittest

from tests.helpers import FIXTURES, codes, run, run_json

SCRIPT = "check_testcases.py"
VIEWPOINTS = FIXTURES / "viewpoints_ok.md"


class CheckTestcasesTest(unittest.TestCase):
    def test_well_formed_file_with_matching_trace_is_ok(self):
        code, out, _ = run(SCRIPT, FIXTURES / "testcases_ok.md", "--viewpoints", VIEWPOINTS)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "OK")

    def test_structure_only_check_without_viewpoints(self):
        code, receipt, _ = run_json(SCRIPT, FIXTURES / "testcases_ok.md")
        self.assertEqual(code, 0)
        self.assertEqual(receipt["check"], "testcases")
        self.assertEqual(receipt["stats"], {"cases": 8, "lastCaseId": "DUMMY-001-TC-008"})

    def test_wrong_column_set_is_reported(self):
        code, receipt, _ = run_json(SCRIPT, FIXTURES / "testcases_columns.md")
        self.assertEqual(code, 1)
        self.assertEqual(codes(receipt), ["COLUMNS"])

    def test_sequence_remarks_viewpoint_id_and_trace_are_reported(self):
        code, receipt, _ = run_json(SCRIPT, FIXTURES / "testcases_ng.md", "--viewpoints", VIEWPOINTS)
        self.assertEqual(code, 1)
        self.assertEqual(
            codes(receipt),
            ["REMARKS", "SEQUENCE", "TRACE", "TRACE", "TRACE", "VIEWPOINT_ID"],
        )
        trace = {f["tp"]: (f["expected"], f["actual"]) for f in receipt["findings"] if f["code"] == "TRACE"}
        self.assertEqual(trace, {"TP-001": (4, 3), "TP-002": (3, 1), "TP-003": (1, 0)})

    def test_text_output_lists_one_finding_per_line(self):
        code, out, _ = run(SCRIPT, FIXTURES / "testcases_ng.md")
        self.assertEqual(code, 1)
        self.assertIn("SEQUENCE 7 expected DUMMY-001-TC-003 got DUMMY-001-TC-004", out.splitlines())

    def test_missing_viewpoints_file_exits_two(self):
        code, _, err = run(SCRIPT, FIXTURES / "testcases_ok.md", "--viewpoints", FIXTURES / "nope.md")
        self.assertEqual(code, 2)
        self.assertIn("nope.md", err)


if __name__ == "__main__":
    unittest.main()
