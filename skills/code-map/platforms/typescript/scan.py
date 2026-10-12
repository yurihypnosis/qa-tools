"""プラットフォーム定義 typescript：TypeScript / JavaScript のファイルを正規表現で読む（仮の方式。docs/design/tools/code-map.md の 8・12）。"""
import json
import os
import posixpath
import re
from pathlib import Path

EXTENSIONS = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
IMPORTS = [
    re.compile(r"""\b(?:import|export)\b[^;'"`]*?\bfrom\s*['"]([^'"]+)['"]"""),
    re.compile(r"""\bimport\s*['"]([^'"]+)['"]"""),
    re.compile(r"""\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
    re.compile(r"""\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
]
SYMBOL = re.compile(
    r"^export\s+(?:default\s+)?(?:declare\s+)?(?:async\s+)?(function\*?|abstract\s+class|class|interface|type|enum|const)\s+([A-Za-z_$][\w$]*)",
    re.M,
)


def _read_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:  # tsconfig はコメントと末尾のカンマを許す
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"(?m)^\s*//.*$", "", text)
        return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


SKIP_DIRS = {"node_modules", "dist", "build", "venv", "__pycache__"}   # ドットで始まるフォルダは、load() で別に除く


def _extends_target(spec, folder, packages, repo):
    """`extends` の先の tsconfig（リポジトリからの相対パス）。相対パスと、ワークスペースのパッケージ経由だけを辿る。"""
    if spec.startswith("."):
        path = posixpath.normpath(posixpath.join(folder, spec))
    else:
        parts = spec.split("/")
        name = "/".join(parts[:2]) if spec.startswith("@") else parts[0]
        package = packages.get(name)
        if package is None:
            return None
        path = posixpath.normpath(posixpath.join(package["dir"], *parts[len(name.split("/")):] or ["tsconfig.json"]))
    for candidate in (path, path + ".json", posixpath.join(path, "tsconfig.json")):
        if (repo / candidate).is_file():
            return candidate
    return None


