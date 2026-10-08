import unittest

from tests.helpers import FIXTURES, ROOT, codes, run, run_json

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

    def test_file_without_case_table_is_not_ok(self):
        code, receipt, _ = run_json(SCRIPT, FIXTURES / "testcases_none.md")
        self.assertEqual(code, 1)
        self.assertEqual(codes(receipt), ["NO_CASES"])

    def test_malformed_case_id_is_reported_once(self):
        code, receipt, _ = run_json(SCRIPT, FIXTURES / "testcases_bad_id.md")
        self.assertEqual(code, 1)
        self.assertEqual(codes(receipt), ["CASE_ID"])

    def test_escaped_pipe_inside_cell_is_not_a_column_break(self):
        code, out, _ = run(SCRIPT, FIXTURES / "testcases_escaped_pipe.md")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "OK")

    def test_case_pointing_to_unknown_viewpoint_is_reported(self):
        code, receipt, _ = run_json(SCRIPT, FIXTURES / "testcases_unknown_tp.md", "--viewpoints", VIEWPOINTS)
        self.assertEqual(code, 1)
        self.assertEqual(receipt["findings"], [{"code": "UNKNOWN_TP", "tp": "TP-090", "line": 13}])

    def test_range_headings_expand_with_prefix_and_fullwidth_tilde(self):
        code, receipt, _ = run_json(
            SCRIPT, FIXTURES / "testcases_range.md", "--viewpoints", FIXTURES / "viewpoints_range.md"
        )
        self.assertEqual(code, 1)
        missing = sorted(f["tp"] for f in receipt["findings"] if f["code"] == "TRACE")
        self.assertEqual(missing, ["TP-002", "TP-003", "TP-004", "TP-005"])

    def test_missing_viewpoints_file_exits_two(self):
        code, _, err = run(SCRIPT, FIXTURES / "testcases_ok.md", "--viewpoints", FIXTURES / "nope.md")
        self.assertEqual(code, 2)
        self.assertIn("nope.md", err)

    def test_recorded_sample_output_still_passes(self):
        """実際の E2E 出力に対する回帰テスト。検査を変えて誤検出が出たら気づける。"""
        sample = ROOT / "examples" / "dummy-product" / "sample-output" / "DUMMY-001"
        code, receipt, _ = run_json(
            SCRIPT, sample / "step3-testcases.md", "--viewpoints", sample / "step2-viewpoints.md"
        )
        self.assertEqual((code, receipt["findings"]), (0, []))
        self.assertEqual(receipt["stats"]["cases"], 37)


if __name__ == "__main__":
    unittest.main()
