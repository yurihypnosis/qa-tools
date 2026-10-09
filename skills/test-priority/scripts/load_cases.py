#!/usr/bin/env python3
"""テストケースを読み、判断（judge）の入力 `_raw/cases.jsonl` を書く。

使い方: load_cases.py [--config .qa/test-priority.toml]
終了コード: 0=OK / 2=設定か入力のエラー
"""
import argparse
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
        cases = pr.load_cases(config)
    except (pr.ConfigError, pr.InputError) as error:
        print(error, file=sys.stderr)
        return 2
    pr.write_jsonl(pr.raw_dir(config) / "cases.jsonl", cases)
    print(f"{len(cases)} cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