def _options(repo, file, packages, depth=0):
    """tsconfig の paths（どこを基準にするか付き）と baseUrl を、`extends` の連鎖を辿って集める。子が paths を持てば、親の paths は置き換わる（TypeScript と同じ）。"""
    result = {"paths": None, "base_url": None}
    try:
        data = _read_json((repo / file).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return result
    folder = posixpath.dirname(file) or "."
    extends = data.get("extends", [])
    for spec in [extends] if isinstance(extends, str) else extends:
        target = _extends_target(spec, folder, packages, repo) if depth < 10 else None
        if target:
            parent = _options(repo, target, packages, depth + 1)
            result = {k: parent[k] if parent[k] is not None else result[k] for k in result}
    options = data.get("compilerOptions", {})
    if "paths" in options:
        result["paths"] = (options["paths"], folder)
    if "baseUrl" in options:
        result["base_url"] = posixpath.normpath(posixpath.join(folder, options["baseUrl"]))
    return result


def _tsconfig(repo, folder, packages):
    options = _options(repo, posixpath.join(folder, "tsconfig.json"), packages)
    paths, origin = options["paths"] or ({}, folder)
    root = options["base_url"] if options["base_url"] is not None else origin   # paths は、baseUrl があればそれを、無ければ定義した tsconfig の場所を基準にする
    return {"paths": {pattern: [posixpath.normpath(posixpath.join(root, t)) for t in targets] for pattern, targets in paths.items()},
            "base_url": options["base_url"]}


def _package(repo, folder):
    try:
        data = json.loads((repo / folder / "package.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data.get("name"), str):
        return None
    entries = [data.get(k) for k in ("source", "module", "main", "types")]
    exports = data.get("exports")
    if isinstance(exports, dict) and "." in exports:
        exports = exports["."]
    if isinstance(exports, str):
        entries.append(exports)
    elif isinstance(exports, dict):
        entries += [exports.get(k) for k in ("import", "default", "types")]
    return {"name": data["name"], "dir": folder, "entries": [e for e in entries if isinstance(e, str)]}


def load(repo, options):
    """ディレクトリごとの tsconfig（ファイルは、いちばん近い祖先のものを使い、`extends` も辿る）と、ワークスペースのパッケージ（package.json の name）を集める。"""
    tsconfigs, packages = [], {}
    for folder, dirs, names in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        rel = posixpath.relpath(Path(folder).as_posix(), repo.as_posix())
        if "tsconfig.json" in names:
            tsconfigs.append(rel)
        if "package.json" in names:
            package = _package(repo, rel)
            if package:
                packages[package["name"]] = package
    return {"configs": {rel: _tsconfig(repo, rel, packages) for rel in tsconfigs}, "packages": packages}


def _try(base, files):
    candidates = [base] + [base + ext for ext in EXTENSIONS] + [base + ".d.ts"] + [posixpath.join(base, "index" + ext) for ext in EXTENSIONS]
    stem, ext = posixpath.splitext(base)
    if ext in (".js", ".jsx", ".mjs", ".cjs"):  # ESM の書き方：./a.js が実際は a.ts
        candidates += [stem + e for e in EXTENSIONS]
    return next((c for c in candidates if c in files), None)


def _nearest_config(path, configs):
    folder = posixpath.dirname(path) or "."
    while True:
        if folder in configs:
            return configs[folder]
        if folder == ".":
            return {"paths": {}, "base_url": None}
        folder = posixpath.dirname(folder) or "."


def _workspace(spec, context):
    """`@scope/name` や `@scope/name/sub` を、ワークスペースのパッケージのソースに解決する。"""
    packages = context["packages"]
    name = next((n for n in sorted(packages, key=len, reverse=True) if spec == n or spec.startswith(n + "/")), None)
    if name is None:
        return None
    package, sub = packages[name], spec[len(name) + 1:]
    base = package["dir"]
    if sub:
        candidates = [posixpath.join(base, "src", sub), posixpath.join(base, sub)]
    else:
        candidates = []
        for entry in package["entries"]:
            path = posixpath.normpath(posixpath.join(base, entry))
            candidates += [path, path.replace("/dist/", "/src/", 1), posixpath.splitext(path)[0], posixpath.splitext(path.replace("/dist/", "/src/", 1))[0]]
        candidates += [posixpath.join(base, "src", "index"), posixpath.join(base, "index")]
    return next((hit for hit in (_try(c, context["files"]) for c in candidates) if hit), None)


def _resolve(spec, importer, context):
    spec = spec.split("?")[0]   # logo.svg?url のような、ビルドツールのクエリ
    files = context["files"]
    if spec.startswith("."):
        base = posixpath.normpath(posixpath.join(posixpath.dirname(importer), spec))
        hit = _try(base, files)
        if hit:
            return hit, "internal"
        return None, "asset" if base in context["on_disk"] else "unresolved"
    config = _nearest_config(importer, context["configs"])
    # より具体的なパターン（長い接頭辞）を先に試す
    for pattern in sorted(config["paths"], key=len, reverse=True):
        if pattern.endswith("*") and spec.startswith(pattern[:-1]):
            rest = spec[len(pattern) - 1:]
        elif pattern == spec:
            rest = ""
        else:
            continue
        targets = config["paths"][pattern]
        for target in targets:
            hit = _try(target.replace("*", rest), files)
            if hit:
                return hit, "internal"
        on_disk = any(target.replace("*", rest) in context["on_disk"] for target in targets)  # JSON や画像などの資産
        return None, "asset" if on_disk else "unresolved"
    if config["base_url"] is not None:
        hit = _try(posixpath.normpath(posixpath.join(config["base_url"], spec)), files)
        if hit:
            return hit, "internal"
    hit = _workspace(spec, context)
    return (hit, "internal") if hit else (None, "external")


def analyze(repo, path, text, context):
    imports, unresolved = set(), 0
    for pattern in IMPORTS:
        for spec in pattern.findall(text):
            target, kind = _resolve(spec, path, context)
            if kind == "internal" and target != path:
                imports.add(target)
            elif kind == "unresolved":
                unresolved += 1
    symbols = []
    for match in SYMBOL.finditer(text):
        kind = match.group(1).split()[-1].rstrip("*")
        symbols.append({"name": match.group(2), "kind": kind, "line": text.count("\n", 0, match.start()) + 1})
    return {"imports": sorted(imports), "unresolved": unresolved, "symbols": symbols}
