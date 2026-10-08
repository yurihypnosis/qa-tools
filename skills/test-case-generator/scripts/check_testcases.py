#!/usr/bin/env python3
"""Step 3 のテストケースファイルを検査する（読み取り専用）。

  NO_CASES            CaseNo. で始まるケース表が 1 つも無い
  COLUMNS <行>        ケース表の列が 15 列の固定ヘッダと一致しない
  ROW_WIDTH <行>      データ行のセル数が 15 ではない
  CASE_ID <行>        CaseNo. が `{PBI ID}-TC-###` の形でない
  SEQUENCE <行>       CaseNo. が 001 からの通し番号になっていない
  VIEWPOINT_ID <行>   観点ID が `TP-###` の形でない
  REMARKS <行>        備考セルが空でない
  TRACE <TP>          --viewpoints 指定時、観点ファイルを数え直した必要ケース数に足りない
  UNKNOWN_TP <TP>     --viewpoints 指定時、観点ファイルに無い TP を参照している

必要ケース数は観点ファイルから数え直す（Step 3 自身のトレース表は信用しない）:
DT は R 列の数、確認パターン表はデータ行の数、表の無い TP は 1。

使い方: check_testcases.py <step3-testcases.md> [--viewpoints <step2-viewpoints.md>] [--json]
終了コード: 0=OK / 1=指摘あり / 2=入力エラー
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _markdown import emit, expand_tp, parse, read_text

COLUMNS = [
    "CaseNo.",
    "観点ID/Viewpoint ID",
    "タイトル/Title",
    "領域/Area",
    "確認画面/Screen",
    "機能/Function",
    "大項目/Category",
    "中項目/Sub category",
    "小項目/Item",
    "実施ユーザー/Execution Role",
    "事前条件/Precondition",
    "実施手順/Execution Step",
    "期待結果/Expected Result",
    "重要度/Priority",
    "備考/Remarks",
]
CASE_ID = re.compile(r"^(?P<pbi>[A-Z][A-Z0-9]*-\d+)-TC-(?P<num>\d{3})$")
VIEWPOINT_ID = re.compile(r"^TP-\d{3}$")
RULE_COLUMN = re.compile(r"^R\d+$")


def check_structure(text):
    findings, cases = [], []
    expected_num = 1
    pbi = None
    case_tables = [t for t in parse(text).tables if t.header and t.header[0] == "CaseNo."]
    if not case_tables:
        findings.append({"code": "NO_CASES"})
    for table in case_tables:
        if table.header != COLUMNS:
            findings.append({"code": "COLUMNS", "line": table.line})
            continue
        for line, cells in table.rows:
            if len(cells) != len(COLUMNS):
                findings.append({"code": "ROW_WIDTH", "line": line})
                continue
            case_id, viewpoint, remarks = cells[0], cells[1], cells[-1]
            match = CASE_ID.match(case_id)
            if not match:
                findings.append({"code": "CASE_ID", "line": line, "value": case_id})
                expected_num += 1  # 不正な行も 1 件と数え、次の行に SEQUENCE を重ねて出さない
            else:
                pbi = pbi or match.group("pbi")
                expected = f"{pbi}-TC-{expected_num:03d}"
                if case_id != expected:
                    findings.append(
                        {"code": "SEQUENCE", "line": line, "expected": expected, "actual": case_id}
                    )
                expected_num = int(match.group("num")) + 1
            if not VIEWPOINT_ID.match(viewpoint):
                findings.append({"code": "VIEWPOINT_ID", "line": line, "value": viewpoint})
            if remarks:
                findings.append({"code": "REMARKS", "line": line})
            cases.append((line, case_id, viewpoint))
    return findings, cases


def required_cases(viewpoints_text):
    """観点ファイルを数え直し、TP ごとの必要ケース数を返す。"""
    doc = parse(viewpoints_text)
    required = dict.fromkeys(doc.tp_ids, 0)
    for table in doc.tables:
        if table.tp is None or len(table.header) < 2 or not table.rows:
            continue
        rules = [c for c in table.header[1:] if RULE_COLUMN.match(c)]
        count = len(rules) if rules else len(table.rows)
        for tp_id in expand_tp(table.tp):
            required[tp_id] += count
    return {tp_id: max(count, 1) for tp_id, count in required.items()}


def check_trace(cases, viewpoints_text):
    required = required_cases(viewpoints_text)
    actual = Counter(viewpoint for _, _, viewpoint in cases)
    findings = []
    for tp_id, expected in required.items():
        if actual[tp_id] < expected:
            findings.append({"code": "TRACE", "tp": tp_id, "expected": expected, "actual": actual[tp_id]})
    for line, _, viewpoint in cases:
        if VIEWPOINT_ID.match(viewpoint) and viewpoint not in required:
            findings.append({"code": "UNKNOWN_TP", "tp": viewpoint, "line": line})
    return findings


def as_text(finding):
    code = finding["code"]
    if code == "NO_CASES":
        return code
    if code == "UNKNOWN_TP":
        return f"UNKNOWN_TP {finding['line']} {finding['tp']}"
    if code == "TRACE":
        return f"TRACE {finding['tp']} expected>={finding['expected']} actual={finding['actual']}"
    if code == "SEQUENCE":
        return f"SEQUENCE {finding['line']} expected {finding['expected']} got {finding['actual']}"
    if "value" in finding:
        return f"{code} {finding['line']} {finding['value']}"
    return f"{code} {finding['line']}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path")
    parser.add_argument("--viewpoints", help="数え直しに使う step2-viewpoints.md")
    parser.add_argument("--json", action="store_true", help="JSON レシートを出力する")
    args = parser.parse_args()
    text = read_text(args.path)
    viewpoints_text = read_text(args.viewpoints) if args.viewpoints else None

    findings, cases = check_structure(text)
    if viewpoints_text is not None:
        findings += check_trace(cases, viewpoints_text)
    stats = {"cases": len(cases), "lastCaseId": cases[-1][1] if cases else None}
    raise SystemExit(emit("testcases", args.path, findings, args.json, stats=stats, text_of=as_text))


if __name__ == "__main__":
    main()
