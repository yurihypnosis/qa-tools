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


def _roots(path, files, root):
    """絶対 import を解決する起点：ファイルが属するパッケージの 1 つ上（`__init__.py` を辿った先）、ファイルのディレクトリ、設定の root。"""
    folder, top = posixpath.dirname(path), None
    while folder and posixpath.join(folder, "__init__.py") in files:
        top, folder = folder, posixpath.dirname(folder)
    roots = [posixpath.dirname(top) if top else None, posixpath.dirname(path), root]
    return [r for i, r in enumerate(roots) if r is not None and r not in roots[:i]]


def analyze(repo, path, text, context):
    files, root = context["files"], context["root"]
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"imports": [], "unresolved": 0, "symbols": []}
    roots = _roots(path, files, root)
    first = lambda candidates: next((h for h in (_module_file(c, files) for c in candidates) if h), None)
    imports, unresolved = set(), 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hit = first(posixpath.normpath(posixpath.join(r, alias.name.replace(".", "/"))) for r in roots)
                if hit:
                    imports.add(hit)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = posixpath.dirname(path)
                for _ in range(node.level - 1):
                    base = posixpath.dirname(base)
                bases = [base]
            else:
                bases = roots
            modules = [posixpath.normpath(posixpath.join(b, node.module.replace(".", "/"))) if node.module else posixpath.normpath(b) for b in bases]
            hits = [h for h in (first([posixpath.join(m, a.name)]) for m in modules for a in node.names) if h] or [h for h in [first(modules)] if h]
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
