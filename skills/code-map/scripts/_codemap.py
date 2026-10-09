"""code-map の処理（標準ライブラリのみ）。仕様：docs/design/tools/code-map.md

エラーはすべて ValueError（メッセージは、何をすればよいかを含む）。CLI が終了コード 2 にする。
"""
import fnmatch
import hashlib
import importlib.util
import json
import os
import posixpath
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR.parent.parent / "core"))  # contracts.md の C7
import carry  # noqa: E402
import config as cfg  # noqa: E402
import gitinfo  # noqa: E402
import jsonl  # noqa: E402
import manifest  # noqa: E402

ALWAYS_EXCLUDED = {".git", "node_modules", "__pycache__", ".next", "dist", "build"}
SECTIONS = ["役割", "主なファイル", "公開シンボル", "依存先", "依存元"]
MAX_ROLE = 600  # 役割は 2〜4 文。長すぎる下書きは、要約になっていない


# --- 設定と言語 -----------------------------------------------------------------

def available_platforms():
    return sorted(p.name for p in (SKILL_DIR / "platforms").iterdir() if p.is_dir())


def load_platform(name):
    path = SKILL_DIR / "platforms" / name / "scan.py"
    if not path.is_file():
        raise ValueError(f"言語 {name!r} のプラットフォーム定義が無い。選べるもの: {', '.join(available_platforms())}")
    spec = importlib.util.spec_from_file_location(f"scan_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_config(path):
    raw = cfg.load(path)
    platforms = raw["platform"]
    if not (isinstance(platforms, list) and platforms and all(isinstance(p, str) for p in platforms)):
        raise ValueError("platform は言語の名前の配列（例：[\"a\", \"b\"]）")
    source, rules = raw["source"], raw.get("rules", {})
    for key in ("repo", "root"):
        if not isinstance(source.get(key), str):
            raise ValueError(f"source.{key} が無い")
    if not isinstance(raw["output"].get("dir"), str):
        raise ValueError("output.dir が無い")
    depth = rules.get("module_depth")
    if not (isinstance(depth, int) and depth >= 1):
        raise ValueError(f"rules.module_depth は 1 以上の整数: {depth!r}")
    project = cfg.project_root(path)
    repo = cfg.resolve_repo(project, source["repo"])
    return {
        "path": Path(path), "project": project, "repo": repo, "repo_name": source["repo"],
        "root": posixpath.normpath(source["root"]), "exclude": list(source.get("exclude", [])),
        "out": project / raw["output"]["dir"], "platforms": platforms, "depth": depth,
        "representatives": rules.get("representatives", 5), "rules": rules,
    }


# --- 抽出 ---------------------------------------------------------------------

def collect(config):
    """(ソースのファイル, ディスク上の全ファイル) をリポジトリからの相対パス（`/` 区切り）で返す。"""
    repo, root = config["repo"], config["root"]
    base = repo / root
    if not base.is_dir():
        raise ValueError(f"source.root {root!r} が {repo} の下に無い")
    on_disk = set()
    for folder, dirs, names in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in ALWAYS_EXCLUDED)
        for name in names:
            on_disk.add(Path(folder, name).relative_to(repo).as_posix())
    return on_disk


def module_of(config, path):
    parts = posixpath.relpath(path, config["root"]).split("/")[:-1]
    return "/".join(parts[: config["depth"]]) or "(root)"


def scan(config):
    """全ファイルを読み、{path: 情報} を返す。"""
    modules = {name: load_platform(name) for name in config["platforms"]}
    by_ext = {ext: (name, mod) for name, mod in modules.items() for ext in mod.EXTENSIONS}
    on_disk = collect(config)
    files = sorted(p for p in on_disk
                   if posixpath.splitext(p)[1] in by_ext and not any(fnmatch.fnmatch(p, g) for g in config["exclude"]))
    if not files:
        raise ValueError(f"{config['repo'] / config['root']} の下に、対象の言語（{', '.join(config['platforms'])}）のファイルが無い")
    contexts = {}
    for name, mod in modules.items():
        contexts[name] = {**mod.load(config["repo"], config["rules"].get(name, {})), "files": set(files), "on_disk": on_disk, "root": config["root"]}
    info = {}
    for path in files:
        name, mod = by_ext[posixpath.splitext(path)[1]]
        data = (config["repo"] / path).read_bytes()
        result = mod.analyze(config["repo"], path, data.decode("utf-8", errors="replace"), contexts[name])
        info[path] = {**result, "language": name, "lines": data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1),
                      "hash": hashlib.sha256(data).hexdigest(), "module": module_of(config, path)}
    return info


