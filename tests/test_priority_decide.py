"""test-priority の判定ロジック（docs/design/tools/test-priority.md の 4・6・7・10）。"""
import sys
import unittest

from tests.helpers import FIXTURES, ROOT

sys.path.insert(0, str(ROOT / "skills" / "test-priority" / "scripts"))
import _priority as pr  # noqa: E402

CONFIG = pr.load_config(FIXTURES / "priority" / "test-priority.toml")
RULES = CONFIG["rules"]


def rec(case="C", area="DMY-TASK", feature="タスク名の文字数上限", screen="タスク編集ダイアログ", existing=""):
    return {"case": case, "title": "t", "area": area, "feature": feature, "screen": screen,
            "existing": existing, "body": "b", "fingerprint": f"fp-{case}"}


def judgment(case="C", axes=(), impact="stop", kind="応用"):
    return {"case": case, "fingerprint": f"fp-{case}", "axes": list(axes), "impact": impact, "kind": kind,
            "reason": "r", "reason_level": 0}


def decide(record, axes, impact, kind, rep, adjudication=None):
    d = pr.decide_level(RULES, record, judgment(record["case"], axes, impact, kind), adjudication)
    d["scale"] = pr.scale_of(RULES, record, d["level"], rep, adjudication)
    return d


class WorkedExamplesTest(unittest.TestCase):
    """仕様書 §10 の計算例 6 つ。"""

    def test_1_data_axis_raises_one_step(self):
        d = decide(rec(existing="high"), ["data"], "stop", "代表", True)
        self.assertEqual((d["start"], d["level"], d["scale"], d["marks"]), (3, 2, "smoke", []))
        self.assertEqual((d["effective_axes"], d["blocked_by"]), (["data"], None))

    def test_2_cosmetic_without_axis_lowers_one_step(self):
        d = decide(rec(existing="medium"), [], "cosmetic", "応用", False)
        self.assertEqual((d["level"], d["scale"], d["marks"]), (4, "full", ["下げ"]))

    def test_3_cannot_go_above_r1(self):
        d = decide(rec(area="DMY-COMMON", feature="ログイン", existing="high"), ["permission"], "harm", "代表", True)
        self.assertEqual((d["start"], d["level"], d["scale"], d["marks"]), (1, 1, "sanity", []))

    def test_4_unlisted_feature_uses_default_and_is_marked(self):
        d = decide(rec(area="DMY-COMMON", feature="ログアウト"), ["blast"], "stop", "応用", False)
        self.assertEqual((d["start"], d["level"], d["scale"], d["marks"]), (2, 1, "smoke", ["上げ", "推定"]))

    def test_5_unknown_area_is_undecidable(self):
        d = decide(rec(area="DMY-XXX"), ["data"], "stop", "代表", True)
        self.assertEqual((d["level"], d["scale"], d["marks"]), (None, "判定不可", ["判定不可"]))

    def test_6_existing_low_blocks_a_raise(self):
        d = decide(rec(existing="low"), ["data"], "stop", "応用", False)
        self.assertEqual((d["level"], d["scale"], d["marks"]), (3, "full", []))
        self.assertEqual((d["effective_axes"], d["blocked_by"]), (["data"], "existing_low"))


class RuleDetailsTest(unittest.TestCase):
    def test_axis_outside_the_areas_emphasis_does_not_raise(self):
        d = decide(rec(), ["blast"], "harm", "応用", False)  # DMY-TASK は data と permission だけ
        self.assertEqual(d["level"], 3)

    def test_cosmetic_with_an_effective_axis_is_unchanged(self):
        self.assertEqual(decide(rec(), ["data"], "cosmetic", "応用", False)["level"], 3)

    def test_existing_high_blocks_a_lowering(self):
        d = decide(rec(existing="high"), [], "cosmetic", "応用", False)
        self.assertEqual((d["level"], d["blocked_by"]), (3, "existing_high"))

    def test_axes_outside_the_emphasis_are_not_effective(self):
        d = decide(rec(), ["blast", "data"], "stop", "応用", False)
        self.assertEqual(d["effective_axes"], ["data"])

    def test_excluded_feature_is_out_of_scale(self):
        rules = {**RULES, "exclude": {"features": ["タスク名の文字数上限"]}}
        self.assertEqual(pr.scale_of(rules, rec(), 2, True, None), "対象外")

    def test_adjudicated_level_resolves_an_undecidable_case(self):
        adj = {"重要度": "R2", "理由": "管理者"}
        d = decide(rec(area="DMY-XXX"), [], "stop", "応用", False, adj)
        self.assertEqual((d["level"], d["scale"], d["marks"]), (2, "light", []))

    def test_adjudicated_scale_wins_over_the_table(self):
        adj = {"規模": "対象外", "理由": "別 PBI で網羅"}
        d = decide(rec(), ["data"], "stop", "代表", True, adj)
        self.assertEqual(d["scale"], "対象外")


