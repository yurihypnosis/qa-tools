"""検査スクリプト共通の、最小限の Markdown 読み取り（標準ライブラリのみ）。

対象は本 skill が生成する成果物の書式に限る。汎用の Markdown パーサではない。
"""
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
TP_HEADING = re.compile(r"^###\s+(TP-\d{3}(?:〜\d{3})?)\b")
SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")
BOLD = re.compile(r"\*\*[^*]+\*\*")


@dataclass
class Table:
    line: int  # ヘッダ行の行番号（1 始まり）
    header: list
    rows: list = field(default_factory=list)  # [(行番号, [セル...])]
    tp: str | None = None  # 属する TP 見出しの ID（TP 外なら None）


@dataclass
class Document:
    headings: list  # [(行番号, レベル, 行テキスト, 属する TP or None)]
    tables: list


def split_row(line):
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [cell.strip() for cell in body.split("|")]


def is_separator(cells):
    return bool(cells) and all(SEPARATOR_CELL.match(c) for c in cells)


def parse(text):
    """見出しと表を、TP 見出しへの所属付きで取り出す。コードブロック内は無視する。"""
    headings, tables = [], []
    tp = None
    table = None
    in_code = False
    lines = text.splitlines()
    for index, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            in_code = not in_code
            table = None
            continue
        if in_code:
            continue

        if line.lstrip().startswith("|"):
            cells = split_row(line)
            if table is None:
                nxt = lines[index].rstrip() if index < len(lines) else ""
                if nxt.lstrip().startswith("|") and is_separator(split_row(nxt)):
                    table = Table(line=index, header=cells, tp=tp)
                    tables.append(table)
            elif not is_separator(cells):
                table.rows.append((index, cells))
            continue
        table = None

        match = HEADING.match(line)
        if not match:
            continue
        level = len(match.group(1))
        tp_match = TP_HEADING.match(line)
        if level <= 2:
            tp = None
        elif tp_match:
            tp = tp_match.group(1)
        headings.append((index, level, line, None if tp_match else tp))
    return Document(headings=headings, tables=tables)


def expand_tp(tp_id):
    """`TP-010〜012` のようなまとめ見出しを個別の ID に展開する。"""
    match = re.match(r"^TP-(\d{3})(?:〜(\d{3}))?$", tp_id)
    start = int(match.group(1))
    end = int(match.group(2) or start)
    return [f"TP-{n:03d}" for n in range(start, end + 1)]


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as error:
        sys.stderr.write(f"error: cannot read {path}: {error.strerror}\n")
        sys.exit(2)


def emit(check, path, findings, as_json, stats=None, text_of=None):
    """結果を出力し、終了コード（0=OK / 1=指摘あり）を返す。"""
    if as_json:
        receipt = {
            "check": check,
            "file": str(path),
            "status": "fail" if findings else "ok",
            "findings": findings,
        }
        if stats is not None:
            receipt["stats"] = stats
        print(json.dumps(receipt, ensure_ascii=False))
    elif findings:
        for finding in findings:
            print(text_of(finding))
    else:
        print("OK")
    return 1 if findings else 0
