"""プラットフォーム定義 python：標準ライブラリの ast で import とシンボルを読む（docs/design/tools/code-map.md の 8）。"""
import ast
import posixpath

EXTENSIONS = (".py",)


def load(repo, options):
    return {}


def _module_file(base, files):
    """`a/b` が、ファイル `a/b.py` かパッケージ `a/b/__init__.py` かを調べる。"""
    for candidate in (base + ".py", posixpath.join(base, "__init__.py")):
        if candidate in files:
            return candidate
    return None


def analyze(repo, path, text, context):
    files, root = context["files"], context["root"]
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"imports": [], "unresolved": 0, "symbols": []}
    imports, unresolved = set(), 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hit = _module_file(posixpath.normpath(posixpath.join(root, alias.name.replace(".", "/"))), files)
                if hit:
                    imports.add(hit)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = posixpath.dirname(path)
                for _ in range(node.level - 1):
                    base = posixpath.dirname(base)
            else:
                base = root
            module = posixpath.normpath(posixpath.join(base, node.module.replace(".", "/"))) if node.module else base
            hits = [_module_file(posixpath.join(module, a.name), files) for a in node.names]  # from x import 部分モジュール
            hits = [h for h in hits if h] or [_module_file(module, files)]
            hits = [h for h in hits if h]
            if hits:
                imports.update(hits)
            elif node.level:
                unresolved += 1
    symbols = [
        {"name": n.name, "kind": "class" if isinstance(n, ast.ClassDef) else "function", "line": n.lineno}
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith("_")
    ]
    return {"imports": sorted(imports - {path}), "unresolved": unresolved, "symbols": symbols}