class DecideAllTest(unittest.TestCase):
    def setUp(self):
        self.cases = [
            rec("A-1", screen="一覧"), rec("A-2", screen="一覧"), rec("A-3", screen="一覧"),
            rec("B-1", screen=""), rec("B-2", screen=""),
        ]
        self.judgments = [
            judgment("A-1", ["data"], "stop", "代表"),     # R2
            judgment("A-2", [], "stop", "代表"),           # R3（A-1 が先に選ばれる）
            judgment("A-3", ["data"], "stop", "応用"),     # R2 だが応用
            judgment("B-1", [], "stop", "代表"),           # R3
            judgment("B-2", [], "stop", "代表"),           # R3（同じなら case の昇順で B-1）
        ]

    def run_all(self, cases=None, judgments=None, adjudications=None):
        return {r["case"]: r for r in pr.decide_all(CONFIG, cases or self.cases, judgments or self.judgments, adjudications or {})}

    def test_representative_is_lowest_level_then_smallest_case_per_group(self):
        rows = self.run_all()
        self.assertEqual([c for c, r in sorted(rows.items()) if r["representative"]], ["A-1", "B-1"])
        self.assertEqual((rows["A-1"]["scale"], rows["A-2"]["scale"], rows["A-3"]["scale"]), ("smoke", "full", "light"))

    def test_empty_group_key_forms_one_group_named_none(self):
        rows = self.run_all()
        self.assertEqual((rows["B-1"]["scale"], rows["B-2"]["scale"]), ("light", "full"))

    def test_at_most_one_sanity_per_group(self):
        cases = [rec("S-1", area="DMY-COMMON", feature="ログイン", screen="x"), rec("S-2", area="DMY-COMMON", feature="ログイン", screen="x")]
        judgments = [judgment("S-1", ["permission"], "harm", "代表"), judgment("S-2", ["permission"], "harm", "代表")]
        rows = self.run_all(cases, judgments)
        self.assertEqual(sorted(r["scale"] for r in rows.values()), ["sanity", "smoke"])

    def test_missing_judgment_is_an_input_error(self):
        with self.assertRaises(pr.InputError) as ctx:
            self.run_all(judgments=self.judgments[:-1])
        self.assertIn("B-2", str(ctx.exception))

    def test_stale_fingerprint_counts_as_missing(self):
        stale = [dict(j, fingerprint="old") if j["case"] == "A-1" else j for j in self.judgments]
        with self.assertRaises(pr.InputError) as ctx:
            self.run_all(judgments=stale)
        self.assertIn("A-1", str(ctx.exception))

    def test_same_input_gives_identical_rows(self):
        self.assertEqual(self.run_all(), self.run_all())


class ConfigTest(unittest.TestCase):
    def test_bad_values_are_config_errors(self):
        import tempfile
        from pathlib import Path
        text = (FIXTURES / "priority" / "test-priority.toml").read_text(encoding="utf-8")
        for bad in (text.replace('group_by = "screen"', 'group_by = "page"'),
                    text.replace('default = 3', 'default = 9', 1),
                    text.replace('emphasis = ["data", "permission"]', 'emphasis = ["speed"]'),
                    text.split("[rules]")[0] + "[checks]\nrun = []\n",
                    text.replace('platform = "tcg-markdown"\n', "")):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / ".qa" / "test-priority.toml"
                path.parent.mkdir()
                path.write_text(bad, encoding="utf-8")
                with self.assertRaises(pr.ConfigError):
                    pr.load_config(path)


if __name__ == "__main__":
    unittest.main()