def build_modules(config, info):
    imported_by = {}
    for path, item in info.items():
        for target in item["imports"]:
            imported_by.setdefault(target, set()).add(path)
    modules = {}
    for path, item in info.items():
        m = modules.setdefault(item["module"], {"files": [], "edges": Counter()})
        m["files"].append(path)
    for name, m in modules.items():
        digest = "\n".join(f"{p}\t{info[p]['hash']}" for p in sorted(m["files"]))
        ranked = sorted(m["files"], key=lambda p: (-len(imported_by.get(p, ())), p))
        m.update(
            hash=hashlib.sha256(digest.encode("utf-8")).hexdigest(), files=sorted(m["files"]),
            representatives=[{"path": p, "imported_by": len(imported_by.get(p, ()))} for p in ranked[: config["representatives"]]],
            symbols=[{"file": p, **s} for p in sorted(m["files"]) for s in info[p]["symbols"]],
            depends_on={}, depended_by={},
        )
    edges = Counter()
    for path, item in info.items():
        for target in item["imports"]:
            a, b = item["module"], info[target]["module"]
            if a != b:
                edges[(a, b)] += 1
    for (a, b), n in sorted(edges.items()):
        modules[a]["depends_on"][b] = n
        modules[b]["depended_by"][a] = n
    for m in modules.values():
        del m["edges"]
    return {k: modules[k] for k in sorted(modules)}, imported_by


