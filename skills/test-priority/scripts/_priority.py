"""test-priority の共通処理（標準ライブラリのみ）。仕様：docs/design/tools/test-priority.md

判定の計算（決定・規模・代表）は、AI の判断と設定だけから決まる純粋な関数にしてある。
列名や書式など、テストケースの形式に依存する部分は platforms/<名前>/ に置く（contracts.md の C9）。
"""
import sys

if sys.version_info < (3, 11):  # 設定ファイルの TOML を読む tomllib は 3.11 から標準
    raise SystemExit(f"Python 3.11 以上が必要（今は {sys.version.split()[0]}）")

import csv
import glob
import hashlib
import importlib.util
import json
import tomllib
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR.parent.parent / "core"))  # contracts.md の C7
import carry  # noqa: E402
import manifest  # noqa: E402
LEVELS = (1, 2, 3, 4)
SCALES = ("sanity", "smoke", "light", "full")
EXCLUDED = "対象外"
UNDECIDABLE = "判定不可"
AXES = ("data", "permission", "blast")
IMPACTS = ("cosmetic", "stop", "harm")
KINDS = ("代表", "応用")
EXISTING = ("high", "medium", "low")
NO_GROUP = "(なし)"
CHECK_NAMES = ("import-clean", "examples")
MARK_ORDER = ("上げ", "下げ", "推定", UNDECIDABLE)
# 重要度 → (グループの代表, それ以外) の規模。仕様書 6.2（仮の値）
# 毎回流す段（sanity・smoke）に入るのは、グループの代表だけ。重要でも代表ではないケースは light 以下（仕様書 6.2。32 件の試算で、毎回流す割合が 52% → 29%）
SCALE_TABLE = {1: ("sanity", "light"), 2: ("smoke", "light"), 3: ("light", "full"), 4: ("full", "full")}


class ConfigError(Exception):
    """設定ファイルの問題。`init` を実行するよう伝える。"""


class InputError(Exception):
    """入力ファイルの問題（重複、欠け、古い判断など）。"""


def level_name(level):
    return f"R{level}" if level else ""


def parse_level(text):
    if not (isinstance(text, str) and len(text) == 2 and text[0] == "R" and text[1] in "1234"):
        raise InputError(f"重要度は R1〜R4: {text!r}")
    return int(text[1])


# --- 設定 -------------------------------------------------------------------

def _int_level(value, where):
    if not (isinstance(value, int) and not isinstance(value, bool) and value in LEVELS):
        raise ConfigError(f"{where} は 1〜4 の整数: {value!r}")
    return value


def load_config(path):
    path = Path(path)
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"{path} が無い。init を実行する") from None
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path} を TOML として読めない: {error}") from None
    for key in ("platform", "source", "output", "rules", "checks"):
        if key not in raw:
            raise ConfigError(f"{path} に {key} が無い")
    if not isinstance(raw["platform"], str):
        raise ConfigError("platform は文字列（プラットフォーム定義の名前）")
    source, output, rules = raw["source"], raw["output"], raw["rules"]
    if source.get("repo") != ".":
        raise ConfigError(f"source.repo は \".\" （利用側プロジェクト自身）: {source.get('repo')!r}")
    for table, key in ((source, "source.cases_glob"), (output, "output.dir")):
        if not isinstance(table.get(key.split(".")[1]), str):
            raise ConfigError(f"{key} が無い")
    group_by = rules.get("group_by")
    if group_by not in ("feature", "screen"):
        raise ConfigError(f"rules.group_by は feature か screen: {group_by!r}")
    areas = {}
    for code, area in rules.get("areas", {}).items():
        emphasis = area.get("emphasis", [])
        if not set(emphasis) <= set(AXES):
            raise ConfigError(f"rules.areas.{code}.emphasis に知らないリスク軸: {emphasis}")
        weights = {name: _int_level(v, f"rules.areas.{code}.weights.{name}") for name, v in area.get("weights", {}).items()}
        areas[code] = {"emphasis": set(emphasis), "default": _int_level(area.get("default"), f"rules.areas.{code}.default"), "weights": weights}
    if not areas:
        raise ConfigError("rules.areas が空")
    run = raw["checks"].get("run", [])
    unknown = sorted(set(run) - set(CHECK_NAMES))
    if unknown:
        raise ConfigError(f"checks.run に知らない検査: {unknown}（選べるもの: {', '.join(CHECK_NAMES)}）")
    root = path.resolve().parent.parent
    return {
        "path": path,
        "root": root,
        "platform": raw["platform"],
        "cases_glob": source["cases_glob"],
        "out_dir": root / output["dir"],
        "rules": {"group_by": group_by, "areas": areas, "exclude": {"features": list(rules.get("exclude", {}).get("features", []))}},
        "checks": raw["checks"],
    }


