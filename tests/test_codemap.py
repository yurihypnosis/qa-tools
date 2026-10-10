"""code-map（docs/design/tools/code-map.md）。小さなアプリを一時ディレクトリに作って、抽出から更新まで通しで確かめる。"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT, run_path

SKILL = ROOT / "skills" / "code-map"
CLI = SKILL / "scripts" / "codemap.py"
sys.path.insert(0, str(SKILL / "scripts"))
import _codemap as cm  # noqa: E402

TS_FILES = {
    "tsconfig.json": '{"compilerOptions": {"paths": {"@/*": ["./src/*"]}}}',
    "src/app/page.tsx": 'import { computeStreak } from "@/features/quiz/lib/streak";\nimport Link from "next/link";\nimport "./globals.css";\nimport terms from "@/features/quiz/data/terms.json";\nexport default function Page() { return null; }\n',
    "src/app/globals.css": "body {}\n",
    "src/features/quiz/data/terms.json": "[]\n",
    "src/features/quiz/lib/streak.ts": 'import { fmt } from "./format";\nexport function computeStreak() { return fmt(); }\nexport const LIMIT = 3;\nexport interface Streak { n: number }\n',
    "src/features/quiz/lib/format.ts": "export function fmt() { return 1; }\n",
    "src/features/quiz/index.ts": 'export * from "./lib/streak";\nexport { fmt } from "./lib/format";\n',
    "src/features/mindset/mindset.ts": 'import { fmt } from "@/features/quiz/lib/format";\nconst lazy = import("./lazy");\nconst m = require("../quiz/lib/missing");\nexport const mind = fmt;\n',
    "src/proxy.ts": 'import { mind } from "./features/mindset/mindset";\nexport const p = mind;\n',
}
CONFIG = """platform = ["typescript"]

[source]
repo = "."
root = "src"
exclude = []

[output]
dir = "output/code-map"

[rules]
module_depth = 2
representatives = 2

[rules.typescript]
tsconfig = "tsconfig.json"

