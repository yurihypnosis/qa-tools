"""ダミーアプリ（examples/dummy-product/app/）の構成の検証。

test-steps・code-map・screen-list の共通の入力なので、ツールが前提にする形が崩れていないかを確かめる。
"""
import json
import re
import unittest

from tests.helpers import ROOT

APP = ROOT / "examples" / "dummy-product" / "app"
NOTICE = "テスト用のダミー"


class DummyAppTest(unittest.TestCase):
    def files(self):
        files = [p for p in APP.rglob("*") if p.is_file()]
        self.assertTrue(files)
        return files

    def test_every_file_says_it_is_a_dummy_near_the_top(self):
        for path in self.files():
            with self.subTest(path=str(path.relative_to(APP))):
                head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:3])
                self.assertIn(NOTICE, head)

    def test_routes_define_six_screens(self):
        text = (APP / "src" / "routes.ts").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^\s*\{\s*path:", text, re.M)), 6)

    def test_two_dialogs_use_the_shared_dialog_component(self):
        dialogs = sorted((APP / "src" / "components" / "dialogs").glob("*.tsx"))
        self.assertEqual(len(dialogs), 2)
        for path in dialogs:
            with self.subTest(dialog=path.name):
                self.assertIn('from "../ui/Dialog"', path.read_text(encoding="utf-8"))

    def test_backend_has_three_python_modules(self):
        modules = sorted(p.stem for p in (APP / "backend").glob("*.py") if p.stem != "__init__")
        self.assertEqual(modules, ["auth", "tasks", "users"])

    def test_three_specs_and_a_fixture_reached_through_a_tsconfig_path(self):
        specs = sorted(p.name for p in (APP / "e2e").glob("*.spec.ts"))
        self.assertEqual(specs, ["login.spec.ts", "task-create.spec.ts", "task-delete.spec.ts"])
        paths = json.loads((APP / "tsconfig.json").read_text(encoding="utf-8"))["compilerOptions"]["paths"]
        self.assertEqual(len(paths), 1)
        alias = next(iter(paths)).removesuffix("*")
        uses = [p for p in (APP / "e2e").glob("*.spec.ts") if f'from "{alias}' in p.read_text(encoding="utf-8")]
        self.assertTrue(uses)


if __name__ == "__main__":
    unittest.main()