def available_platforms():
    return sorted(p.name for p in (SKILL_DIR / "platforms").iterdir() if p.is_dir())


def load_platform(name):
    path = SKILL_DIR / "platforms" / name / "load.py"
    if not path.is_file():
        raise ConfigError(f"プラットフォーム定義 {name!r} が無い。選べるもの: {', '.join(available_platforms())}")
    spec = importlib.util.spec_from_file_location(f"platform_{name.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def case_files(config):
    return sorted(Path(p) for p in glob.glob(str(config["root"] / config["cases_glob"])))


def load_cases(config):
    platform = load_platform(config["platform"])
    files = case_files(config)
    if not files:
        raise InputError(f"{config['cases_glob']} に当たるファイルが無い")
    seen, cases = {}, []
    for file in files:
        try:
            records = platform.load_cases(file)
        except ValueError as error:
            raise InputError(f"{file}: {error}") from None
        for record in records:
            if record["case"] in seen:
                raise InputError(f"DUPLICATE {record['case']}: {seen[record['case']]} と {file}")
            seen[record["case"]] = file
            cases.append(record)
    return sorted(cases, key=lambda r: r["case"])


def source_hash(config):
    digest = hashlib.sha256()
    for file in case_files(config):
        digest.update(file.read_bytes())
    return "sha256:" + digest.hexdigest()


# --- jsonl / 裁定 -------------------------------------------------------------

def raw_dir(config):
    return config["out_dir"] / "_raw"


def read_jsonl(path):
    path = Path(path)
    if not path.is_file():
        return []
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise InputError(f"{path.name} の {number} 行目を JSON として読めない: {error}。{path} を作り直す（build）") from None
    return rows


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    path.write_text(text, encoding="utf-8")


def read_adjudications(config):
    """人の裁定を読んで検証する（仕様書 7）。誤りは InputError（どのケースのどのキーか）。"""
    path = config["out_dir"] / "adjudications.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise InputError(f"{path.name} を JSON として読めない: {error}") from None
    if not isinstance(data, dict):
        raise InputError(f"{path.name} は {{ケース: 裁定 }} の形")
    for case, adj in data.items():
        where = f"{path.name} の {case}"
        if not isinstance(adj, dict) or not set(adj) <= {"重要度", "規模", "理由"}:
            raise InputError(f"{where}: キーは 重要度・規模・理由 だけ")
        if not (isinstance(adj.get("理由"), str) and adj["理由"].strip()):
            raise InputError(f"{where}: 理由が必須")
        if "重要度" not in adj and "規模" not in adj:
            raise InputError(f"{where}: 重要度か規模のどちらかが必要")
        if "重要度" in adj and adj["重要度"] not in tuple(level_name(l) for l in LEVELS):
            raise InputError(f"{where}: 重要度は R1〜R4: {adj['重要度']!r}")
        if "規模" in adj and adj["規模"] not in (*SCALES, EXCLUDED):
            raise InputError(f"{where}: 規模は {[*SCALES, EXCLUDED]} のどれか: {adj['規模']!r}")
    return data


# --- 決定 ---------------------------------------------------------------------

def decide_level(rules, rec, judgment, adjudication=None):
    """開始点・リスク軸・影響範囲・既存の優先度から、重要度と要レビューの印を決める（仕様書 4・5.2）。"""
    area = rules["areas"].get(rec["area"])
    start, level, marks, effective, blocked_by = None, None, set(), [], None
    if area is not None:
        if rec["feature"] in area["weights"]:
            start = area["weights"][rec["feature"]]
        else:
            start = area["default"]
            marks.add("推定")
        effective = [a for a in AXES if a in judgment["axes"] and a in area["emphasis"]]
        if judgment["impact"] in ("stop", "harm"):
            step = 1 if effective else 0
        else:
            step = 0 if effective else -1
        if step > 0 and rec["existing"] == "low":
            step, blocked_by = 0, "existing_low"
        elif step < 0 and rec["existing"] == "high":
            step, blocked_by = 0, "existing_high"
        level = min(4, max(1, start - step))
    if adjudication and "重要度" in adjudication:
        level = parse_level(adjudication["重要度"])
    if level is None:
        marks.add(UNDECIDABLE)
    else:
        if start is not None and start != 1 and level == 1:
            marks.add("上げ")
        if start is not None and start != 4 and level == 4:
            marks.add("下げ")
    return {"start": start, "level": level, "marks": [m for m in MARK_ORDER if m in marks],
            "effective_axes": effective, "blocked_by": blocked_by}


def scale_of(rules, rec, level, is_representative, adjudication=None):
    if adjudication and "規模" in adjudication:
        return adjudication["規模"]
    if rec["feature"] in rules["exclude"]["features"]:
        return EXCLUDED
    if level is None:
        return UNDECIDABLE
    return SCALE_TABLE[level][0 if is_representative else 1]


def group_key(rules, rec):
    return rec[rules["group_by"]] or NO_GROUP


def current_judgments(cases, judgments):
    """ケースの内容（fingerprint）が一致する判断だけを返す。欠けと古いものは InputError。"""
    by_case = {j["case"]: j for j in judgments}
    problems = [c["case"] for c in cases if c["case"] not in by_case or by_case[c["case"]]["fingerprint"] != c["fingerprint"]]
    if problems:
        raise InputError("判断が無い、または古いケース: " + ", ".join(problems))
    return by_case


def decide_all(config, cases, judgments, adjudications):
    rules = config["rules"]
    by_case = current_judgments(cases, judgments)
    rows = []
    for rec in cases:
        j = by_case[rec["case"]]
        adj = adjudications.get(rec["case"])
        d = decide_level(rules, rec, j, adj)
        rows.append({"rec": rec, "judgment": j, "adjudication": adj, "representative": False, **d})
    groups = {}
    for row in rows:
        if row["level"] is not None and row["rec"]["feature"] not in rules["exclude"]["features"]:
            groups.setdefault(group_key(rules, row["rec"]), []).append(row)
    for members in groups.values():
        # 代表と判断されたケースから選ぶ。1 件も無いグループは、グループの全ケースから最も重要な 1 件を代表にする
        pool = [r for r in members if r["judgment"]["kind"] == "代表"] or members
        min(pool, key=lambda r: (r["level"], r["rec"]["case"]))["representative"] = True
    for row in rows:
        row["case"] = row["rec"]["case"]
        row["scale"] = scale_of(rules, row["rec"], row["level"], row["representative"], row["adjudication"])
    return sorted(rows, key=lambda r: r["case"])


# --- 書き出し -----------------------------------------------------------------

REVIEW_TAIL = ["タイトル", "領域", "機能", "確認画面", "既存の優先度", "開始点", "リスク軸", "影響範囲", "種別", "代表",
               "重要度", "規模", "理由", "要レビュー"]
IMPORT_TAIL = ["重要度", "規模"]


def import_header(config):
    return [load_platform(config["platform"]).CASE_COLUMN, *IMPORT_TAIL]


def review_header(config):
    return [load_platform(config["platform"]).CASE_COLUMN, *REVIEW_TAIL]


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def decide_from_files(config):
    cases = load_cases(config)
    judgments = read_jsonl(raw_dir(config) / "judgments.jsonl")
    return decide_all(config, cases, judgments, read_adjudications(config))


def export(config):
    rows = decide_from_files(config)
    missing = [r["case"] for r in rows
               if not r["judgment"].get("reason") or r["judgment"].get("reason_level") != (r["level"] or 0)]
    if missing:
        raise InputError("理由が無い、または別の重要度で書かれたケース: " + ", ".join(missing))
    review, import_rows = [review_header(config)], [import_header(config)]
    for r in rows:
        rec, j = r["rec"], r["judgment"]
        review.append([
            r["case"], rec["title"], rec["area"], rec["feature"], rec["screen"], rec["existing"].capitalize(),
            level_name(r["start"]), ";".join(sorted(set(j["axes"]), key=AXES.index)), j["impact"], j["kind"],
            "○" if r["representative"] else "", level_name(r["level"]), r["scale"], j["reason"], ";".join(r["marks"]),
        ])
        if r["scale"] in SCALES:
            import_rows.append([r["case"], level_name(r["level"]), r["scale"]])
    write_csv(config["out_dir"] / "review.csv", review)
    write_csv(config["out_dir"] / "import.csv", import_rows)
    return rows


# --- 検査 ---------------------------------------------------------------------

def _finding(code, file, line, **extra):
    return {"code": code, "file": str(file), "line": line, **extra}


def run_examples(config):
    findings = []
    examples = config["checks"].get("examples", {}).get("case", [])
    for index, e in enumerate(examples, start=1):
        rec = {"case": e["name"], "title": "", "area": e["area"], "feature": e["feature"], "screen": "",
               "existing": e.get("existing", ""), "body": "", "fingerprint": ""}
        judgment = {"axes": e["axes"], "impact": e["impact"], "kind": e["kind"]}
        d = decide_level(config["rules"], rec, judgment, None)
        got = {"level": level_name(d["level"]), "scale": scale_of(config["rules"], rec, d["level"], e["representative"], None)}
        if got != e["expect"]:
            findings.append(_finding("EXAMPLE", config["path"], index, name=e["name"], expected=e["expect"], actual=got))
    return findings


def check(config, skip_manifest=False):
    """検査結果（findings, stats）を返す。入力ファイルが読めないときは InputError。"""
    out = config["out_dir"]
    findings, stats = [], {}
    cases = load_cases(config)
    paths = {name: out / name for name in ("import.csv", "review.csv")}
    for name, path in paths.items():
        if not path.is_file():
            raise InputError(f"{path} が無い。先に build か export を実行する")
    run = config["checks"].get("run", [])
    imp, rev = read_csv(paths["import.csv"]), read_csv(paths["review.csv"])
    for name, table in (("import.csv", imp), ("review.csv", rev)):
        if not table:
            raise InputError(f"{paths[name]} が空")
    rev_header = review_header(config)
    if rev[0] != rev_header:
        raise InputError(f"{paths['review.csv']} の列が決まった列と違う")
    review = [(n, dict(zip(rev_header, r))) for n, r in enumerate(rev[1:], start=2)]
    scale_of_case = {}
    for _, r in review:
        scale_of_case.setdefault(r[rev_header[0]], []).append(r["規模"])
    key = rev_header[0]
    decided = {c for c, scales in scale_of_case.items() if len(scales) == 1 and scales[0] in SCALES}
    stats.update(cases=len(cases), unresolved=sum(1 for _, r in review if r["規模"] == UNDECIDABLE))
    for scale in (*SCALES, EXCLUDED):
        stats[scale] = sum(1 for _, r in review if r["規模"] == scale)

    if "import-clean" in run:
        header_ok = imp[0] == import_header(config)
        if not header_ok:
            findings.append(_finding("COLUMNS", paths["import.csv"], 1, expected=import_header(config), actual=imp[0]))
        case_names = [c["case"] for c in cases]
        for case in case_names:
            if len(scale_of_case.get(case, [])) != 1:
                findings.append(_finding("COVERAGE", paths["review.csv"], 1, case=case, problem="review.csv に 1 行ずつ無い"))
        for case in sorted(set(scale_of_case) - set(case_names)):
            findings.append(_finding("COVERAGE", paths["review.csv"], 1, case=case, problem="入力に無いケースがある"))
        if header_ok:
            imported = []
            for n, r in enumerate(imp[1:], start=2):
                if len(r) != 3 or not (r[1] in tuple(level_name(l) for l in LEVELS) and r[2] in SCALES):
                    findings.append(_finding("VALUE", paths["import.csv"], n, row=r))
                if r and r[0] in scale_of_case and set(scale_of_case[r[0]]) & {EXCLUDED, UNDECIDABLE}:
                    findings.append(_finding("EXCLUDED_ROW", paths["import.csv"], n, case=r[0]))
                imported.append(r[0] if r else "")
            if sorted(imported) != sorted(decided):
                for case in sorted(set(imported) ^ decided):
                    findings.append(_finding("COVERAGE", paths["import.csv"], 1, case=case, problem="import.csv と review.csv で規模が決まったケースが違う"))
        known = {c["case"] for c in cases}
        for case in sorted(set(read_adjudications(config)) - known):
            findings.append(_finding("ADJUDICATION_UNKNOWN_CASE", out / "adjudications.json", 1, case=case))
    stats["decided"] = len(imp) - 1
    if "examples" in run:
        findings += run_examples(config)
    if not skip_manifest:
        path = out / "manifest.json"
        if not path.is_file():
            findings.append(_finding("MANIFEST", path, 1, message="manifest.json が無い"))
        else:
            findings += [_finding("MANIFEST", path, 1, message=m) for m in manifest.validate(json.loads(path.read_text(encoding="utf-8")))]
    return findings, stats


# --- AI の判断の取り込み --------------------------------------------------------

DRAFT_KEYS = {"judge": {"case", "axes", "impact", "kind"}, "explain": {"case", "reason"}}


def read_draft(path, mode):
    """AI が書いた下書きを検証して返す。1 行でも誤りがあれば InputError（何も書かない）。"""
    path = Path(path)
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        where = f"{path.name} の {number} 行目"
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise InputError(f"{where}: JSON として読めない: {error}") from None
        if not isinstance(row, dict) or set(row) != DRAFT_KEYS[mode]:
            raise InputError(f"{where}: キーは {sorted(DRAFT_KEYS[mode])} だけ")
        if mode == "judge":
            axes = row["axes"]
            if not (isinstance(axes, list) and set(axes) <= set(AXES)):
                raise InputError(f"{where}: axes は {list(AXES)} の配列")
            if row["impact"] not in IMPACTS:
                raise InputError(f"{where}: impact は {list(IMPACTS)} のどれか: {row['impact']!r}")
            if row["kind"] not in KINDS:
                raise InputError(f"{where}: kind は {list(KINDS)} のどちらか: {row['kind']!r}")
        elif not (isinstance(row["reason"], str) and row["reason"].strip()):
            raise InputError(f"{where}: reason が空")
        rows.append((where, row))
    return rows


def apply_judge(config, draft):
    cases = {c["case"]: c for c in load_cases(config)}
    path = raw_dir(config) / "judgments.jsonl"
    stored = {j["case"]: j for j in read_jsonl(path) if j["case"] in cases}
    for where, row in draft:
        if row["case"] not in cases:
            raise InputError(f"{where}: 入力に無いケース {row['case']}")
    for _, row in draft:
        new = {"case": row["case"], "fingerprint": cases[row["case"]]["fingerprint"],
               "axes": sorted(set(row["axes"]), key=AXES.index), "impact": row["impact"], "kind": row["kind"],
               "reason": "", "reason_level": 0}
        old = stored.get(row["case"])
        if old and all(old[k] == new[k] for k in ("fingerprint", "axes", "impact", "kind")):
            new["reason"], new["reason_level"] = old["reason"], old["reason_level"]
        stored[row["case"]] = new
    write_jsonl(path, [stored[c] for c in sorted(stored)])
    return len(draft)


def apply_explain(config, draft):
    rows = {r["case"]: r for r in decide_from_files(config)}
    path = raw_dir(config) / "judgments.jsonl"
    stored = {j["case"]: j for j in read_jsonl(path)}
    for where, row in draft:
        if row["case"] not in rows:
            raise InputError(f"{where}: 判断が無いケース {row['case']}")
    for _, row in draft:
        stored[row["case"]]["reason"] = row["reason"]
        stored[row["case"]]["reason_level"] = rows[row["case"]]["level"] or 0
    write_jsonl(path, [stored[c] for c in sorted(stored)])
    return len(draft)


def survey(platform_name, root, cases_glob):
    """init 用：領域・機能・確認画面ごとの件数を数える（設定ファイルはまだ無い）。"""
    config = {"platform": platform_name, "root": Path(root), "cases_glob": cases_glob}
    areas = {}
    for rec in load_cases(config):
        area = areas.setdefault(rec["area"], {"cases": 0, "features": {}, "screens": {}})
        area["cases"] += 1
        area["features"][rec["feature"]] = area["features"].get(rec["feature"], 0) + 1
        area["screens"][rec["screen"]] = area["screens"].get(rec["screen"], 0) + 1
    return {"cases": sum(a["cases"] for a in areas.values()), "areas": areas}


# --- update：何を作り直すか ------------------------------------------------------

def plan_path(config):
    return raw_dir(config) / "plan.json"


def read_plan(config):
    path = plan_path(config)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise InputError(f"{path.name} を JSON として読めない: {error}。load_cases.py を実行し直す") from None


def write_plan(config, **parts):
    plan = {**read_plan(config), **parts}
    plan_path(config).parent.mkdir(parents=True, exist_ok=True)
    plan_path(config).write_text(json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def plan_judge(config):
    """前回の判断と今回のケースを比べ、AI が判断し直すケースを _raw/pending.jsonl に書く。消えたケースの判断は捨てる。"""
    cases = load_cases(config)
    path = raw_dir(config) / "judgments.jsonl"
    stored = read_jsonl(path)
    result = carry.split({j["case"]: j["fingerprint"] for j in stored}, {c["case"]: c["fingerprint"] for c in cases})
    kept = [j for j in stored if j["case"] not in set(result["removed"])]
    if len(kept) != len(stored):
        write_jsonl(path, sorted(kept, key=lambda j: j["case"]))
    by_case = {c["case"]: c for c in cases}
    write_jsonl(raw_dir(config) / "pending.jsonl", [by_case[k] for k in result["changed"]])
    write_plan(config, judge=result["changed"], explain=[])
    return {"pending": result["changed"], "carried": len(result["carried"]), "removed": result["removed"]}


def plan_explain(config):
    """決定した重要度と、理由文を書いたときの重要度を比べ、理由文を書き直すケースを _raw/explain_input.jsonl に書く。"""
    rows = decide_from_files(config)
    pending = [r for r in rows if not r["judgment"].get("reason") or r["judgment"].get("reason_level") != (r["level"] or 0)]
    write_jsonl(raw_dir(config) / "explain_input.jsonl", [{
        "case": r["case"], "title": r["rec"]["title"], "body": r["rec"]["body"],
        "axes": r["judgment"]["axes"], "impact": r["judgment"]["impact"], "kind": r["judgment"]["kind"],
        "start": level_name(r["start"]) or None, "level": level_name(r["level"]) or None, "scale": r["scale"],
        "representative": r["representative"], "marks": r["marks"], "effective_axes": r["effective_axes"],
        "blocked_by": r["blocked_by"], "adjudicated": bool(r["adjudication"]),
    } for r in pending])
    names = [r["case"] for r in pending]
    write_plan(config, explain=names)
    return {"pending": names}


def carried_count(config, cases):
    """AI が今回何も作らなかったケースの数。plan.json が無い（build）なら 0。"""
    if not plan_path(config).is_file():
        return 0
    plan = read_plan(config)
    touched = set(plan.get("judge", [])) | set(plan.get("explain", []))
    return sum(1 for c in cases if c["case"] not in touched)


def adjudicate(config, case, level=None, scale=None, reason=None):
    cases = {c["case"] for c in load_cases(config)}
    if case not in cases:
        raise InputError(f"入力に無いケース: {case}")
    if not (reason and reason.strip()):
        raise InputError("--reason が必須")
    if level is None and scale is None:
        raise InputError("--level か --scale のどちらかが必要")
    value = {"理由": reason}
    if level is not None:
        if level not in tuple(level_name(l) for l in LEVELS):
            raise InputError(f"--level は R1〜R4: {level!r}")
        value["重要度"] = level
    if scale is not None:
        if scale not in (*SCALES, EXCLUDED):
            raise InputError(f"--scale は {[*SCALES, EXCLUDED]} のどれか: {scale!r}")
        value["規模"] = scale
    carry.record(config["out_dir"] / "adjudications.json", case, value)
    return value
