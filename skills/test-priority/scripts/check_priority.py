#!/usr/bin/env python3
"""出力を検査する（読み取り専用）。仕様：docs/design/tools/test-priority.md の「9. 検査」

見つけるもの:
  COLUMNS / VALUE / EXCLUDED_ROW / COVERAGE / ADJUDICATION_UNKNOWN_CASE（checks.run に import-clean がある）
  EXAMPLE（checks.run に examples がある）
  MANIFEST（--no-manifest を付けないとき）

使い方: check_priority.py [--config .qa/test-priority.toml] [--json] [--no-manifest]
終了コード: 0=OK / 1=指摘あり / 2=入力エラー
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _priority as pr


def text_of(finding):
    detail = {k: v for k, v in finding.items() if k not in ("code", "file", "line")}
    return f"{finding['code']} {finding['file']}:{finding['line']} {json.dumps(detail, ensure_ascii=False)}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default=".qa/test-priority.toml")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-manifest", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = pr.load_config(args.config)
        findings, stats = pr.check(config, skip_manifest=args.no_manifest)
    except (pr.ConfigError, pr.InputError) as error:
        print(error, file=sys.stderr)
        return 2
    if args.json:
        receipt = {"check": "check_priority", "file": str(config["out_dir"]), "status": "fail" if findings else "ok",
                   "findings": findings, "stats": stats}
        print(json.dumps(receipt, ensure_ascii=False))
    else:
        print("\n".join(text_of(f) for f in findings) if findings else "OK")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
