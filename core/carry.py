"""前回の項目の引き継ぎと、人の裁定の記録（全ツール共通。仕様：docs/design/contracts.md の C7）。

ツールは「項目のキー ＋ 内容のハッシュ」を渡すだけでよい。何をキーとハッシュにするかは、ツールが決める。
"""
import json
import os
import tempfile
from pathlib import Path


def split(previous, current):
    """前回と今回の {キー: ハッシュ} を比べ、引き継ぐもの・作り直すもの・消えたものに分ける（各々ソート済み）。"""
    return {
        "carried": sorted(k for k in current if previous.get(k) == current[k]),
        "changed": sorted(k for k in current if previous.get(k) != current[k]),
        "removed": sorted(k for k in previous if k not in current),
    }


def load(path):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".carry-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def record(path, key, value):
    """裁定を 1 件記録する。同じキーがあれば丸ごと置き換え、他のキーはそのまま残す。"""
    data = load(path)
    data[key] = value
    _save(path, data)


def forget(path, key):
    """裁定を 1 件消す。消したら True、元から無ければ False。"""
    data = load(path)
    if key not in data:
        return False
    del data[key]
    _save(path, data)
    return True
