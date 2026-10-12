"""JSON Lines の読み書き（全ツール共通）。書くときは、キーをソートして、同じ入力なら同じバイト列にする。"""
import json
from pathlib import Path


def read(path):
    """行ごとの辞書のリスト。ファイルが無ければ空。壊れた行は、ファイルと行番号つきの ValueError。"""
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
            raise ValueError(f"{path.name} の {number} 行目を JSON として読めない: {error}") from None
    return rows


def write(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
