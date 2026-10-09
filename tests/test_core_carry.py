import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT

sys.path.insert(0, str(ROOT / "core"))
import carry  # noqa: E402


class SplitTest(unittest.TestCase):
    def test_same_key_and_hash_is_carried(self):
        self.assertEqual(carry.split({"a": "h1", "b": "h2"}, {"a": "h1", "b": "h2"}),
                         {"carried": ["a", "b"], "changed": [], "removed": []})

    def test_a_different_hash_or_a_new_key_is_changed(self):
        result = carry.split({"a": "h1", "b": "h2"}, {"a": "h1", "b": "H2", "c": "h3"})
        self.assertEqual(result, {"carried": ["a"], "changed": ["b", "c"], "removed": []})

    def test_a_key_missing_from_the_current_items_is_removed(self):
        self.assertEqual(carry.split({"a": "h1", "gone": "h"}, {"a": "h1"}),
                         {"carried": ["a"], "changed": [], "removed": ["gone"]})

    def test_results_are_sorted_so_the_same_input_gives_the_same_output(self):
        a = carry.split({"b": "1", "a": "1"}, {"c": "1", "b": "2", "a": "1"})
        b = carry.split({"a": "1", "b": "1"}, {"a": "1", "b": "2", "c": "1"})
        self.assertEqual(a, b)
        self.assertEqual(a["changed"], ["b", "c"])

    def test_nothing_previous_means_everything_is_changed(self):
        self.assertEqual(carry.split({}, {"a": "1"})["changed"], ["a"])


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "out" / "adjudications.json"

    def test_record_creates_the_file_and_keeps_other_entries(self):
        carry.record(self.path, "A-1", {"重要度": "R1", "理由": "監査"})
        carry.record(self.path, "B-1", {"規模": "対象外", "理由": "別 PBI"})
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(sorted(data), ["A-1", "B-1"])
        self.assertEqual(data["A-1"]["理由"], "監査")

    def test_record_replaces_an_existing_entry_wholly(self):
        carry.record(self.path, "A-1", {"重要度": "R1", "理由": "x"})
        carry.record(self.path, "A-1", {"規模": "smoke", "理由": "y"})
        self.assertEqual(carry.load(self.path)["A-1"], {"規模": "smoke", "理由": "y"})

    def test_forget_removes_only_that_entry_and_tolerates_a_missing_one(self):
        carry.record(self.path, "A-1", {"重要度": "R1", "理由": "x"})
        carry.record(self.path, "B-1", {"重要度": "R2", "理由": "y"})
        self.assertTrue(carry.forget(self.path, "A-1"))
        self.assertFalse(carry.forget(self.path, "A-1"))
        self.assertEqual(sorted(carry.load(self.path)), ["B-1"])

    def test_load_of_a_missing_file_is_empty_and_the_file_is_deterministic(self):
        self.assertEqual(carry.load(self.path), {})
        carry.record(self.path, "B-1", {"理由": "y", "重要度": "R2"})
        carry.record(self.path, "A-1", {"理由": "x", "重要度": "R1"})
        first = self.path.read_bytes()
        carry.record(self.path, "A-1", {"重要度": "R1", "理由": "x"})
        self.assertEqual(self.path.read_bytes(), first)
        self.assertTrue(first.endswith(b"\n"))


if __name__ == "__main__":
    unittest.main()
