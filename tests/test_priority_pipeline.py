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
        decisions = [json.loads(line) for line in out.splitlines()]
        got = {d["case"]: (d["level"] or "", d["scale"]) for d in decisions}
        self.assertEqual(got, EXPECTED)
        by_case = {d["case"]: d for d in decisions}
        self.assertEqual((by_case["T-3"]["blocked_by"], by_case["T-3"]["effective_axes"], by_case["T-3"]["adjudicated"]), ("existing_low", ["data"], False))

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


class ApplyJudgmentsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name)
        self.draft = self.p.root / "draft.jsonl"

    def write_draft(self, *lines):
        self.draft.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lines), encoding="utf-8")

    def judge_all(self):
        self.write_draft(*[{"case": c, "axes": a, "impact": i, "kind": k} for c, (a, i, k) in JUDGMENTS.items()])
        return self.p.run("apply_judgments.py", "judge", self.draft)

    def stored(self):
        return {j["case"]: j for j in pr.read_jsonl(self.p.out / "_raw" / "judgments.jsonl")}

    def test_judge_fills_the_fingerprint_and_leaves_the_reason_empty(self):
        code, out, err = self.judge_all()
        self.assertEqual((code, out.strip()), (0, "6 judgments"), err)
        cases = {c["case"]: c for c in pr.load_cases(pr.load_config(self.p.config))}
        stored = self.stored()
        self.assertEqual(stored["T-1"]["fingerprint"], cases["T-1"]["fingerprint"])
        self.assertEqual((stored["T-1"]["reason"], stored["T-1"]["reason_level"]), ("", 0))
        self.assertEqual(stored["C-1"]["axes"], ["permission"])

    def test_invalid_drafts_are_rejected_and_nothing_is_written(self):
        bad = [
            {"case": "NOPE", "axes": [], "impact": "stop", "kind": "代表"},
            {"case": "T-1", "axes": ["speed"], "impact": "stop", "kind": "代表"},
            {"case": "T-1", "axes": [], "impact": "huge", "kind": "代表"},
            {"case": "T-1", "axes": [], "impact": "stop", "kind": "普通"},
            {"case": "T-1", "axes": [], "impact": "stop", "kind": "代表", "extra": 1},
        ]
        for line in bad:
            with self.subTest(line=line):
                self.write_draft({"case": "T-2", "axes": [], "impact": "stop", "kind": "応用"}, line)
                code, _, err = self.p.run("apply_judgments.py", "judge", self.draft)
                self.assertEqual(code, 2, err)
                self.assertIn("draft.jsonl", err)  # どのファイルの何行目かを伝える
                self.assertFalse((self.p.out / "_raw" / "judgments.jsonl").exists())

    def test_explain_stores_the_reason_with_the_decided_level(self):
        self.judge_all()
        self.write_draft({"case": "T-1", "reason": "結論\n何を確認する？"}, {"case": "X-1", "reason": "領域が決まらない"})
        code, out, err = self.p.run("apply_judgments.py", "explain", self.draft)
        self.assertEqual((code, out.strip()), (0, "2 reasons"), err)
        stored = self.stored()
        self.assertEqual((stored["T-1"]["reason"], stored["T-1"]["reason_level"]), ("結論\n何を確認する？", 2))
        self.assertEqual(stored["X-1"]["reason_level"], 0)

    def test_rejudging_with_the_same_answer_keeps_the_reason(self):
        self.judge_all()
        self.write_draft({"case": "T-1", "reason": "残る理由"})
        self.p.run("apply_judgments.py", "explain", self.draft)
        self.judge_all()
        self.assertEqual(self.stored()["T-1"]["reason"], "残る理由")
        self.write_draft({"case": "T-1", "axes": [], "impact": "cosmetic", "kind": "代表"})
        self.p.run("apply_judgments.py", "judge", self.draft)
        self.assertEqual(self.stored()["T-1"]["reason"], "")

    def test_judgments_of_cases_that_left_the_input_are_dropped(self):
        self.judge_all()
        stale = self.stored()["T-1"] | {"case": "GONE-1"}
        pr.write_jsonl(self.p.out / "_raw" / "judgments.jsonl", [*self.stored().values(), stale])
        self.judge_all()
        self.assertNotIn("GONE-1", self.stored())

    def test_load_cases_fresh_removes_all_stored_judgments(self):
        self.judge_all()
        self.assertEqual(self.p.run("load_cases.py", "--fresh")[0], 0)
        self.assertFalse((self.p.out / "_raw" / "judgments.jsonl").exists())
        self.judge_all()
        self.assertEqual(self.p.run("load_cases.py")[0], 0)
        self.assertTrue((self.p.out / "_raw" / "judgments.jsonl").exists())

    def test_explain_for_a_case_without_a_judgment_is_rejected(self):
        self.write_draft({"case": "T-1", "reason": "x"})
        self.assertEqual(self.p.run("apply_judgments.py", "explain", self.draft)[0], 2)