def extract(config, fresh=False):
    info = scan(config)
    modules, imported_by = build_modules(config, info)
    out = config["out"]
    tree = ["# ファイルツリー", "", "| ファイル | モジュール | 言語 | 行数 |", "| --- | --- | --- | --- |"]
    tree += [f"| {p} | {info[p]['module']} | {info[p]['language']} | {info[p]['lines']} |" for p in sorted(info)]
    symbols = ["file\tline\tkind\tname"] + [f"{p}\t{s['line']}\t{s['kind']}\t{s['name']}" for p in sorted(info) for s in info[p]["symbols"]]
    (out / "lookup").mkdir(parents=True, exist_ok=True)
    (out / "lookup" / "tree.md").write_text("\n".join(tree) + "\n", encoding="utf-8")
    (out / "lookup" / "symbol_index.tsv").write_text("\n".join(symbols) + "\n", encoding="utf-8")
    jsonl.write(out / "lookup" / "reverse_imports.jsonl", [{"file": f, "imported_by": sorted(v)} for f, v in sorted(imported_by.items())])
    (out / "_raw").mkdir(exist_ok=True)
    (out / "_raw" / "modules.json").write_text(json.dumps(modules, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    roles_path = out / "_raw" / "roles.jsonl"
    if fresh:
        roles_path.unlink(missing_ok=True)
    stored = {r["module"]: r["hash"] for r in jsonl.read(roles_path)}
    plan = carry.split({m: h for m, h in stored.items() if m in modules}, {m: v["hash"] for m, v in modules.items()})
    jsonl.write(roles_path, [r for r in jsonl.read(roles_path) if r["module"] in modules])  # 消えたモジュールの役割を捨てる
    jsonl.write(out / "_raw" / "pending.jsonl", [{"module": m, "files": modules[m]["files"], "representatives": modules[m]["representatives"]} for m in plan["changed"]])
    (out / "_raw" / "plan.json").write_text(json.dumps({"pending": plan["changed"]}, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"modules": sorted(modules), "pending": plan["changed"], "files": len(info), "symbols": sum(len(i["symbols"]) for i in info.values()),
            "unresolved": sum(i["unresolved"] for i in info.values())}


def survey(repo_path, root, platforms):
    """init 用：source.root の下の、ディレクトリごとの対象ファイル数。"""
    extensions = {e for name in platforms for e in load_platform(name).EXTENSIONS}
    base = Path(repo_path) / root
    if not base.is_dir():
        raise ValueError(f"{base} がディレクトリではない")
    counts = Counter()
    for folder, dirs, names in os.walk(base):
        dirs[:] = [d for d in dirs if d not in ALWAYS_EXCLUDED]
        n = sum(1 for name in names if posixpath.splitext(name)[1] in extensions)
        rel = Path(folder).relative_to(base).as_posix()
        parts = [] if rel == "." else rel.split("/")
        for depth in range(len(parts) + 1):
            if n:
                counts["/".join(parts[:depth]) or "."] += n
    return {"directories": dict(sorted(counts.items()))}


# --- 役割 ---------------------------------------------------------------------

def read_draft(path):
    path = Path(path)
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        where = f"{path.name} の {number} 行目"
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{where}: JSON として読めない: {error}") from None
        if not isinstance(row, dict) or set(row) != {"module", "role"}:
            raise ValueError(f"{where}: キーは module と role だけ")
        if not (isinstance(row["role"], str) and row["role"].strip()):
            raise ValueError(f"{where}: role が空")
        if len(row["role"]) > MAX_ROLE:
            raise ValueError(f"{where}: role が {MAX_ROLE} 字を超えている（2〜4 文にする）")
        rows.append((where, row))
    return rows


def apply_roles(config, draft):
    modules = json.loads((config["out"] / "_raw" / "modules.json").read_text(encoding="utf-8"))
    for where, row in draft:
        if row["module"] not in modules:
            raise ValueError(f"{where}: 知らないモジュール {row['module']!r}")
    path = config["out"] / "_raw" / "roles.jsonl"
    stored = {r["module"]: r for r in jsonl.read(path)}
    for _, row in draft:
        stored[row["module"]] = {"module": row["module"], "hash": modules[row["module"]]["hash"], "role": row["role"].strip()}
    jsonl.write(path, [stored[m] for m in sorted(stored)])
    return len(draft)


# --- 組み立て -------------------------------------------------------------------

def module_file(name):
    return name.replace("/", "__") + ".md"


def link(name):
    return "modules/" + module_file(name).replace("(", "%28").replace(")", "%29")


def first_sentence(role):
    text = " ".join(role.split())
    return (text[: text.index("。") + 1] if "。" in text else text).replace("|", "\\|")


def listing(items):
    return "\n".join(items) if items else "（なし）"


def assemble(config):
    out = config["out"]
    modules = json.loads((out / "_raw" / "modules.json").read_text(encoding="utf-8"))
    roles = {r["module"]: r for r in jsonl.read(out / "_raw" / "roles.jsonl")}
    missing = [m for m in modules if m not in roles or roles[m]["hash"] != modules[m]["hash"]]
    if missing:
        raise ValueError("役割が無い、または古いモジュール: " + ", ".join(missing) + "（extract の pending を書いて apply する）")
    (out / "modules").mkdir(exist_ok=True)
    keep = {module_file(m) for m in modules}
    for old in (out / "modules").glob("*.md"):
        if old.name not in keep:
            old.unlink()
    for name, m in modules.items():
        symbols = [f"| {s['file']} | {s['line']} | {s['kind']} | {s['name']} |" for s in m["symbols"]]
        table = "| ファイル | 行 | 種類 | 名前 |\n| --- | --- | --- | --- |\n" + "\n".join(symbols) if symbols else "（なし）"
        text = "\n".join([
            f"# {name}", "", "## 役割", "", roles[name]["role"], "",
            "## 主なファイル", "", listing([f"- `{r['path']}`（被参照 {r['imported_by']}）" for r in m["representatives"]]), "",
            "## 公開シンボル", "", table, "",
            "## 依存先", "", listing([f"- `{k}`（{v} import）" for k, v in m["depends_on"].items()]), "",
            "## 依存元", "", listing([f"- `{k}`（{v} import）" for k, v in m["depended_by"].items()]), "",
        ])
        (out / "modules" / module_file(name)).write_text(text, encoding="utf-8")
    rows = [f"| {n} | {len(m['files'])} | {len(m['symbols'])} | {first_sentence(roles[n]['role'])} | [modules/{module_file(n)}]({link(n)}) |" for n, m in modules.items()]
    (out / "index.md").write_text("# モジュール一覧\n\n| モジュール | ファイル数 | 公開シンボル数 | 概要 | 詳細 |\n| --- | --- | --- | --- | --- |\n" + "\n".join(rows) + "\n", encoding="utf-8")
    edges = [f"| {a} | {b} | {n} |" for a, m in modules.items() for b, n in m["depends_on"].items()]
    (out / "architecture.md").write_text("# アーキテクチャ\n\n## モジュール間の依存\n\n| 依存元 | 依存先 | import 数 |\n| --- | --- | --- |\n" + ("\n".join(edges) if edges else "| （なし） | | |") + "\n", encoding="utf-8")
    shutil.copy(SKILL_DIR / "assets" / "output-skill.template.md", out / "SKILL.md")
    return len(modules)


# --- 検査 ---------------------------------------------------------------------

PUBLIC = ["manifest.json", "index.md", "SKILL.md", "architecture.md", "lookup/tree.md", "lookup/symbol_index.tsv", "lookup/reverse_imports.jsonl"]


def _finding(code, file, line=1, **extra):
    return {"code": code, "file": str(file), "line": line, **extra}


def check(config, skip_manifest=False):
    out = config["out"]
    findings = []
    tree_path = out / "lookup" / "tree.md"
    tree = [l for l in tree_path.read_text(encoding="utf-8").splitlines()[4:] if l.startswith("|")] if tree_path.is_file() else []
    rows = [[c.strip() for c in l.strip("|").split("|")] for l in tree]
    paths = {r[0] for r in rows}
    modules = sorted({r[1] for r in rows})
    for name in PUBLIC:
        if name == "manifest.json" and skip_manifest:
            continue
        if not (out / name).is_file() and name != "manifest.json":
            findings.append(_finding("PUBLIC_MISSING", out / name))
    for name in modules:
        path = out / "modules" / module_file(name)
        if not path.is_file():
            findings.append(_finding("PUBLIC_MISSING", path, module=name))
            continue
        text = path.read_text(encoding="utf-8")
        headings = re.findall(r"(?m)^## (.+)$", text)
        role = re.search(r"## 役割\n\n(.*?)\n\n## ", text, re.S)
        if headings != SECTIONS or not (role and role.group(1).strip()):
            findings.append(_finding("SECTION", path, module=name))
            continue
        for token in re.findall(r"`([^`\s]+)`", role.group(1)):
            if "/" in token and token not in paths and token not in modules:
                findings.append(_finding("ANCHOR", path, module=name, path=token))
    if not skip_manifest:
        mpath = out / "manifest.json"
        if not mpath.is_file():
            findings.append(_finding("MANIFEST", mpath, message="manifest.json が無い"))
        else:
            findings += [_finding("MANIFEST", mpath, message=m) for m in manifest.validate(json.loads(mpath.read_text(encoding="utf-8")))]
    symbols = (out / "lookup" / "symbol_index.tsv")
    stats = {"files": len(paths), "modules": len(modules),
             "symbols": max(0, len(symbols.read_text(encoding="utf-8").splitlines()) - 1) if symbols.is_file() else 0}
    return findings, stats


def finish(config):
    findings, stats = check(config, skip_manifest=True)
    if findings:
        return findings, stats
    plan = json.loads((config["out"] / "_raw" / "plan.json").read_text(encoding="utf-8")) if (config["out"] / "_raw" / "plan.json").is_file() else {"pending": None}
    items = stats["modules"]
    claude = items if plan["pending"] is None else len(plan["pending"])
    manifest.write(
        config["out"], tool="code-map",
        source={"repo": config["repo_name"], "commit": gitinfo.head(config["repo"], config["root"])},
        config_hash_value=manifest.config_hash(config["path"]), inputs={},
        generated_by={"claude": claude, "carried": items - claude}, items=items,
    )
    return [], stats
