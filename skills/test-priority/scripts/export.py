#!/usr/bin/env python3
"""取り込み用 import.csv とレビュー用 review.csv を書く（manifest.json は書かない。finish.py が書く）。

使い方: export.py [--config .qa/test-priority.toml]
終了コード: 0=OK / 2=設定か入力のエラー（理由が無い、古い、など）
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
        rows = pr.export(pr.load_config(args.config))
    except (pr.ConfigError, pr.InputError) as error:
        print(error, file=sys.stderr)
        return 2
    print(f"{len(rows)} cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