[checks]
run = ["public-files"]
"""


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


class Project:
    def __init__(self, tmp, files=TS_FILES, config=CONFIG):
        self.root = Path(tmp)
        for name, text in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (self.root / ".qa").mkdir(exist_ok=True)
        (self.root / ".qa" / "code-map.toml").write_text(config, encoding="utf-8")
        for args in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"]):
            git(self.root, *args)
        self.commit()
        self.out = self.root / "output" / "code-map"

    def commit(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "c", "--allow-empty")

    def run(self, *args):
        return run_path(CLI, *args, "--config", self.root / ".qa" / "code-map.toml", cwd=self.root)

    def extract(self, *args):
        code, out, err = self.run("extract", *args)
        assert code == 0, err
        return json.loads(out)

    def apply_roles(self, roles):
        draft = self.root / "draft.jsonl"
        draft.write_text("".join(json.dumps({"module": m, "role": r}, ensure_ascii=False) + "\n" for m, r in roles.items()), encoding="utf-8")
        return self.run("apply", draft)

    def build(self, roles=None):
        pending = self.extract("--fresh")["pending"]
        code, _, err = self.apply_roles(roles or {m: f"{m} の役割。" for m in pending})
        assert code == 0, err
        for cmd in ("assemble", "finish"):
            code, _, err = self.run(cmd)
            assert code == 0, err

    def snapshot(self):
        return {str(p.relative_to(self.out)): p.read_bytes() for p in sorted(self.out.rglob("*")) if p.is_file() and "_raw" not in p.parts}


class ExtractTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name)

    def test_tree_assigns_modules_by_depth_and_lists_only_source_files(self):
        result = self.p.extract()
        self.assertEqual(result["modules"], ["(root)", "app", "features/mindset", "features/quiz"])
        rows = (self.p.out / "lookup" / "tree.md").read_text(encoding="utf-8").splitlines()
        self.assertEqual(rows[:4], ["# ファイルツリー", "", "| ファイル | モジュール | 言語 | 行数 | ハッシュ |", "| --- | --- | --- | --- | --- |"])
        table = [r for r in rows[4:] if r.startswith("|")]
        self.assertTrue(any(r.startswith("| src/features/quiz/lib/streak.ts | features/quiz | typescript | 4 | ") for r in table))
        self.assertTrue(any(r.startswith("| src/proxy.ts | (root) | typescript | 2 | ") for r in table))
        import hashlib
        digest = hashlib.sha256((self.p.root / "src" / "proxy.ts").read_bytes()).hexdigest()[:12]
        self.assertTrue(any(r == f"| src/proxy.ts | (root) | typescript | 2 | {digest} |" for r in table))   # 内容の sha256 の先頭 12 桁
        self.assertFalse([r for r in table if "globals.css" in r])
        self.assertEqual(table, sorted(table))

    def test_imports_resolve_relative_alias_index_and_ignore_externals_and_assets(self):
        self.p.extract()
        reverse = {r["file"]: r["imported_by"] for r in map(json.loads, (self.p.out / "lookup" / "reverse_imports.jsonl").read_text(encoding="utf-8").splitlines())}
        self.assertEqual(reverse["src/features/quiz/lib/format.ts"], ["src/features/mindset/mindset.ts", "src/features/quiz/index.ts", "src/features/quiz/lib/streak.ts"])
        self.assertEqual(reverse["src/features/quiz/lib/streak.ts"], ["src/app/page.tsx", "src/features/quiz/index.ts"])
        self.assertEqual(reverse["src/features/mindset/mindset.ts"], ["src/proxy.ts"])
        self.assertNotIn("src/app/page.tsx", reverse)

    def test_symbols_are_the_exported_ones_with_their_lines(self):
        self.p.extract()
        lines = (self.p.out / "lookup" / "symbol_index.tsv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "file\tline\tkind\tname")
        self.assertIn("src/features/quiz/lib/streak.ts\t2\tfunction\tcomputeStreak", lines)
        self.assertIn("src/features/quiz/lib/streak.ts\t3\tconst\tLIMIT", lines)
        self.assertIn("src/features/quiz/lib/streak.ts\t4\tinterface\tStreak", lines)
        self.assertIn("src/app/page.tsx\t5\tfunction\tPage", lines)

    def test_unresolved_relative_imports_are_counted_not_fatal(self):
        code, out, _ = self.p.run("extract")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["unresolved"], 2)  # ./lazy と ../quiz/lib/missing

    def test_modules_json_has_representatives_and_module_dependencies(self):
        self.p.extract()
        modules = json.loads((self.p.out / "_raw" / "modules.json").read_text(encoding="utf-8"))
        quiz = modules["features/quiz"]
        self.assertEqual([r["path"] for r in quiz["representatives"]], ["src/features/quiz/lib/format.ts", "src/features/quiz/lib/streak.ts"])
        self.assertEqual(quiz["representatives"][0]["imported_by"], 3)
        self.assertEqual(modules["app"]["depends_on"], {"features/quiz": 1})
        self.assertEqual(modules["features/quiz"]["depended_by"], {"app": 1, "features/mindset": 1})
        self.assertEqual(modules["(root)"]["depends_on"], {"features/mindset": 1})

    def test_the_same_input_gives_identical_lookup_files(self):
        self.p.extract()
        first = self.p.snapshot()
        self.p.extract()
        self.assertEqual(self.p.snapshot(), first)

    def test_no_source_files_or_unknown_platform_exit_2_with_a_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = Project(tmp, files={"src/readme.txt": "x"})
            code, _, err = q.run("extract")
            self.assertEqual(code, 2)
            self.assertIn("ファイルが無い", err)
        text = (self.p.root / ".qa" / "code-map.toml").read_text(encoding="utf-8").replace('["typescript"]', '["cobol"]')
        (self.p.root / ".qa" / "code-map.toml").write_text(text, encoding="utf-8")
        code, _, err = self.p.run("extract")
        self.assertEqual(code, 2)
        self.assertIn("typescript", err)

    def test_exclude_globs_and_always_excluded_directories(self):
        files = dict(TS_FILES, **{"src/features/quiz/lib/format.test.ts": "export const t = 1;\n", "src/node_modules/x/a.ts": "export const n = 1;\n"})
        with tempfile.TemporaryDirectory() as tmp:
            q = Project(tmp, files=files, config=CONFIG.replace("exclude = []", 'exclude = ["**/*.test.ts"]'))
            q.extract()
            tree = (q.out / "lookup" / "tree.md").read_text(encoding="utf-8")
            self.assertNotIn("format.test.ts", tree)
            self.assertNotIn("node_modules", tree)


class PythonTest(unittest.TestCase):
    FILES = {
        "pkg/__init__.py": "",
        "pkg/a.py": "from . import b\nfrom .b import helper\nimport os\nfrom pkg.c import thing\n\ndef run():\n    pass\n\ndef _private():\n    pass\n\nclass Tool:\n    pass\n",
        "pkg/b.py": "def helper():\n    pass\n",
        "pkg/sub/c.py": "from .. import b\nfrom ..missing import x\n",
        "pkg/c.py": "thing = 1\n",
    }

    def test_python_imports_symbols_and_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = Project(tmp, files=self.FILES, config=CONFIG.replace('["typescript"]', '["python"]').replace('root = "src"', 'root = "."').replace("[rules.typescript]\ntsconfig = \"tsconfig.json\"\n", ""))
            result = q.extract()
            reverse = {r["file"]: r["imported_by"] for r in map(json.loads, (q.out / "lookup" / "reverse_imports.jsonl").read_text(encoding="utf-8").splitlines())}
            self.assertEqual(reverse["pkg/b.py"], ["pkg/a.py", "pkg/sub/c.py"])
            self.assertEqual(reverse["pkg/c.py"], ["pkg/a.py"])
            self.assertEqual(result["unresolved"], 1)  # ..missing
            symbols = (q.out / "lookup" / "symbol_index.tsv").read_text(encoding="utf-8").splitlines()
            self.assertIn("pkg/a.py\t6\tfunction\trun", symbols)
            self.assertIn("pkg/a.py\t12\tclass\tTool", symbols)
            self.assertFalse([s for s in symbols if "_private" in s])


class RolesAndAssembleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name)

    def test_extract_lists_every_module_as_pending_the_first_time(self):
        self.assertEqual(self.p.extract("--fresh")["pending"], ["(root)", "app", "features/mindset", "features/quiz"])
        pending = [json.loads(l) for l in (self.p.out / "_raw" / "pending.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([m["module"] for m in pending], ["(root)", "app", "features/mindset", "features/quiz"])
        self.assertIn("representatives", pending[3])

    def test_apply_rejects_bad_drafts_and_writes_nothing(self):
        self.p.extract("--fresh")
        bad = [{"module": "nope", "role": "x"}, {"module": "app", "role": "  "}, {"module": "app", "role": "x" * 700},
               {"module": "app"}, {"module": "app", "role": "x", "extra": 1}]
        for row in bad:
            with self.subTest(row=row):
                draft = self.p.root / "draft.jsonl"
                draft.write_text(json.dumps({"module": "(root)", "role": "ok"}, ensure_ascii=False) + "\n" + json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
                code, _, err = self.p.run("apply", draft)
                self.assertEqual(code, 2)
                self.assertIn("draft.jsonl", err)
                self.assertEqual((self.p.out / "_raw" / "roles.jsonl").read_text(encoding="utf-8"), "")  # 何も取り込まれていない

    def test_assemble_without_every_role_names_the_missing_modules(self):
        self.p.extract("--fresh")
        self.p.apply_roles({"app": "アプリの入口。"})
        code, _, err = self.p.run("assemble")
        self.assertEqual(code, 2)
        self.assertIn("features/quiz", err)

    def test_assemble_writes_module_files_index_architecture_and_skill(self):
        self.p.build({"(root)": "ルートの入口。", "app": "画面を持つ。`src/app/page.tsx` が入口。", "features/mindset": "マインドセット。", "features/quiz": "クイズの計算を持つ。最初の文。次の文。"})
        quiz = (self.p.out / "modules" / "features__quiz.md").read_text(encoding="utf-8")
        headings = [l for l in quiz.splitlines() if l.startswith("## ")]
        self.assertEqual(headings, ["## 役割", "## 主なファイル", "## 公開シンボル", "## 依存先", "## 依存元"])
        self.assertIn("クイズの計算を持つ。最初の文。次の文。", quiz)
        self.assertIn("## 主なファイル\n\n- `src/features/quiz/lib/format.ts`（被参照 3）", quiz)
        self.assertIn("| src/features/quiz/lib/streak.ts | 2 | function | computeStreak |", quiz)      # 代表ファイルのシンボル
        self.assertIn("全部は `lookup/symbol_index.tsv`", quiz)
        self.assertNotIn("| src/features/quiz/index.ts |", quiz)                                  # 代表ファイル以外は出ない（representatives = 2）
        self.assertIn("- `app`（1 import）", quiz)           # 依存元
        self.assertIn("## 依存先\n\n（なし）", quiz)
        index = (self.p.out / "index.md").read_text(encoding="utf-8")
        self.assertIn("| features/quiz | 3 | 4 | クイズの計算を持つ。 | [modules/features__quiz.md](modules/features__quiz.md) |", index)
        arch = (self.p.out / "architecture.md").read_text(encoding="utf-8")
        self.assertIn("| app | features/quiz | 1 |", arch)
        self.assertTrue((self.p.out / "SKILL.md").read_text(encoding="utf-8").startswith("---\nname:") or "当たりを付けるための索引" in (self.p.out / "SKILL.md").read_text(encoding="utf-8"))

    def test_check_passes_on_a_clean_build_and_finish_writes_the_manifest(self):
        self.p.build()
        code, out, _ = self.p.run("check", "--json")
        receipt = json.loads(out)
        self.assertEqual((code, receipt["status"], receipt["findings"]), (0, "ok", []))
        self.assertEqual(receipt["stats"]["modules"], 4)
        self.assertEqual(receipt["stats"]["files"], 6)
        manifest = json.loads((self.p.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual((manifest["tool"], manifest["items"], manifest["generated_by"]["claude"], manifest["generated_by"]["carried"]), ("code-map", 4, 4, 0))
        self.assertRegex(manifest["source"]["commit"], r"^[0-9a-f]{7}$")
        self.assertEqual(manifest["source"]["repo"], ".")
        self.assertEqual(run_path(ROOT / "core" / "manifest.py", "check", self.p.out)[0], 0)


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name)
        self.p.build()

    def codes(self, *args):
        code, out, _ = self.p.run("check", "--json", *args)
        return code, sorted({f["code"] for f in json.loads(out)["findings"]})

    def test_a_missing_public_file_or_module_file(self):
        (self.p.out / "modules" / "app.md").unlink()
        self.assertEqual(self.codes(), (1, ["PUBLIC_MISSING"]))
        (self.p.out / "index.md").unlink()
        self.assertEqual(self.codes()[1], ["PUBLIC_MISSING"])

    def test_a_missing_section_or_an_empty_role(self):
        path = self.p.out / "modules" / "app.md"
        path.write_text(path.read_text(encoding="utf-8").replace("## 依存先", "## 依存"), encoding="utf-8")
        self.assertEqual(self.codes(), (1, ["SECTION"]))
        self.p.build()
        path = self.p.out / "modules" / "app.md"
        path.write_text(path.read_text(encoding="utf-8").replace("app の役割。", ""), encoding="utf-8")
        self.assertEqual(self.codes(), (1, ["SECTION"]))

    def test_a_path_in_the_role_that_is_not_in_the_tree(self):
        self.p.extract("--fresh")
        roles = {"(root)": "x。", "app": "`src/app/nothing.tsx` を持つ。`features/quiz` は module。`src/app/page.tsx` は実在。", "features/mindset": "x。", "features/quiz": "x。"}
        self.assertEqual(self.p.apply_roles(roles)[0], 0)
        self.assertEqual(self.p.run("assemble")[0], 0)
        code, codes = self.codes("--no-manifest")
        self.assertEqual((code, codes), (1, ["ANCHOR"]))
        receipt = json.loads(self.p.run("check", "--json", "--no-manifest")[1])
        self.assertEqual([f["path"] for f in receipt["findings"]], ["src/app/nothing.tsx"])
        code, out, _ = self.p.run("finish")  # 検査に通らないので、manifest は書き換えない
        self.assertEqual(code, 1)

    def test_manifest_is_required_unless_skipped(self):
        (self.p.out / "manifest.json").unlink()
        self.assertEqual(self.codes(), (1, ["MANIFEST"]))
        self.assertEqual(self.codes("--no-manifest"), (0, []))


class UpdateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name)
        self.p.build()
        self.before = self.p.snapshot()

    def finish(self, roles):
        if roles:
            self.assertEqual(self.p.apply_roles(roles)[0], 0)
        for cmd in ("assemble", "finish"):
            self.assertEqual(self.p.run(cmd)[0], 0)

    def test_nothing_changed_means_no_pending_modules_and_identical_output(self):
        self.assertEqual(self.p.extract()["pending"], [])
        self.finish({})
        self.assertEqual({k: v for k, v in self.p.snapshot().items() if k != "manifest.json"}, {k: v for k, v in self.before.items() if k != "manifest.json"})
        by = json.loads((self.p.out / "manifest.json").read_text(encoding="utf-8"))["generated_by"]
        self.assertEqual((by["claude"], by["carried"]), (0, 4))

    def test_editing_one_file_makes_only_its_module_pending_and_other_roles_stay(self):
        path = self.p.root / "src" / "features" / "quiz" / "lib" / "format.ts"
        path.write_text("export function fmt() { return 2; }\n", encoding="utf-8")
        self.assertEqual(self.p.extract()["pending"], ["features/quiz"])
        self.finish({"features/quiz": "新しい役割。"})
        after = self.p.snapshot()
        for name in ("modules/app.md", "modules/features__mindset.md", "modules/(root).md"):
            self.assertEqual(after[name], self.before[name], name)
        self.assertIn("新しい役割。", after["modules/features__quiz.md"].decode("utf-8"))
        by = json.loads((self.p.out / "manifest.json").read_text(encoding="utf-8"))["generated_by"]
        self.assertEqual((by["claude"], by["carried"]), (1, 3))

    def test_a_moved_file_changes_both_modules(self):
        src = self.p.root / "src" / "features" / "quiz" / "lib" / "format.ts"
        dst = self.p.root / "src" / "features" / "mindset" / "format.ts"
        shutil.move(src, dst)
        (self.p.root / "src" / "features" / "quiz" / "index.ts").write_text("export * from \"./lib/streak\";\n", encoding="utf-8")
        (self.p.root / "src" / "features" / "quiz" / "lib" / "streak.ts").write_text("export function computeStreak() { return 1; }\n", encoding="utf-8")
        (self.p.root / "src" / "features" / "mindset" / "mindset.ts").write_text("export const mind = 1;\n", encoding="utf-8")
        self.assertEqual(self.p.extract()["pending"], ["features/mindset", "features/quiz"])

    def test_a_removed_module_loses_its_file_and_its_role(self):
        shutil.rmtree(self.p.root / "src" / "features" / "mindset")
        (self.p.root / "src" / "proxy.ts").write_text("export const p = 1;\n", encoding="utf-8")
        result = self.p.extract()
        self.assertNotIn("features/mindset", result["modules"])
        self.finish({m: "新しい。" for m in result["pending"]})
        self.assertFalse((self.p.out / "modules" / "features__mindset.md").exists())
        roles = [json.loads(l)["module"] for l in (self.p.out / "_raw" / "roles.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertNotIn("features/mindset", roles)


class NotAGitRepoTest(unittest.TestCase):
    def test_a_source_that_is_not_a_git_repo_gets_a_files_and_hash_source_that_follows_the_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, text in TS_FILES.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(text, encoding="utf-8")
            (root / ".qa").mkdir()
            (root / ".qa" / "code-map.toml").write_text(CONFIG, encoding="utf-8")
            run = lambda *a: run_path(CLI, *a, "--config", root / ".qa" / "code-map.toml", cwd=root)
            pending = json.loads(run("extract", "--fresh")[1])["pending"]
            draft = root / "d.jsonl"
            draft.write_text("".join(json.dumps({"module": m, "role": "役割。"}, ensure_ascii=False) + "\n" for m in pending), encoding="utf-8")
            self.assertEqual(run("apply", draft)[0], 0)
            self.assertEqual(run("assemble")[0], 0)
            code, out, err = run("finish")
            self.assertEqual(code, 0, err + out)
            first = json.loads((root / "output" / "code-map" / "manifest.json").read_text(encoding="utf-8"))["source"]
            self.assertEqual(sorted(first), ["files", "hash"])
            self.assertTrue(first["hash"].startswith("sha256:"))
            (root / "src" / "proxy.ts").write_text("export const p = 9;\n", encoding="utf-8")
            run("extract")
            pending = json.loads(run("extract")[1])["pending"]
            draft.write_text("".join(json.dumps({"module": m, "role": "新しい。"}, ensure_ascii=False) + "\n" for m in pending), encoding="utf-8")
            run("apply", draft); run("assemble"); run("finish")
            second = json.loads((root / "output" / "code-map" / "manifest.json").read_text(encoding="utf-8"))["source"]
            self.assertNotEqual(first["hash"], second["hash"])


class DirtyAndSurveyTest(unittest.TestCase):
    def test_uncommitted_changes_under_the_root_are_recorded_as_dirty(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            (p.root / "src" / "proxy.ts").write_text("export const p = 3;\n", encoding="utf-8")
            p.build()
            commit = json.loads((p.out / "manifest.json").read_text(encoding="utf-8"))["source"]["commit"]
            self.assertTrue(commit.endswith("+dirty"))

    def test_survey_counts_source_files_per_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            Project(tmp)
            code, out, err = run_path(CLI, "survey", "--repo-path", tmp, "--root", "src", "--platform", "typescript", cwd=tmp)
            self.assertEqual(code, 0, err)
            counts = json.loads(out)["directories"]
            self.assertEqual(counts["features/quiz"], 3)
            self.assertEqual(counts["features"], 4)
            self.assertEqual(counts["."], 6)


class SampleOutputTest(unittest.TestCase):
    """examples/sample-app/sample-output/code-map/ は、実際に build を実行して得た出力例。
    ソースが無くても、保存してある材料と役割から、modules/ などがそのまま再現できることを確かめる。"""

    SAMPLE = ROOT / "examples" / "sample-app" / "sample-output" / "code-map"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".qa").mkdir()
        shutil.copy(ROOT / "examples" / "sample-app" / ".qa" / "code-map.toml", self.root / ".qa" / "code-map.toml")
        (self.root / "src").mkdir()
        (self.root / ".qa" / "local.toml").write_text(f'[repos]\nsample-app = "{self.root}"\n', encoding="utf-8")
        shutil.copytree(self.SAMPLE, self.root / "output" / "code-map")
        self.out = self.root / "output" / "code-map"

    def run_cli(self, *args):
        return run_path(CLI, *args, "--config", self.root / ".qa" / "code-map.toml", cwd=self.root)

    def test_assemble_reproduces_the_committed_files_byte_for_byte(self):
        committed = {p.relative_to(self.SAMPLE): p.read_bytes() for p in self.SAMPLE.rglob("*") if p.is_file() and p.parts[-2] != "_raw" and p.name != "manifest.json" and "lookup" not in p.parts}
        for name in ("modules", "index.md", "architecture.md", "SKILL.md"):
            path = self.out / name
            shutil.rmtree(path) if path.is_dir() else path.unlink()
        self.assertEqual(self.run_cli("assemble")[0], 0)
        for relative, data in committed.items():
            self.assertEqual((self.out / relative).read_bytes(), data, str(relative))

    def test_the_committed_output_passes_every_check(self):
        code, out, _ = self.run_cli("check", "--json")
        self.assertEqual(code, 0, out)
        stats = json.loads(out)["stats"]
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual((stats["modules"], manifest["items"]), (14, 14))
        self.assertEqual(stats["files"], 78)


class SeparationTest(unittest.TestCase):
    FORBIDDEN = ("typescript", "tsconfig", "TypeScript", "ast.parse")

    def test_nothing_outside_platforms_names_a_language(self):
        offenders = []
        for path in SKILL.rglob("*"):
            if not path.is_file() or "platforms" in path.relative_to(SKILL).parts or path.suffix == ".pyc" or path.name in ("evals.json",):
                continue
            text = path.read_text(encoding="utf-8")
            offenders += [f"{path.relative_to(ROOT)}: {w}" for w in self.FORBIDDEN if w in text]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()


MONOREPO = {
    "package.json": '{"name": "root", "workspaces": ["packages/*", "apps/*"]}',
    "packages/ui/package.json": '{"name": "@acme/ui", "main": "./dist/index.js", "types": "./dist/index.d.ts"}',
    "packages/ui/src/index.ts": 'export * from "./button";\nexport const ui = 1;\n',
    "packages/ui/src/button.ts": "export function Button() { return 1; }\n",
    "packages/ui/src/icons/star.ts": "export const Star = 1;\n",
    "packages/utils/package.json": '{"name": "@acme/utils", "exports": {".": "./src/main.ts"}}',
    "packages/utils/src/main.ts": "export const util = 1;\n",
    "apps/web/tsconfig.json": '{"compilerOptions": {"paths": {"@/*": ["./core/*"], "@/helpers/*": ["./helpers/*"]}}}',
    "apps/web/core/page.ts": 'import { thing } from "@/lib/thing";\nimport { fmt } from "@/helpers/fmt";\nimport { ui } from "@acme/ui";\nimport { Star } from "@acme/ui/icons/star";\nimport { util } from "@acme/utils";\nimport react from "react";\nexport const page = 1;\n',
    "apps/web/core/lib/thing.ts": "export const thing = 1;\n",
    "apps/web/helpers/fmt.ts": "export const fmt = 1;\n",
    "apps/admin/tsconfig.json": '{"compilerOptions": {"paths": {"@/*": ["./src/*"]}}}',
    "apps/admin/src/main.ts": 'import { thing } from "@/lib/thing";\nimport { ui } from "@acme/ui";\nexport const admin = 1;\n',
    "apps/admin/src/lib/thing.ts": "export const thing = 2;\n",
    "apps/web/core/assets/logo.svg": "<svg/>\n",
    "apps/web/core/types/issue.d.ts": "export interface Issue { id: string }\n",
    "apps/web/core/query.ts": 'import logo from "@/assets/logo.svg?url";\nimport type { Issue } from "@/types/issue";\nimport "./missing-generated";\nexport const q = 1;\n',
    "apps/web/.react-router/types/routes.ts": 'import "./app/root";\nexport const r = 1;\n',
}
MONOREPO_CONFIG = CONFIG.replace('root = "src"', 'root = "."').replace('module_depth = 2', 'module_depth = 2').replace('[rules.typescript]\ntsconfig = "tsconfig.json"\n', "")


class MonorepoTest(unittest.TestCase):
    """パッケージごとの tsconfig と、ワークスペースのパッケージ（package.json の name）を解決できること。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Project(self.tmp.name, files=MONOREPO, config=MONOREPO_CONFIG)
        self.p.extract()
        self.reverse = {r["file"]: r["imported_by"] for r in map(json.loads, (self.p.out / "lookup" / "reverse_imports.jsonl").read_text(encoding="utf-8").splitlines())}

    def test_each_file_uses_the_nearest_tsconfig(self):
        self.assertEqual(self.reverse["apps/web/core/lib/thing.ts"], ["apps/web/core/page.ts"])      # web の @/ は ./core
        self.assertEqual(self.reverse["apps/admin/src/lib/thing.ts"], ["apps/admin/src/main.ts"])    # admin の @/ は ./src
        self.assertEqual(self.reverse["apps/web/helpers/fmt.ts"], ["apps/web/core/page.ts"])         # より具体的なパターン

    def test_workspace_packages_resolve_by_name_to_their_source(self):
        self.assertEqual(self.reverse["packages/ui/src/index.ts"], ["apps/admin/src/main.ts", "apps/web/core/page.ts"])   # main は dist/ → src/ に読み替える
        self.assertEqual(self.reverse["packages/ui/src/icons/star.ts"], ["apps/web/core/page.ts"])                         # サブパス
        self.assertEqual(self.reverse["packages/utils/src/main.ts"], ["apps/web/core/page.ts"])                            # exports["."]

    def test_module_level_dependencies_show_the_cross_package_edges(self):
        modules = json.loads((self.p.out / "_raw" / "modules.json").read_text(encoding="utf-8"))
        self.assertEqual(modules["apps/web"]["depends_on"], {"packages/ui": 2, "packages/utils": 1})
        self.assertEqual(modules["packages/ui"]["depended_by"], {"apps/admin": 1, "apps/web": 2})

    def test_asset_queries_and_declaration_files_resolve_and_hidden_folders_are_not_scanned(self):
        tree = (self.p.out / "lookup" / "tree.md").read_text(encoding="utf-8")
        self.assertNotIn(".react-router", tree)                                         # 生成物のフォルダ（ドットで始まる）は読まない
        self.assertEqual(self.reverse["apps/web/core/types/issue.d.ts"], ["apps/web/core/query.ts"])   # @/types/issue → issue.d.ts
        result = json.loads(self.p.run("extract")[1])
        self.assertEqual(result["unresolved"], 1)                                       # ?url の資産は数えず、./missing-generated だけ

    def test_external_packages_are_still_ignored(self):
        self.assertNotIn("react", json.dumps(self.reverse))


class PythonPackageRootTest(unittest.TestCase):
    FILES = {
        "apps/api/plane/__init__.py": "",
        "apps/api/plane/db/__init__.py": "",
        "apps/api/plane/db/models.py": "from plane.utils import helper\nimport plane.utils.helper as h\n",
        "apps/api/plane/utils/__init__.py": "",
        "apps/api/plane/utils/helper.py": "def helper():\n    pass\n",
        "tools/script.py": "import sibling\n",
        "tools/sibling.py": "x = 1\n",
    }

    def test_absolute_imports_resolve_from_the_top_of_the_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = Project(tmp, files=self.FILES, config=CONFIG.replace('["typescript"]', '["python"]').replace('root = "src"', 'root = "."').replace('[rules.typescript]\ntsconfig = "tsconfig.json"\n', ""))
            result = q.extract()
            reverse = {r["file"]: r["imported_by"] for r in map(json.loads, (q.out / "lookup" / "reverse_imports.jsonl").read_text(encoding="utf-8").splitlines())}
            self.assertEqual(reverse["apps/api/plane/utils/helper.py"], ["apps/api/plane/db/models.py"])
            self.assertEqual(reverse["tools/sibling.py"], ["tools/script.py"])
