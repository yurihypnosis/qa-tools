"""test-priority の CLI を通しで動かす（読み込み → 決定 → 書き出し → 検査 → manifest）。"""
import csv
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES, ROOT, run_path
from tests.test_priority_platform import row, write_md

SCRIPTS = ROOT / "skills" / "test-priority" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import _priority as pr  # noqa: E402

TASK = dict(area="DMY-TASK", feature="タスク名の文字数上限", screen="タスク編集ダイアログ")
CASES = [
    row("T-1", "High", **TASK),
    row("T-2", "Medium", **TASK),
    row("T-3", "Low", **TASK),
    row("C-1", "High", area="DMY-COMMON", feature="ログイン", screen="ログイン画面"),
    row("C-2", "", area="DMY-COMMON", feature="ログアウト", screen="ヘッダー"),
    row("X-1", "High", area="DMY-XXX", feature="何か", screen="どこか"),
]
JUDGMENTS = {  # 仕様書 §10 の 6 つの例
    "T-1": (["data"], "stop", "代表"),
    "T-2": ([], "cosmetic", "応用"),
    "T-3": (["data"], "stop", "応用"),
    "C-1": (["permission"], "harm", "代表"),
    "C-2": (["blast"], "stop", "応用"),
    "X-1": (["data"], "stop", "代表"),
}
EXPECTED = {  # case: (重要度, 規模)
    "T-1": ("R2", "smoke"), "T-2": ("R4", "full"), "T-3": ("R3", "full"),
    "C-1": ("R1", "sanity"), "C-2": ("R1", "smoke"), "X-1": ("", "判定不可"),
}


def script(name):
    return SCRIPTS / name


