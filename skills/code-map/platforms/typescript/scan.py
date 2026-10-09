"""プラットフォーム定義 typescript：TypeScript / JavaScript のファイルを正規表現で読む（仮の方式。docs/design/tools/code-map.md の 8・12）。"""
import json
import posixpath
import re

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


def load(repo, options):
    """tsconfig の `paths` と `baseUrl` を、リポジトリからの相対パスにして返す。tsconfig が無ければ別名なし。"""
    rel = options.get("tsconfig", "tsconfig.json")
    path = repo / rel
    if not path.is_file():
        return {"paths": {}, "base_url": None}
    try:
        options_ = _read_json(path.read_text(encoding="utf-8")).get("compilerOptions", {})
    except json.JSONDecodeError as error:
        raise ValueError(f"{rel} を JSON として読めない: {error}") from None
    folder = posixpath.dirname(rel)
    join = lambda p: posixpath.normpath(posixpath.join(folder, p))
    base = options_.get("baseUrl")
    return {
        "paths": {pattern: [join(t) for t in targets] for pattern, targets in options_.get("paths", {}).items()},
        "base_url": join(base) if base is not None else None,
        "folder": folder,
    }


def _try(base, files):
    candidates = [base] + [base + ext for ext in EXTENSIONS] + [posixpath.join(base, "index" + ext) for ext in EXTENSIONS]
    stem, ext = posixpath.splitext(base)
    if ext in (".js", ".jsx", ".mjs", ".cjs"):  # ESM の書き方：./a.js が実際は a.ts
        candidates += [stem + e for e in EXTENSIONS]
    return next((c for c in candidates if c in files), None)


def _resolve(spec, importer, context):
    files = context["files"]
    if spec.startswith("."):
        base = posixpath.normpath(posixpath.join(posixpath.dirname(importer), spec))
        hit = _try(base, files)
        if hit:
            return hit, "internal"
        return None, "asset" if base in context["on_disk"] else "unresolved"
    for pattern, targets in context["paths"].items():
        if pattern.endswith("*") and spec.startswith(pattern[:-1]):
            rest = spec[len(pattern) - 1:]
        elif pattern == spec:
            rest = ""
        else:
            continue
        for target in targets:
            hit = _try(target.replace("*", rest), files)
            if hit:
                return hit, "internal"
        on_disk = any(target.replace("*", rest) in context["on_disk"] for target in targets)  # JSON や画像などの資産
        return None, "asset" if on_disk else "unresolved"
    if context["base_url"] is not None:
        hit = _try(posixpath.normpath(posixpath.join(context["base_url"], spec)), files)
        if hit:
            return hit, "internal"
    return None, "external"


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
