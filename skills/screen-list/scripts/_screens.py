"""screen-list の処理（標準ライブラリのみ）。仕様：docs/design/tools/screen-list.md

エラーはすべて ValueError（メッセージは、何をすればよいかを含む）。CLI が終了コード 2 にする。
"""
import csv
import hashlib
import importlib.util
import json
import posixpath
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR.parent.parent / "core"))  # contracts.md の C7
import carry  # noqa: E402
import config as cfg  # noqa: E402
import gitinfo  # noqa: E402
import jsonl  # noqa: E402
import manifest  # noqa: E402

COLUMNS = ["画面ID", "画面名", "種別", "ロール", "URL", "ソース", "モジュール", "親画面ID"]
KINDS = ("画面", "ダイアログ")
EVERYONE = "全員"
MAX_NAME = 80
FORMULA_START = "=+-@\t\r"  # CSV を表計算ソフトで開いたとき、式として評価される先頭の文字


def available_platforms():
    return sorted(p.name for p in (SKILL_DIR / "platforms").iterdir() if p.is_dir())


def load_platform(name):
    path = SKILL_DIR / "platforms" / name / "candidates.py"
    if not path.is_file():
        raise ValueError(f"UI フレームワーク {name!r} のプラットフォーム定義が無い。選べるもの: {', '.join(available_platforms())}")
    spec = importlib.util.spec_from_file_location(f"candidates_{name.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_config(path):
    raw = cfg.load(path, required=("platform", "source", "output", "rules", "checks"))
    if not isinstance(raw["platform"], str):
        raise ValueError("platform は文字列（プラットフォーム定義の名前）")
    source, rules = raw["source"], raw["rules"]
    for key in ("repo", "root", "code_map"):
        if not isinstance(source.get(key), str):
            raise ValueError(f"source.{key} が無い")
    if not isinstance(raw["output"].get("dir"), str):
        raise ValueError("output.dir が無い")
    if not (isinstance(rules.get("roles"), list) and all(isinstance(r, str) for r in rules["roles"])):
        raise ValueError("rules.roles が必須（ロールの名前の配列。無ければ []）。init を実行する")
    if any(";" in r for r in rules["roles"]):
        raise ValueError("rules.roles のロール名に ; は使えない（CSV のロール列の区切りのため）")
    extra = rules.get("extra", [])
    for item in extra:
        if not (isinstance(item, dict) and all(isinstance(item.get(k), str) for k in ("key", "source", "parent"))):
            raise ValueError("rules.extra の各要素は key・source・parent（文字列）を持つ")
    project = cfg.project_root(path)
    return {
        "path": Path(path), "project": project, "repo": cfg.resolve_repo(project, source["repo"]), "repo_name": source["repo"],
        "root": posixpath.normpath(source["root"]), "code_map": project / source["code_map"], "out": project / raw["output"]["dir"],
        "platform": raw["platform"], "rules": rules, "roles": list(rules["roles"]), "exclude": list(rules.get("exclude", [])), "extra": extra,
    }


def read_code_map(config):
    """code-map の公開ファイル（F1・F2・F5）を読む。古ければ止まる。"""
    folder = config["code_map"]
    missing = [n for n in ("lookup/tree.md", "lookup/reverse_imports.jsonl", "manifest.json") if not (folder / n).is_file()]
    if missing:
        raise ValueError(f"code-map の出力が無い（{folder} に {', '.join(missing)}）。code-map build を実行する")
    tree = {}
    for line in (folder / "lookup" / "tree.md").read_text(encoding="utf-8").splitlines()[4:]:
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            tree[cells[0]] = cells[1]
    reverse = {r["file"]: r["imported_by"] for r in jsonl.read(folder / "lookup" / "reverse_imports.jsonl")}
    mapped = manifest.read(folder)
    now = gitinfo.head(config["repo"], config["root"])  # 未コミットの変更（+dirty）も、code-map の版と合わせて比べる。root は code-map と同じにする
    if mapped["source"].get("commit") != now:
        raise ValueError(f"code-map が古い（code-map は {mapped['source'].get('commit')}、ソースは {now}）。code-map update を実行する")
    return {"tree": tree, "reverse": reverse, "manifest": mapped}


def vocabulary(config):
    return set(config["roles"]) | {EVERYONE}


def candidates(config, fresh=False):
    code_map = read_code_map(config)
    platform = load_platform(config["platform"])
    found = platform.candidates(config["repo"], config["rules"], code_map["reverse"])
    for item in config["extra"]:
        found.append({"key": item["key"], "kind": "画面", "file": item["source"], "line": 1, "url": "", "parents": [item["parent"]]})
    rows, seen = [], {}
    for c in found:
        cid = platform.id_of(c)
        if cid in seen:
            raise ValueError(f"画面 ID {cid} が重複している（{seen[cid]} と {c['file']}）")
        seen[cid] = c["file"]
        path = config["repo"] / c["file"]
        if not path.is_file():
            raise ValueError(f"{cid} のソース {c['file']} が {config['repo']} の下に無い")
        digest = hashlib.sha256(path.read_bytes() + b"\n" + ";".join(sorted(c["parents"])).encode("utf-8")).hexdigest()
        rows.append({"id": cid, "kind": c["kind"], "url": c["url"], "file": c["file"], "line": c["line"], "source": f"{c['file']}:{c['line']}",
                     "module": code_map["tree"].get(c["file"], ""), "parents": sorted(c["parents"]), "fingerprint": digest})
    unknown = [i for i in config["exclude"] if i not in seen]
    if unknown:
        raise ValueError("rules.exclude に、候補に無い画面 ID がある: " + ", ".join(unknown))
    rows = sorted((r for r in rows if r["id"] not in config["exclude"]), key=lambda r: r["id"])
    raw = config["out"] / "_raw"
    jsonl.write(raw / "candidates.jsonl", rows)
    names_path = raw / "names.jsonl"
    if fresh:
        names_path.unlink(missing_ok=True)
    stored = {r["id"]: r["fingerprint"] for r in jsonl.read(names_path)}
    plan = carry.split(stored, {r["id"]: r["fingerprint"] for r in rows})
    jsonl.write(names_path, [r for r in jsonl.read(names_path) if r["id"] in {x["id"] for x in rows}])  # 消えた画面の名前を捨てる
    by_id = {r["id"]: r for r in rows}
    jsonl.write(raw / "pending.jsonl", [{k: by_id[i][k] for k in ("id", "kind", "url", "source", "parents")} for i in plan["changed"]])
    (raw / "plan.json").write_text(json.dumps({"pending": plan["changed"]}, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"candidates": len(rows), "dialogs": sum(1 for r in rows if r["kind"] == "ダイアログ"), "pending": plan["changed"]}


def read_draft(path, config):
    path = Path(path)
    vocab = vocabulary(config)
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        where = f"{path.name} の {number} 行目"
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{where}: JSON として読めない: {error}") from None
        if not isinstance(row, dict) or set(row) != {"id", "name", "roles"}:
            raise ValueError(f"{where}: キーは id・name・roles だけ")
        if not (isinstance(row["name"], str) and row["name"].strip()):
            raise ValueError(f"{where}: name が空")
        if row["name"][0] in FORMULA_START:
            raise ValueError(f"{where}: name が {row['name'][0]!r} で始まっている（表計算ソフトで式として実行されるため、別の名前にする）")
        if len(row["name"]) > MAX_NAME:
            raise ValueError(f"{where}: name が {MAX_NAME} 字を超えている")
        roles = row["roles"]
        unresolved = isinstance(roles, list) and len(roles) == 1 and isinstance(roles[0], str) and roles[0].startswith("[未解決:") and roles[0].endswith("]")
        if not (isinstance(roles, list) and roles and all(isinstance(r, str) for r in roles) and (unresolved or set(roles) <= vocab)):
            raise ValueError(f"{where}: roles は {sorted(vocab)} の配列か、[未解決: 理由] の 1 要素: {roles!r}")
        rows.append((where, row))
    return rows


def apply_names(config, draft):
    candidates_ = {r["id"]: r for r in jsonl.read(config["out"] / "_raw" / "candidates.jsonl")}
    for where, row in draft:
        if row["id"] not in candidates_:
            raise ValueError(f"{where}: 候補に無い画面 ID {row['id']!r}")
    path = config["out"] / "_raw" / "names.jsonl"
    stored = {r["id"]: r for r in jsonl.read(path)}
    for _, row in draft:
        stored[row["id"]] = {"id": row["id"], "fingerprint": candidates_[row["id"]]["fingerprint"], "name": row["name"].strip(), "roles": row["roles"]}
    jsonl.write(path, [stored[i] for i in sorted(stored)])
    return len(draft)


def merge(config):
    rows = jsonl.read(config["out"] / "_raw" / "candidates.jsonl")
    names = {r["id"]: r for r in jsonl.read(config["out"] / "_raw" / "names.jsonl")}
    missing = [r["id"] for r in rows if r["id"] not in names or names[r["id"]]["fingerprint"] != r["fingerprint"]]
    if missing:
        raise ValueError("名前が無い、または古い画面: " + ", ".join(missing) + "（candidates の pending を書いて apply する）")
    path = config["out"] / "screens.csv"
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(COLUMNS)
        for r in rows:
            n = names[r["id"]]
            writer.writerow([r["id"], n["name"], r["kind"], ";".join(n["roles"]), r["url"], r["source"], r["module"], ";".join(r["parents"])])
    return len(rows)


def _finding(code, file, line=1, **extra):
    return {"code": code, "file": str(file), "line": line, **extra}


def check(config, skip_manifest=False):
    out = config["out"]
    path = out / "screens.csv"
    if not path.is_file():
        raise ValueError(f"{path} が無い。merge を実行する")
    with open(path, encoding="utf-8-sig", newline="") as handle:
        table = list(csv.DictReader(handle))
    expected = {r["id"] for r in jsonl.read(out / "_raw" / "candidates.jsonl")}
    vocab, findings, seen = vocabulary(config), [], set()
    ids = [r.get("画面ID", "") for r in table]
    for number, r in enumerate(table, start=2):
        if r.get("画面ID") in seen:
            findings.append(_finding("DUPLICATE_ID", path, number, id=r.get("画面ID")))
        seen.add(r.get("画面ID"))
        roles = [x for x in r.get("ロール", "").split(";") if x]
        bad_roles = [x for x in roles if x not in vocab and not (len(roles) == 1 and x.startswith("[未解決:"))]
        if r.get("種別") not in KINDS or not r.get("画面名", "").strip() or not roles or bad_roles:
            findings.append(_finding("VALUE", path, number, id=r.get("画面ID")))
    for cid in sorted(expected ^ set(ids)):
        findings.append(_finding("COVERAGE", path, 1, id=cid, problem="候補に無い" if cid in set(ids) else "CSV に無い"))
    if not skip_manifest:
        mpath = out / "manifest.json"
        if not mpath.is_file():
            findings.append(_finding("MANIFEST", mpath, message="manifest.json が無い"))
        else:
            findings += [_finding("MANIFEST", mpath, message=m) for m in manifest.validate(json.loads(mpath.read_text(encoding="utf-8")))]
    stats = {"candidates": len(expected), "rows": len(table), "dialogs": sum(1 for r in table if r.get("種別") == "ダイアログ"),
             "unresolved": sum(1 for r in table if "[未解決" in r.get("画面名", "") + r.get("ロール", ""))}
    return findings, stats


def finish(config):
    findings, stats = check(config, skip_manifest=True)
    if findings:
        return findings, stats
    plan_path = config["out"] / "_raw" / "plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.is_file() else {"pending": None}
    items = stats["rows"]
    claude = items if plan["pending"] is None else len(plan["pending"])
    manifest.write(
        config["out"], tool="screen-list",
        source={"repo": config["repo_name"], "commit": gitinfo.head(config["repo"], config["root"])},
        config_hash_value=manifest.config_hash(config["path"]),
        inputs={"code-map": read_code_map(config)["manifest"]["source"]},
        generated_by={"claude": claude, "carried": items - claude}, items=items,
    )
    return [], stats
