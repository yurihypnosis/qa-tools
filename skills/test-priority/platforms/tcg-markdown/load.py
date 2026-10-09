"""プラットフォーム定義 tcg-markdown：test-case-generator の 4-testcases.md（15 列の表）を読む。

共通部分（scripts/）には、テストケースの列名を書かない。列名との対応はこのファイルだけが持つ。
返す項目の形は docs/design/tools/test-priority.md の「3. 入力」を参照。
"""
import hashlib
import re
from pathlib import Path

COLUMNS = [
    "CaseNo.", "観点ID/Viewpoint ID", "タイトル/Title", "領域/Area", "確認画面/Screen", "機能/Function", "大項目/Category",
    "中項目/Sub category", "小項目/Item", "実施ユーザー/Execution Role", "事前条件/Precondition", "実施手順/Execution Step",
    "期待結果/Expected Result", "重要度/Priority", "備考/Remarks",
]
CASE_COLUMN = COLUMNS[0]  # 取り込み用・レビュー用 CSV の、ケースを指す列の名前
CELL_BREAK = re.compile(r"(?<!\\)\|")  # エスケープされた `\|` はセル内の文字として扱う
BODY_COLUMNS = ("事前条件/Precondition", "実施手順/Execution Step", "期待結果/Expected Result")


def split_row(line):
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [cell.strip().replace("\\|", "|") for cell in CELL_BREAK.split(body)]


def cell_text(cell):
    return "\n".join(part.strip() for part in re.split(r"<br\s*/?>", cell))


def load_cases(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    records, in_table = [], False
    for number, line in enumerate(lines, start=1):
        if not line.lstrip().startswith("|"):
            in_table = False
            continue
        cells = split_row(line)
        if cells and cells[0] == COLUMNS[0]:
            if cells != COLUMNS:
                raise ValueError(f"{number} 行目: 列が決まった 15 列と違う")
            in_table = True
            continue
        if not in_table or all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        if len(cells) != len(COLUMNS):
            raise ValueError(f"{number} 行目: 列が {len(cells)} 個ある（15 個のはず）")
        row = dict(zip(COLUMNS, cells))
        priority = row["重要度/Priority"].lower()
        record = {
            "case": row["CaseNo."],
            "title": row["タイトル/Title"],
            "area": row["領域/Area"],
            "feature": row["機能/Function"],
            "screen": row["確認画面/Screen"],
            "existing": priority if priority in ("high", "medium", "low") else "",
            "body": "\n".join(cell_text(row[c]) for c in BODY_COLUMNS),
        }
        record["fingerprint"] = hashlib.sha256(
            "\x1f".join([record["title"], record["area"], record["feature"], record["screen"], record["body"]]).encode("utf-8")
        ).hexdigest()
        records.append(record)
    return records