class SurveyTest(unittest.TestCase):
    def test_lists_areas_features_and_screens_with_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            Project(tmp)
            code, out, err = run_path(script("survey.py"), "--platform", "tcg-markdown", "--glob", "output/*/4-testcases.md", "--root", tmp)
            self.assertEqual(code, 0, err)
            data = json.loads(out)
            self.assertEqual(data["cases"], 6)
            self.assertEqual(data["areas"]["DMY-TASK"], {"cases": 3, "features": {"タスク名の文字数上限": 3}, "screens": {"タスク編集ダイアログ": 3}})
            self.assertEqual(sorted(data["areas"]), ["DMY-COMMON", "DMY-TASK", "DMY-XXX"])

    def test_unknown_platform_exits_2_and_lists_the_choices(self):
        code, _, err = run_path(script("survey.py"), "--platform", "nope", "--glob", "x", "--root", ".")
        self.assertEqual(code, 2)
        self.assertIn("選べるもの", err)


class SampleOutputTest(unittest.TestCase):
    """examples/dummy-product/sample-output/test-priority/ は、実際に build を実行して得た出力例。
    AI の判断（judgments.jsonl）から、CSV がそのまま再現できることと、設定・入力と食い違っていないことを確かめる。"""

    SAMPLE = ROOT / "examples" / "dummy-product" / "sample-output"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".qa").mkdir()
        shutil.copy(ROOT / "examples" / "dummy-product" / ".qa" / "test-priority.toml", self.root / ".qa" / "test-priority.toml")
        shutil.copytree(self.SAMPLE / "DUMMY-001", self.root / "output" / "DUMMY-001")
        shutil.copytree(self.SAMPLE / "test-priority", self.root / "output" / "test-priority")
        self.config = pr.load_config(self.root / ".qa" / "test-priority.toml")

    def run_cli(self, name, *args):
        return run_path(script(name), "--config", self.config["path"], *args, cwd=self.root)

    def test_export_reproduces_the_committed_csvs_byte_for_byte(self):
        for name in ("import.csv", "review.csv"):
            (self.root / "output" / "test-priority" / name).unlink()
        self.assertEqual(self.run_cli("export.py")[0], 0)
        for name in ("import.csv", "review.csv"):
            self.assertEqual((self.root / "output" / "test-priority" / name).read_bytes(), (self.SAMPLE / "test-priority" / name).read_bytes())

    def test_the_committed_output_passes_every_check_including_the_manifest(self):
        code, out, _ = self.run_cli("check_priority.py", "--json")
        self.assertEqual(code, 0, out)
        stats = json.loads(out)["stats"]
        self.assertEqual((stats["cases"], stats["decided"]), (47, 47))

    def test_the_manifest_matches_the_current_config_and_input(self):
        data = json.loads((self.SAMPLE / "test-priority" / "manifest.json").read_text(encoding="utf-8"))
        import hashlib
        self.assertEqual(data["config_hash"], "sha256:" + hashlib.sha256(self.config["path"].read_bytes()).hexdigest())
        self.assertEqual(data["source"]["hash"], pr.source_hash(self.config))
