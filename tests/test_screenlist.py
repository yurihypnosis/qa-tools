"""screen-list（docs/design/tools/screen-list.md）。小さな Next.js 風のアプリで、候補の列挙から更新まで通しで確かめる。"""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT, run_path

SKILL = ROOT / "skills" / "screen-list"
CLI = SKILL / "scripts" / "screens.py"
CODEMAP = ROOT / "skills" / "code-map" / "scripts" / "codemap.py"

APP = {
    "tsconfig.json": '{"compilerOptions": {"paths": {"@/*": ["./src/*"]}}}',
    "src/app/layout.tsx": 'import { Shell } from "@/components/shell";\nexport default function Layout() { return null; }\n',
    "src/app/page.tsx": 'import { Shell } from "@/components/shell";\n\nexport default function Home() { return null; }\n',
    "src/app/(auth)/login/page.tsx": 'export default function Login() { return null; }\n',
    "src/app/(main)/tasks/page.tsx": 'import { TaskList } from "@/features/tasks/task-list";\nexport default function Tasks() { return null; }\n',
    "src/app/(main)/tasks/[id]/page.tsx": 'import { EditDialog } from "@/features/tasks/edit-dialog";\nexport default function Task() { return null; }\n',
    "src/app/@modal/preview/page.tsx": "export default function P() { return null; }\n",
    "src/app/_private/page.tsx": "export default function Q() { return null; }\n",
    "src/app/(.)photo/page.tsx": "export default function R() { return null; }\n",
    "src/components/ui/dialog.tsx": "export function Dialog() { return null; }\n",
    "src/components/shell.tsx": 'import { Dialog } from "@/components/ui/dialog";\nexport function Shell() { return null; }\n',
    "src/features/tasks/task-list.tsx": 'import { DeleteDialog } from "./delete-dialog";\nexport function TaskList() { return null; }\n',
    "src/features/tasks/delete-dialog.tsx": 'import { Dialog } from "@/components/ui/dialog";\nexport function DeleteDialog() { return null; }\n',
    "src/features/tasks/edit-dialog.tsx": 'import { Dialog } from "@/components/ui/dialog";\nexport function EditDialog() { return null; }\n',
}
CODEMAP_TOML = """platform = ["typescript"]
[source]
repo = "."
root = "src"
[output]
dir = "output/code-map"
[rules]
module_depth = 2
[rules.typescript]
tsconfig = "tsconfig.json"
[checks]
run = ["public-files"]
"""
SCREENS_TOML = """platform = "nextjs-app-router"

[source]
repo = "."
root = "src"
code_map = "output/code-map"

[output]
dir = "output/screen-list"

[rules]
dialog_imports = ["src/components/ui/dialog"]
roles = ["管理者", "一般ユーザー"]
exclude = []

[checks]
run = ["coverage"]
"""
EXPECTED = {
    "web#src/components/shell": ("ダイアログ", "", "web/index"),
    "web#src/features/tasks/delete-dialog": ("ダイアログ", "", "web/tasks"),
    "web#src/features/tasks/edit-dialog": ("ダイアログ", "", "web/tasks/[id]"),
    "web/index": ("画面", "/", ""),
    "web/login": ("画面", "/login", ""),
    "web/tasks": ("画面", "/tasks", ""),
    "web/tasks/[id]": ("画面", "/tasks/[id]", ""),
}


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


class Setup:
    def __init__(self, tmp, screens=SCREENS_TOML, files=APP):
        self.root = Path(tmp)
        for name, text in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (self.root / ".qa").mkdir(exist_ok=True)
        (self.root / ".qa" / "code-map.toml").write_text(CODEMAP_TOML, encoding="utf-8")
        (self.root / ".qa" / "screen-list.toml").write_text(screens, encoding="utf-8")
        for args in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"]):
            git(self.root, *args)
        self.commit()
        self.refresh_code_map(fresh=True)
        self.out = self.root / "output" / "screen-list"

    def commit(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "c", "--allow-empty")

    def refresh_code_map(self, fresh=False):
        cmd = lambda *a: run_path(CODEMAP, *a, "--config", self.root / ".qa" / "code-map.toml", cwd=self.root)
        code, out, err = cmd("extract", *(["--fresh"] if fresh else []))
        assert code == 0, err
        pending = json.loads(out)["pending"]
        if pending:
            draft = self.root / "cm-draft.jsonl"
            draft.write_text("".join(json.dumps({"module": m, "role": "役割。"}, ensure_ascii=False) + "\n" for m in pending), encoding="utf-8")
            assert cmd("apply", draft)[0] == 0
        for c in ("assemble", "finish"):
            code, _, err = cmd(c)
            assert code == 0, err

    def run(self, *args):
        return run_path(CLI, *args, "--config", self.root / ".qa" / "screen-list.toml", cwd=self.root)

    def candidates(self, *args):
        code, out, err = self.run("candidates", *args)
        assert code == 0, err
        return json.loads(out)

    def apply_names(self, rows):
        draft = self.root / "draft.jsonl"
        draft.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        return self.run("apply", draft)

    def names_for(self, ids, roles=("全員",)):
        return [{"id": i, "name": f"名前:{i}", "roles": list(roles)} for i in ids]

    def build(self):
        pending = self.candidates("--fresh")["pending"]
        code, _, err = self.apply_names(self.names_for(pending))
        assert code == 0, err
        for c in ("merge", "finish"):
            code, _, err = self.run(c)
            assert code == 0, err

    def rows(self):
        with open(self.out / "screens.csv", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))


class CandidatesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.s = Setup(self.tmp.name)

    def candidates(self):
        return {c["id"]: c for c in map(json.loads, (self.s.out / "_raw" / "candidates.jsonl").read_text(encoding="utf-8").splitlines())}

    def test_pages_and_dialogs_with_ids_urls_and_parents(self):
        result = self.s.candidates()
        self.assertEqual(result["pending"], sorted(EXPECTED))
        got = self.candidates()
        self.assertEqual({i: (c["kind"], c["url"], ";".join(c["parents"])) for i, c in got.items()}, EXPECTED)

    def test_route_groups_private_slot_and_intercepting_folders(self):
        ids = set(self.s.candidates()["pending"])
        self.assertNotIn("web/preview", ids)          # @modal
        self.assertFalse([i for i in ids if "_private" in i or "photo" in i])
        self.assertIn("web/login", ids)               # (auth) は URL に含めない

    def test_source_line_is_the_default_export_line_and_one_for_dialogs(self):
        self.s.candidates()
        got = self.candidates()
        self.assertEqual(got["web/index"]["file"] + ":" + str(got["web/index"]["line"]), "src/app/page.tsx:3")
        self.assertEqual(got["web/login"]["line"], 1)
        self.assertEqual(got["web#src/features/tasks/delete-dialog"]["line"], 1)

    def test_no_dialog_imports_means_no_dialog_candidates(self):
        self.s.candidates()
        text = (self.s.root / ".qa" / "screen-list.toml").read_text(encoding="utf-8").replace('dialog_imports = ["src/components/ui/dialog"]', "dialog_imports = []")
        (self.s.root / ".qa" / "screen-list.toml").write_text(text, encoding="utf-8")
        self.assertEqual([i for i in self.s.candidates("--fresh")["pending"] if "#" in i], [])

    def test_declared_extra_screens_become_candidates_with_their_parent(self):
        text = (self.s.root / ".qa" / "screen-list.toml").read_text(encoding="utf-8") + (
            '\n[[rules.extra]]\nkey = "index?screen=analysis"\nsource = "src/features/tasks/task-list.tsx"\nparent = "web/index"\n')
        text = text.replace("[checks]", "[checks]")
        (self.s.root / ".qa" / "screen-list.toml").write_text(text.replace("[checks]\nrun = [\"coverage\"]\n", "") + "\n[checks]\nrun = [\"coverage\"]\n", encoding="utf-8")
        self.assertIn("web/index?screen=analysis", self.s.candidates("--fresh")["pending"])
        extra = self.candidates()["web/index?screen=analysis"]
        self.assertEqual((extra["kind"], extra["url"], extra["parents"], extra["file"]), ("画面", "", ["web/index"], "src/features/tasks/task-list.tsx"))

    def test_exclude_removes_a_candidate_and_an_unknown_id_is_an_error(self):
        path = self.s.root / ".qa" / "screen-list.toml"
        path.write_text(SCREENS_TOML.replace("exclude = []", 'exclude = ["web/login"]'), encoding="utf-8")
        self.assertNotIn("web/login", self.s.candidates("--fresh")["pending"])
        path.write_text(SCREENS_TOML.replace("exclude = []", 'exclude = ["web/nope"]'), encoding="utf-8")
        code, _, err = self.s.run("candidates")
        self.assertEqual(code, 2)
        self.assertIn("web/nope", err)

    def test_modules_come_from_the_code_map_tree(self):
        self.s.candidates()
        got = self.candidates()
        self.assertEqual(got["web/tasks"]["module"], "app/(main)")
        self.assertEqual(got["web#src/features/tasks/delete-dialog"]["module"], "features/tasks")

    def test_a_stale_code_map_stops_with_advice(self):
        (self.s.root / "src" / "app" / "(auth)" / "login" / "page.tsx").write_text("export default function Login() { return 1; }\n", encoding="utf-8")
        self.s.commit()
        code, _, err = self.s.run("candidates")
        self.assertEqual(code, 2)
        self.assertIn("code-map", err)

    def test_uncommitted_changes_since_the_code_map_also_make_it_stale(self):
        (self.s.root / "src" / "app" / "(auth)" / "login" / "page.tsx").write_text("export default function Login() { return 2; }\n", encoding="utf-8")  # コミットしない
        code, _, err = self.s.run("candidates")
        self.assertEqual(code, 2)
        self.assertIn("+dirty", err)
        self.s.refresh_code_map()    # code-map も dirty で作り直せば、同じ状態なので通る
        self.assertEqual(self.s.run("candidates")[0], 0)

    def test_missing_roles_key_or_code_map_output_is_a_config_error(self):
        path = self.s.root / ".qa" / "screen-list.toml"
        path.write_text(SCREENS_TOML.replace('roles = ["管理者", "一般ユーザー"]\n', ""), encoding="utf-8")
        code, _, err = self.s.run("candidates")
        self.assertEqual((code, "roles" in err), (2, True))
        path.write_text(SCREENS_TOML.replace('code_map = "output/code-map"', 'code_map = "output/none"'), encoding="utf-8")
        code, _, err = self.s.run("candidates")
        self.assertEqual((code, "code-map" in err), (2, True))

    def test_duplicate_ids_stop_the_run(self):
        text = SCREENS_TOML + '\n[[rules.extra]]\nkey = "login"\nsource = "src/app/page.tsx"\nparent = "web/index"\n'
        (self.s.root / ".qa" / "screen-list.toml").write_text(text.replace("[checks]\nrun = [\"coverage\"]\n", "") + "\n[checks]\nrun = [\"coverage\"]\n", encoding="utf-8")
        code, _, err = self.s.run("candidates")
        self.assertEqual(code, 2)
        self.assertIn("web/login", err)


class NamesAndMergeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.s = Setup(self.tmp.name)
        self.ids = self.s.candidates("--fresh")["pending"]

    def test_apply_rejects_bad_rows_and_writes_nothing(self):
        good = {"id": "web/login", "name": "ログイン", "roles": ["全員"]}
        bad = [{"id": "web/nope", "name": "x", "roles": ["全員"]}, {"id": "web/index", "name": " ", "roles": ["全員"]},
               {"id": "web/index", "name": "あ" * 81, "roles": ["全員"]}, {"id": "web/index", "name": "x", "roles": ["社長"]},
               {"id": "web/index", "name": "x", "roles": "全員"}, {"id": "web/index", "name": "x"},
               {"id": "web/index", "name": "x", "roles": ["全員"], "note": "余計"}]
        for row in bad:
            with self.subTest(row=row):
                code, _, err = self.s.apply_names([good, row])
                self.assertEqual(code, 2)
                self.assertIn("draft.jsonl", err)
                self.assertEqual((self.s.out / "_raw" / "names.jsonl").read_text(encoding="utf-8"), "")

    def test_names_that_a_spreadsheet_would_run_as_a_formula_are_rejected(self):
        for name in ('=HYPERLINK("http://x","y")', "+1", "@SUM(A1)", "-1", "\t=1"):
            with self.subTest(name=name):
                code, _, err = self.s.apply_names([{"id": "web/login", "name": name, "roles": ["全員"]}])
                self.assertEqual(code, 2)
                self.assertIn("式", err)
        self.assertEqual(self.s.apply_names([{"id": "web/login", "name": "1 ページ目", "roles": ["全員"]}, {"id": "web/index", "name": "ログイン", "roles": ["全員"]}])[0], 0)

    def test_a_role_name_with_a_semicolon_is_a_config_error(self):
        (self.s.root / ".qa" / "screen-list.toml").write_text(SCREENS_TOML.replace('roles = ["管理者", "一般ユーザー"]', 'roles = ["管理者;一般"]'), encoding="utf-8")
        code, _, err = self.s.run("candidates")
        self.assertEqual((code, ";" in err), (2, True))

    def test_roles_may_be_in_the_vocabulary_or_unresolved(self):
        rows = [{"id": "web/login", "name": "ログイン", "roles": ["管理者", "一般ユーザー"]}, {"id": "web/index", "name": "トップ", "roles": ["[未解決: ガードが見つからない]"]}]
        self.assertEqual(self.s.apply_names(rows)[0], 0)

    def test_merge_without_every_name_lists_the_missing_ids(self):
        self.assertEqual(self.s.apply_names(self.s.names_for(["web/login"]))[0], 0)
        code, _, err = self.s.run("merge")
        self.assertEqual(code, 2)
        self.assertIn("web/tasks", err)

    def test_merge_writes_the_csv_with_fixed_columns_bom_and_sorted_ids(self):
        rows = self.s.names_for(self.ids)
        rows[[r["id"] for r in rows].index("web/login")]["roles"] = ["管理者", "一般ユーザー"]
        self.assertEqual(self.s.apply_names(rows)[0], 0)
        self.assertEqual(self.s.run("merge")[0], 0)
        raw = (self.s.out / "screens.csv").read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        table = self.s.rows()
        self.assertEqual(list(table[0]), ["画面ID", "画面名", "種別", "ロール", "URL", "ソース", "モジュール", "親画面ID"])
        self.assertEqual([r["画面ID"] for r in table], sorted(EXPECTED))
        by = {r["画面ID"]: r for r in table}
        self.assertEqual(by["web/login"]["ロール"], "管理者;一般ユーザー")
        self.assertEqual((by["web/tasks"]["種別"], by["web/tasks"]["URL"], by["web/tasks"]["モジュール"], by["web/tasks"]["ソース"]), ("画面", "/tasks", "app/(main)", "src/app/(main)/tasks/page.tsx:2"))
        self.assertEqual((by["web#src/features/tasks/edit-dialog"]["親画面ID"], by["web#src/features/tasks/edit-dialog"]["URL"]), ("web/tasks/[id]", ""))


class CheckAndFinishTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.s = Setup(self.tmp.name)
        self.s.build()

    def write_rows(self, rows):
        with open(self.s.out / "screens.csv", "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def check(self, *args):
        code, out, _ = self.s.run("check", "--json", *args)
        receipt = json.loads(out)
        return code, sorted({f["code"] for f in receipt["findings"]}), receipt

    def test_a_clean_build_passes_with_stats_and_a_manifest_with_inputs(self):
        code, codes, receipt = self.check()
        self.assertEqual((code, codes), (0, []))
        self.assertEqual((receipt["stats"]["candidates"], receipt["stats"]["rows"], receipt["stats"]["dialogs"], receipt["stats"]["unresolved"]), (7, 7, 3, 0))
        manifest = json.loads((self.s.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual((manifest["tool"], manifest["items"], manifest["generated_by"]["claude"], manifest["generated_by"]["carried"]), ("screen-list", 7, 7, 0))
        code_map = json.loads((self.s.root / "output" / "code-map" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["inputs"], {"code-map": code_map["source"]})
        self.assertEqual(run_path(ROOT / "core" / "manifest.py", "check", self.s.out)[0], 0)

    def test_coverage_value_duplicate_and_manifest(self):
        rows = self.s.rows()
        self.write_rows(rows[1:])
        self.assertEqual(self.check()[:2], (1, ["COVERAGE"]))
        self.write_rows(rows + [dict(rows[0])])
        self.assertIn("DUPLICATE_ID", self.check()[1])
        bad = [dict(r) for r in rows]
        bad[0]["ロール"] = "社長"
        self.write_rows(bad)
        self.assertEqual(self.check()[:2], (1, ["VALUE"]))
        bad[0]["ロール"] = "全員"
        bad[0]["種別"] = "ページ"
        self.write_rows(bad)
        self.assertEqual(self.check()[:2], (1, ["VALUE"]))
        self.write_rows(rows)
        (self.s.out / "manifest.json").unlink()
        self.assertEqual(self.check()[:2], (1, ["MANIFEST"]))
        self.assertEqual(self.check("--no-manifest")[:2], (0, []))

    def test_unresolved_names_and_roles_are_counted_not_failed(self):
        rows = self.s.rows()
        rows[0]["ロール"] = "[未解決: ガードが見つからない]"
        self.write_rows(rows)
        code, codes, receipt = self.check()
        self.assertEqual((code, receipt["stats"]["unresolved"]), (0, 1))

    def test_finish_does_not_touch_the_manifest_when_the_check_fails(self):
        before = (self.s.out / "manifest.json").read_bytes()
        self.write_rows(self.s.rows()[1:])
        self.assertEqual(self.s.run("finish")[0], 1)
        self.assertEqual((self.s.out / "manifest.json").read_bytes(), before)


class UpdateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.s = Setup(self.tmp.name)
        self.s.build()
        self.before = (self.s.out / "screens.csv").read_bytes()

    def update(self, names=None):
        self.s.commit()
        self.s.refresh_code_map()
        result = self.s.candidates()
        if result["pending"]:
            self.assertEqual(self.s.apply_names(names or self.s.names_for(result["pending"], roles=("管理者",)))[0], 0)
        for c in ("merge", "finish"):
            self.assertEqual(self.s.run(c)[0], 0)
        return result["pending"]

    def test_nothing_changed_means_nothing_pending_and_an_identical_csv(self):
        self.assertEqual(self.update(), [])
        self.assertEqual((self.s.out / "screens.csv").read_bytes(), self.before)
        by = json.loads((self.s.out / "manifest.json").read_text(encoding="utf-8"))["generated_by"]
        self.assertEqual((by["claude"], by["carried"]), (0, 7))

    def test_editing_one_page_rewrites_only_that_row(self):
        (self.s.root / "src" / "app" / "(auth)" / "login" / "page.tsx").write_text("export default function Login() { return 1; }\n", encoding="utf-8")
        self.assertEqual(self.update(), ["web/login"])
        rows = {r["画面ID"]: r for r in self.s.rows()}
        self.assertEqual(rows["web/login"]["ロール"], "管理者")
        self.assertEqual(rows["web/tasks"]["ロール"], "全員")      # 使い回し
        by = json.loads((self.s.out / "manifest.json").read_text(encoding="utf-8"))["generated_by"]
        self.assertEqual((by["claude"], by["carried"]), (1, 6))

    def test_a_dialog_whose_parent_changes_is_rewritten(self):
        path = self.s.root / "src" / "app" / "(main)" / "tasks" / "page.tsx"
        path.write_text('export default function Tasks() { return null; }\n', encoding="utf-8")   # task-list を import しなくなる
        (self.s.root / "src" / "app" / "page.tsx").write_text('import { TaskList } from "@/features/tasks/task-list";\nimport { Shell } from "@/components/shell";\n\nexport default function Home() { return null; }\n', encoding="utf-8")
        pending = self.update()
        self.assertIn("web#src/features/tasks/delete-dialog", pending)
        self.assertEqual({r["画面ID"]: r for r in self.s.rows()}["web#src/features/tasks/delete-dialog"]["親画面ID"], "web/index")

    def test_a_removed_page_leaves_the_csv(self):
        import shutil
        shutil.rmtree(self.s.root / "src" / "app" / "(auth)")
        self.assertEqual(self.update(), [])
        self.assertNotIn("web/login", [r["画面ID"] for r in self.s.rows()])


class SampleOutputTest(unittest.TestCase):
    """examples/sample-app/sample-output/screen-list/ は、実際に build を実行して得た出力例。
    保存してある候補と名前から、CSV がそのまま再現できることと、検査に通ることを確かめる（ソースは要らない）。"""

    SAMPLE = ROOT / "examples" / "sample-app" / "sample-output" / "screen-list"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".qa").mkdir()
        (self.root / ".qa" / "screen-list.toml").write_bytes((ROOT / "examples" / "sample-app" / ".qa" / "screen-list.toml").read_bytes())
        (self.root / ".qa" / "local.toml").write_text(f'[repos]\nsample-app = "{self.root}"\n', encoding="utf-8")
        import shutil
        shutil.copytree(self.SAMPLE, self.root / "output" / "screen-list")
        self.out = self.root / "output" / "screen-list"

    def run_cli(self, *args):
        return run_path(CLI, *args, "--config", self.root / ".qa" / "screen-list.toml", cwd=self.root)

    def test_merge_reproduces_the_committed_csv_byte_for_byte(self):
        (self.out / "screens.csv").unlink()
        self.assertEqual(self.run_cli("merge")[0], 0)
        self.assertEqual((self.out / "screens.csv").read_bytes(), (self.SAMPLE / "screens.csv").read_bytes())

    def test_the_committed_output_passes_every_check(self):
        code, out, _ = self.run_cli("check", "--json")
        self.assertEqual(code, 0, out)
        stats = json.loads(out)["stats"]
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual((stats["candidates"], stats["rows"], manifest["items"]), (13, 13, 13))
        self.assertEqual(manifest["inputs"]["code-map"]["commit"], manifest["source"]["commit"])


class SeparationAndSampleTest(unittest.TestCase):
    FORBIDDEN = ("nextjs", "page.tsx", "App Router", "app router")

    def test_nothing_outside_platforms_names_the_framework(self):
        offenders = []
        for path in SKILL.rglob("*"):
            if not path.is_file() or "platforms" in path.relative_to(SKILL).parts or path.suffix == ".pyc" or path.name == "evals.json":
                continue
            text = path.read_text(encoding="utf-8")
            offenders += [f"{path.relative_to(ROOT)}: {w}" for w in self.FORBIDDEN if w in text]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
