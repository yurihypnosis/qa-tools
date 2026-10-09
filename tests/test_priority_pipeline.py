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

    def test_finish_counts_cases_untouched_by_the_ai_as_carried(self):
        (self.p.out / "_raw" / "plan.json").write_text(json.dumps({"judge": ["T-1"], "explain": ["T-1", "C-2"]}), encoding="utf-8")
        self.assertEqual(self.p.run("finish.py")[0], 0)
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


class HardeningTest(unittest.TestCase):
    """レビューで見つかった、仕様書が決めているのに確かめていなかったところ。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name)

    def adjudicate(self, value):
        self.p.write_judgments()
        self.p.out.mkdir(parents=True, exist_ok=True)
        (self.p.out / "adjudications.json").write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return self.p.run("decide.py")

    def test_adjudications_are_validated_against_the_spec(self):
        bad = [
            {"T-1": {"規模": "対象外"}},                       # 理由が無い
            {"T-1": {"規模": "huge", "理由": "x"}},           # 規模が語彙の外
            {"T-1": {"重要度": "R9", "理由": "x"}},           # 重要度が語彙の外
            {"T-1": {"理由": "x"}},                           # 重要度も規模も無い
            {"T-1": {"重要度": "R1", "理由": "x", "他": 1}},  # 知らないキー
        ]
        for value in bad:
            with self.subTest(value=value):
                code, _, err = self.adjudicate(value)
                self.assertEqual(code, 2, err)
                self.assertIn("T-1", err)

    def test_a_corrupt_judgments_file_is_an_input_error_naming_file_and_line(self):
        self.p.write_judgments()
        path = self.p.out / "_raw" / "judgments.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        lines[1] = "{壊れた"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        code, _, err = self.p.run("decide.py")
        self.assertEqual(code, 2)
        self.assertIn("judgments.jsonl", err)
        self.assertIn("2 行目", err)
        self.assertNotIn("Traceback", err)

    def test_a_valid_adjudication_is_accepted(self):
        code, out, err = self.adjudicate({"T-1": {"重要度": "R1", "規模": "smoke", "理由": "監査対象"}})
        self.assertEqual(code, 0, err)
        self.assertIn('"scale": "smoke"', out)

    def test_source_repo_other_than_dot_is_a_config_error(self):
        text = self.p.config.read_text(encoding="utf-8").replace('repo = "."', 'repo = "other-app"')
        self.p.config.write_text(text, encoding="utf-8")
        code, _, err = self.p.run("load_cases.py")
        self.assertEqual(code, 2)
        self.assertIn("repo", err)

    def test_empty_or_truncated_csvs_are_input_errors_not_tracebacks(self):
        self.p.build()
        for name, content in (("import.csv", ""), ("review.csv", ""), ("review.csv", "a,b\n")):
            with self.subTest(name=name, content=content):
                (self.p.out / name).write_text(content, encoding="utf-8")
                code, _, err = self.p.run("check_priority.py", "--no-manifest")
                self.assertEqual(code, 2)
                self.assertNotIn("Traceback", err)
                self.p.build()


class UpdateFlowTest(unittest.TestCase):
    """変わったケースだけを判定し直し、ほかは 1 バイトも変えない（仕様書 2・7）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name)
        self.p.build()
        self.assertEqual(self.p.run("finish.py")[0], 0)
        self.before = self.review()
        self.md = self.p.root / "output" / "PBI-1" / "4-testcases.md"

    def review(self):
        rows = self.p.read_csv("review.csv")
        return {r[0]: r for r in rows[1:]}

    def plan(self, which):
        code, out, err = self.p.run("plan.py", which)
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def draft(self, *lines):
        path = self.p.root / "draft.jsonl"
        path.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lines), encoding="utf-8")
        return path

    def edit_case(self, case, old, new):
        text = self.md.read_text(encoding="utf-8")
        lines = [l.replace(old, new) if l.startswith(f"| {case} ") else l for l in text.splitlines()]
        self.md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def update(self, judged=()):
        """update の手順を、AI の下書きだけ差し替えて通しで行う。"""
        self.assertEqual(self.p.run("load_cases.py")[0], 0)
        pending = self.plan("judge")["pending"]
        if pending:
            axes, impact, kind = JUDGMENTS[pending[0]]
            lines = [{"case": c, "axes": JUDGMENTS[c][0], "impact": JUDGMENTS[c][1], "kind": JUDGMENTS[c][2]} for c in pending]
            self.assertEqual(self.p.run("apply_judgments.py", "judge", self.draft(*lines))[0], 0)
        self.assertEqual(self.p.run("decide.py")[0], 0)
        to_explain = self.plan("explain")["pending"]
        if to_explain:
            self.assertEqual(self.p.run("apply_judgments.py", "explain", self.draft(*[{"case": c, "reason": f"新しい理由 {c}"} for c in to_explain]))[0], 0)
        self.assertEqual(self.p.run("export.py")[0], 0)
        self.assertEqual(self.p.run("finish.py")[0], 0)
        return pending, to_explain

    def test_nothing_changed_means_nothing_to_do_and_identical_output(self):
        pending, to_explain = self.update()
        self.assertEqual((pending, to_explain), ([], []))
        self.assertEqual(self.review(), self.before)
        by = json.loads((self.p.out / "manifest.json").read_text(encoding="utf-8"))["generated_by"]
        self.assertEqual((by["claude"], by["carried"]), (0, 6))

    def test_a_run_that_skips_plan_does_not_inherit_the_previous_plan(self):
        self.edit_case("T-2", "確認", "別の確認")
        self.update()  # plan.json に T-2 が載る
        self.assertEqual(self.p.run("load_cases.py")[0], 0)
        self.assertFalse((self.p.out / "_raw" / "plan.json").exists())
        self.assertEqual(self.p.run("finish.py")[0], 0)
        by = json.loads((self.p.out / "manifest.json").read_text(encoding="utf-8"))["generated_by"]
        self.assertEqual((by["claude"], by["carried"]), (6, 0))

    def test_one_edited_case_is_rejudged_and_every_other_row_is_untouched(self):
        self.edit_case("T-2", "確認", "別の確認")
        pending, to_explain = self.update()
        self.assertEqual((pending, to_explain), (["T-2"], ["T-2"]))
        after = self.review()
        self.assertEqual({c: r for c, r in after.items() if c != "T-2"}, {c: r for c, r in self.before.items() if c != "T-2"})
        reason_column = self.p.read_csv("review.csv")[0].index("理由")
        self.assertEqual(after["T-2"][reason_column], "新しい理由 T-2")
        by = json.loads((self.p.out / "manifest.json").read_text(encoding="utf-8"))["generated_by"]
        self.assertEqual((by["claude"], by["carried"]), (1, 5))

    def test_plan_judge_lists_new_cases_and_forgets_removed_ones(self):
        text = self.md.read_text(encoding="utf-8")
        removed = "\n".join(l for l in text.splitlines() if not l.startswith("| X-1 ")) + "\n"
        self.md.write_text(removed.rstrip("\n") + "\n" + row("N-1", "High", **TASK) + "\n", encoding="utf-8")
        self.assertEqual(self.p.run("load_cases.py")[0], 0)
        plan = self.plan("judge")
        self.assertEqual((plan["pending"], plan["removed"], plan["carried"]), (["N-1"], ["X-1"], 5))
        stored = {j["case"] for j in pr.read_jsonl(self.p.out / "_raw" / "judgments.jsonl")}
        self.assertNotIn("X-1", stored)
        pending = [json.loads(l)["case"] for l in (self.p.out / "_raw" / "pending.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(pending, ["N-1"])

    def test_a_config_change_redoes_only_the_reasons_whose_level_changed(self):
        text = self.p.config.read_text(encoding="utf-8").replace("default = 2", "default = 3")  # DMY-COMMON の既定値
        self.p.config.write_text(text, encoding="utf-8")
        pending, to_explain = self.update()
        self.assertEqual(pending, [])
        self.assertEqual(to_explain, ["C-2"])  # 機能が表に無い C-2 だけ、開始点が変わって R1 → R2
        after = self.review()
        for case in ("T-1", "T-2", "T-3", "C-1", "X-1"):
            self.assertEqual(after[case], self.before[case])
        level_column = self.p.read_csv("review.csv")[0].index("重要度")
        self.assertEqual((self.before["C-2"][level_column], after["C-2"][level_column]), ("R1", "R2"))

    def test_explain_input_carries_the_facts_the_reason_must_be_based_on(self):
        self.assertEqual(self.p.run("load_cases.py")[0], 0)
        self.plan("judge")
        self.p.write_judgments()
        self.assertEqual(self.p.run("decide.py")[0], 0)
        pr.write_jsonl(self.p.out / "_raw" / "judgments.jsonl", [dict(j, reason="", reason_level=0) for j in pr.read_jsonl(self.p.out / "_raw" / "judgments.jsonl")])
        self.plan("explain")
        rows = {r["case"]: r for r in pr.read_jsonl(self.p.out / "_raw" / "explain_input.jsonl")}
        t3 = rows["T-3"]
        self.assertEqual((t3["blocked_by"], t3["effective_axes"], t3["level"], t3["start"], t3["scale"]), ("existing_low", ["data"], "R3", "R3", "full"))
        self.assertTrue({"title", "body", "axes", "impact", "kind", "marks", "representative", "adjudicated"} <= set(t3))

    def test_plan_explain_before_every_case_is_judged_is_an_input_error(self):
        (self.p.out / "_raw" / "judgments.jsonl").unlink()
        code, _, err = self.p.run("plan.py", "explain")
        self.assertEqual(code, 2)
        self.assertIn("判断が無い", err)


class AdjudicateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name)
        self.p.build()
        self.assertEqual(self.p.run("finish.py")[0], 0)
        self.file = self.p.out / "adjudications.json"

    def adjudicate(self, *args):
        return self.p.run("adjudicate.py", *args)

    def test_recording_a_level_changes_the_decision_and_the_reason_is_redone(self):
        code, out, err = self.adjudicate("T-3", "--level", "R1", "--reason", "監査の対象")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(self.file.read_text(encoding="utf-8"))["T-3"], {"重要度": "R1", "理由": "監査の対象"})
        self.assertEqual(self.p.decided_levels()["T-3"], "R1")
        self.assertEqual(json.loads(self.p.run("plan.py", "explain")[1])["pending"], ["T-3"])

    def test_adjudications_survive_a_fresh_build(self):
        self.adjudicate("X-1", "--level", "R2", "--reason", "管理者")
        self.assertEqual(self.p.run("load_cases.py", "--fresh")[0], 0)
        self.assertIn("X-1", json.loads(self.file.read_text(encoding="utf-8")))

    def test_invalid_requests_are_rejected_and_nothing_is_written(self):
        for args in (("NOPE", "--level", "R1", "--reason", "x"), ("T-1", "--reason", "x"), ("T-1", "--level", "R1"),
                     ("T-1", "--level", "R9", "--reason", "x"), ("T-1", "--scale", "huge", "--reason", "x")):
            with self.subTest(args=args):
                self.assertEqual(self.adjudicate(*args)[0], 2)
                self.assertFalse(self.file.exists())

    def test_remove_deletes_one_entry_and_complains_when_there_is_none(self):
        self.adjudicate("T-3", "--scale", "対象外", "--reason", "別 PBI")
        self.adjudicate("X-1", "--level", "R2", "--reason", "x")
        self.assertEqual(self.adjudicate("--remove", "T-3")[0], 0)
        self.assertEqual(sorted(json.loads(self.file.read_text(encoding="utf-8"))), ["X-1"])
        self.assertEqual(self.adjudicate("--remove", "T-3")[0], 2)
