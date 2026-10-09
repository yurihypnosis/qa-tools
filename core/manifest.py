#!/usr/bin/env python3
"""manifest.json の読み書きと検査（全ツール共通。仕様：docs/design/contracts.md の C5）。

使い方: manifest.py check <出力ディレクトリ> [--json]
終了コード: 0=OK / 1=指摘あり / 2=入力エラー
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

VERSION = 1
REQUIRED = ("tool", "version", "source", "config_hash", "inputs", "generated_at", "generated_by", "items")
GENERATED_BY_KEYS = ("claude", "script", "carried", "local")
FILE_NAME = "manifest.json"


def config_hash(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(data):
    """問題の一覧を返す。空なら正しい。"""
    problems = [f"キーが無い: {key}" for key in REQUIRED if key not in data]
    if problems:
        return problems
    if data["version"] != VERSION:
        problems.append(f"version は {VERSION} のはず: {data['version']!r}")
    source = data["source"]
    if not (set(source) == {"repo", "commit"} or set(source) == {"files", "hash"}):
        problems.append("source は {repo, commit} か {files, hash} のどちらか")
    by = data["generated_by"]
    unknown = sorted(set(by) - set(GENERATED_BY_KEYS))
    if unknown:
        problems.append(f"generated_by に知らないキー: {unknown}")
    elif not all(isinstance(by.get(k, 0), int) and by.get(k, 0) >= 0 for k in GENERATED_BY_KEYS):
        problems.append("generated_by の値は 0 以上の整数")
    elif sum(by.get(k, 0) for k in GENERATED_BY_KEYS) != data["items"]:
        problems.append(f"generated_by の合計と items が違う: items={data['items']}")
    return problems


def write(directory, *, tool, source, config_hash_value, inputs, generated_by, items, generated_at=None):
    data = {
        "tool": tool,
        "version": VERSION,
        "source": source,
        "config_hash": config_hash_value,
        "inputs": inputs,
        "generated_at": generated_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        "generated_by": {key: generated_by.get(key, 0) for key in GENERATED_BY_KEYS},
        "items": items,
    }
    unknown = sorted(set(generated_by) - set(GENERATED_BY_KEYS))
    problems = [f"generated_by に知らないキー: {unknown}"] if unknown else validate(data)
    if problems:
        raise ValueError("; ".join(problems))
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".manifest-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp, directory / FILE_NAME)
    except BaseException:
        os.unlink(tmp)
        raise
    return data


def read(directory):
    return json.loads((Path(directory) / FILE_NAME).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("directory")
    check.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.directory) / FILE_NAME
    if not path.is_file():
        print(f"{path} が無い", file=sys.stderr)
        return 2
    try:
        problems = validate(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as error:
        problems = [f"JSON として読めない: {error}"]
    findings = [{"code": "MANIFEST", "file": str(path), "line": 1, "message": p} for p in problems]
    if args.json:
        status = "fail" if findings else "ok"
        print(json.dumps({"check": "manifest", "file": str(path), "status": status, "findings": findings}, ensure_ascii=False))
    else:
        print("\n".join(f["message"] for f in findings) if findings else "OK")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
