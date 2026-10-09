import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT, run_path

sys.path.insert(0, str(ROOT / "core"))
import manifest  # noqa: E402

GIT = {"repo": ".", "commit": "3f2a9c1"}


def write(directory, **overrides):
    args = dict(
        tool="demo",
        source=GIT,
        config_hash_value="sha256:abc",
        inputs={},
        generated_by={"claude": 2, "carried": 1},
        items=3,
        generated_at="2026-10-09T10:00:00+09:00",
    )
    args.update(overrides)
    return manifest.write(directory, **args)


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "output" / "demo"
        self.addCleanup(self.tmp.cleanup)

    def test_write_then_read_round_trips_with_all_eight_keys(self):
        write(self.dir)
        data = manifest.read(self.dir)
        self.assertEqual(sorted(data), sorted(manifest.REQUIRED))
        self.assertEqual(data["generated_by"], {"claude": 2, "script": 0, "carried": 1, "local": 0})
        self.assertEqual(data["version"], 1)
        self.assertEqual(manifest.validate(data), [])

    def test_items_must_equal_the_sum_of_generated_by(self):
        with self.assertRaises(ValueError):
            write(self.dir, items=5)
        self.assertFalse((self.dir / "manifest.json").exists())

    def test_source_is_a_git_pair_or_a_files_pair(self):
        write(self.dir, source={"files": "output/*/4-testcases.md", "hash": "sha256:def"})
        with self.assertRaises(ValueError):
            write(self.dir, source={"repo": "."})

    def test_unknown_generated_by_key_is_rejected(self):
        with self.assertRaises(ValueError):
            write(self.dir, generated_by={"human": 3}, items=3)

    def test_config_hash_is_sha256_of_the_file_bytes(self):
        path = Path(self.tmp.name) / "c.toml"
        path.write_bytes(b"a = 1\n")
        self.assertEqual(manifest.config_hash(path), "sha256:" + hashlib.sha256(b"a = 1\n").hexdigest())

    def test_failed_write_leaves_the_previous_file_untouched(self):
        write(self.dir)
        before = (self.dir / "manifest.json").read_bytes()
        with self.assertRaises(ValueError):
            write(self.dir, items=99)
        self.assertEqual((self.dir / "manifest.json").read_bytes(), before)

    def test_cli_check_reports_a_missing_key(self):
        write(self.dir)
        path = self.dir / "manifest.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["config_hash"]
        path.write_text(json.dumps(data), encoding="utf-8")
        code, out, _ = run_path(ROOT / "core" / "manifest.py", "check", self.dir, "--json")
        receipt = json.loads(out)
        self.assertEqual((code, receipt["status"]), (1, "fail"))
        self.assertEqual(receipt["findings"][0]["code"], "MANIFEST")

    def test_cli_check_passes_a_valid_manifest_and_exits_2_when_absent(self):
        write(self.dir)
        self.assertEqual(run_path(ROOT / "core" / "manifest.py", "check", self.dir)[0], 0)
        self.assertEqual(run_path(ROOT / "core" / "manifest.py", "check", self.dir / "nope")[0], 2)


if __name__ == "__main__":
    unittest.main()
