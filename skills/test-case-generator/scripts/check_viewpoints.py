#!/usr/bin/env python3
"""Step 2 の観点ファイルを、ゲート2の前に検査する（読み取り専用）。

見つけるのは「人が読んでも気づきにくく、情報を足さずに直せる」崩れだけ:
  BOLD <行>            TP 配下の 2 列以上の表で、データ行に太字セルが 1 つも無い
  HEADING <行> <見出し>  TP 配下で DT／確認パターン表のタイトルが見出しになっている

使い方: check_viewpoints.py <step2-viewpoints.md> [--json]
終了コード: 0=OK / 1=指摘あり / 2=入力エラー
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _markdown import BOLD, emit, parse, read_text


def check(text):
    doc = parse(text)
    findings = []
    for table in doc.tables:
        if table.tp is None or len(table.header) < 2 or not table.rows:
            continue
        # 1 列目は行ラベル（DT の `**期待結果**` など）なので、期待結果のセルとは数えない
        if not any(BOLD.search(cell) for _, cells in table.rows for cell in cells[1:]):
            findings.append({"code": "BOLD", "line": table.line})
    for line, level, heading, tp in doc.headings:
        if tp is not None and level >= 3:
            findings.append({"code": "HEADING", "line": line, "heading": heading})
    return sorted(findings, key=lambda f: f["line"])


def as_text(finding):
    if finding["code"] == "HEADING":
        return f"HEADING {finding['line']} {finding['heading']}"
    return f"{finding['code']} {finding['line']}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true", help="JSON レシートを出力する")
    args = parser.parse_args()
    findings = check(read_text(args.path))
    raise SystemExit(emit("viewpoints", args.path, findings, args.json, text_of=as_text))


if __name__ == "__main__":
    main()
