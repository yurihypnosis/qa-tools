#!/usr/bin/env python3
"""AI の判断（_raw/judgments.jsonl）と設定から、重要度・規模・代表・要レビューを計算して JSON Lines で出す。

使い方: decide.py [--config .qa/test-priority.toml]
終了コード: 0=OK / 2=設定か入力のエラー（判断が無い、古い、など）
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _priority as pr


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default=".qa/test-priority.toml")
    args = parser.parse_args(argv)
    try:
        config = pr.load_config(args.config)
        rows = pr.decide_from_files(config)
    except (pr.ConfigError, pr.InputError) as error:
        print(error, file=sys.stderr)
        return 2
    for r in rows:
        print(json.dumps({"case": r["case"], "start": pr.level_name(r["start"]) or None, "level": pr.level_name(r["level"]) or None,
                          "scale": r["scale"], "representative": r["representative"], "marks": r["marks"],
                          "effective_axes": r["effective_axes"], "blocked_by": r["blocked_by"],
                          "adjudicated": bool(r["adjudication"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