class Project:
    def __init__(self, tmp):
        self.root = Path(tmp)
        (self.root / ".qa").mkdir()
        shutil.copy(FIXTURES / "priority" / "test-priority.toml", self.root / ".qa" / "test-priority.toml")
        (self.root / "output" / "PBI-1").mkdir(parents=True)
        write_md(self.root / "output" / "PBI-1", "4-testcases.md", *CASES)
        self.config = self.root / ".qa" / "test-priority.toml"
        self.out = self.root / "output" / "test-priority"

    def run(self, name, *args):
        return run_path(script(name), "--config", self.config, *args, cwd=self.root)

    def write_judgments(self, reason_levels=None):
        cases = {c["case"]: c for c in pr.load_cases(pr.load_config(self.config))}
        rows = []
        for case, (axes, impact, kind) in JUDGMENTS.items():
            level = reason_levels.get(case, 0) if reason_levels else 0
            rows.append({"case": case, "fingerprint": cases[case]["fingerprint"], "axes": axes, "impact": impact,
                         "kind": kind, "reason": f"{case} の理由", "reason_level": level})
        pr.write_jsonl(self.out / "_raw" / "judgments.jsonl", rows)

    def decided_levels(self):
        code, out, err = self.run("decide.py")
        assert code == 0, err
        return {d["case"]: d["level"] for d in map(json.loads, out.splitlines())}

    def build(self):
        self.write_judgments()
        levels = {c: int(l[1]) if l else 0 for c, l in self.decided_levels().items()}
        self.write_judgments(levels)
        assert self.run("load_cases.py")[0] == 0
        code, _, err = self.run("export.py")
        assert code == 0, err

    def read_csv(self, name):
        with open(self.out / name, encoding="utf-8-sig", newline="") as handle:
            return list(csv.reader(handle))


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name)

    def test_load_cases_writes_one_line_per_case(self):
        code, _, _ = self.p.run("load_cases.py")
        self.assertEqual(code, 0)
        lines = (self.p.out / "_raw" / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(sorted(json.loads(l)["case"] for l in lines), sorted(JUDGMENTS))

    def test_decide_prints_levels_and_scales_from_the_worked_examples(self):
        self.p.write_judgments()
        code, out, _ = self.p.run("decide.py")
        self.assertEqual(code, 0)
        got = {d["case"]: (d["level"] or "", d["scale"]) for d in map(json.loads, out.splitlines())}
        self.assertEqual(got, EXPECTED)

    def test_decide_without_judgments_exits_2(self):
        code, _, err = self.p.run("decide.py")
        self.assertEqual(code, 2)
        self.assertIn("判断が無い", err)

    def test_export_writes_both_csvs_with_bom_and_fixed_columns(self):
        self.p.build()
        raw = (self.p.out / "import.csv").read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        rows = self.p.read_csv("import.csv")
        self.assertEqual(rows[0], ["CaseNo.", "重要度", "規模"])
        self.assertEqual({r[0]: (r[1], r[2]) for r in rows[1:]},
                         {c: v for c, v in EXPECTED.items() if v[1] != "判定不可"})
        review = self.p.read_csv("review.csv")
        header = review[0]
        self.assertEqual(len(review) - 1, 6)
        by_case = {r[0]: dict(zip(header, r)) for r in review[1:]}
        self.assertEqual(by_case["C-2"]["要レビュー"], "上げ;推定")
        self.assertEqual(by_case["X-1"]["要レビュー"], "判定不可")
        self.assertEqual(by_case["T-1"]["代表"], "○")
        self.assertEqual(by_case["T-1"]["既存の優先度"], "High")
        self.assertEqual(by_case["T-1"]["理由"], "T-1 の理由")

    def test_export_refuses_when_a_reason_is_missing_or_for_another_level(self):
        self.p.write_judgments()  # reason_level がすべて 0 のまま
        code, _, err = self.p.run("export.py")
        self.assertEqual(code, 2)
        self.assertIn("理由", err)

    def test_running_twice_gives_byte_identical_outputs(self):
        self.p.build()
        first = [(self.p.out / n).read_bytes() for n in ("import.csv", "review.csv")]
        self.assertEqual(self.p.run("export.py")[0], 0)
        self.assertEqual(first, [(self.p.out / n).read_bytes() for n in ("import.csv", "review.csv")])


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name)
        self.p.build()

    def check(self, *args):
        code, out, _ = self.p.run("check_priority.py", "--json", "--no-manifest", *args)
        return code, json.loads(out)

    def codes(self, receipt):
        return sorted(f["code"] for f in receipt["findings"])

    def edit_csv(self, name, fn):
        rows = self.p.read_csv(name)
        rows = fn(rows)
        with open(self.p.out / name, "w", encoding="utf-8-sig", newline="") as handle:
            csv.writer(handle, lineterminator="\n").writerows(rows)

    def test_clean_output_passes_and_reports_stats(self):
        code, receipt = self.check()
        self.assertEqual((code, receipt["status"], receipt["findings"]), (0, "ok", []))
        self.assertEqual(receipt["check"], "check_priority")
        self.assertEqual(receipt["stats"]["cases"], 6)
        self.assertEqual(receipt["stats"]["decided"], 5)
        self.assertEqual(receipt["stats"]["unresolved"], 1)
        self.assertEqual(receipt["stats"]["sanity"], 1)

    def test_wrong_import_columns(self):
        self.edit_csv("import.csv", lambda rows: [["CaseNo.", "重要度"]] + [r[:2] for r in rows[1:]])
        self.assertEqual(self.codes(self.check()[1]), ["COLUMNS"])

    def test_value_outside_the_vocabulary(self):
        self.edit_csv("import.csv", lambda rows: rows[:1] + [[rows[1][0], "R9", rows[1][2]]] + rows[2:])
        self.assertEqual(self.codes(self.check()[1]), ["VALUE"])

    def test_undecidable_case_in_the_import_file(self):
        self.edit_csv("import.csv", lambda rows: rows + [["X-1", "R1", "smoke"]])
        code, receipt = self.check()
        self.assertEqual(code, 1)
        self.assertIn("EXCLUDED_ROW", self.codes(receipt))

    def test_a_case_missing_from_the_review_file(self):
        self.edit_csv("review.csv", lambda rows: [r for r in rows if r[0] != "T-3"])
        self.assertIn("COVERAGE", self.codes(self.check()[1]))

    def test_a_decided_case_dropped_from_the_import_file(self):
        self.edit_csv("import.csv", lambda rows: [r for r in rows if r[0] != "T-3"])
        self.assertEqual(self.codes(self.check()[1]), ["COVERAGE"])

    def test_adjudication_for_an_unknown_case(self):
        (self.p.out / "adjudications.json").write_text(json.dumps({"NOPE-1": {"規模": "対象外", "理由": "x"}}), encoding="utf-8")
        self.assertEqual(self.codes(self.check()[1]), ["ADJUDICATION_UNKNOWN_CASE"])

    def test_a_worked_example_that_disagrees_with_the_rules(self):
        text = self.p.config.read_text(encoding="utf-8").replace('expect = { level = "R2", scale = "smoke" }', 'expect = { level = "R1", scale = "sanity" }')
        self.p.config.write_text(text, encoding="utf-8")
        self.assertEqual(self.codes(self.check()[1]), ["EXAMPLE"])

    def test_manifest_is_required_unless_skipped(self):
        code, out, _ = self.p.run("check_priority.py", "--json")
        self.assertEqual((code, [f["code"] for f in json.loads(out)["findings"]]), (1, ["MANIFEST"]))


class FinishTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name)
        self.p.build()
        self.manifest = self.p.out / "manifest.json"

    def test_finish_writes_the_manifest_when_the_check_passes(self):
        code, _, err = self.p.run("finish.py")
        self.assertEqual(code, 0, err)
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual((data["tool"], data["items"], data["generated_by"]["claude"], data["generated_by"]["carried"]), ("test-priority", 6, 6, 0))
        self.assertEqual(data["source"]["files"], "output/*/4-testcases.md")
        self.assertEqual(data["inputs"], {})
        self.assertEqual(run_path(ROOT / "core" / "manifest.py", "check", self.p.out)[0], 0)
        self.assertEqual(self.p.run("check_priority.py")[0], 0)

    def test_finish_counts_carried_cases(self):
        self.assertEqual(self.p.run("finish.py", "--carried", "4")[0], 0)
        by = json.loads(self.manifest.read_text(encoding="utf-8"))["generated_by"]
        self.assertEqual((by["claude"], by["carried"]), (2, 4))

    def test_a_failing_check_leaves_the_previous_manifest_untouched(self):
        self.assertEqual(self.p.run("finish.py")[0], 0)
        before = self.manifest.read_bytes()
        rows = self.p.read_csv("import.csv")
        with open(self.p.out / "import.csv", "w", encoding="utf-8-sig", newline="") as handle:
            csv.writer(handle, lineterminator="\n").writerows(rows + [["X-1", "R1", "smoke"]])
        code, out, _ = self.p.run("finish.py")
        self.assertEqual(code, 1)
        self.assertEqual(self.manifest.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
