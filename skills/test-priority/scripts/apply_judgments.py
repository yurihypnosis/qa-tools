#!/usr/bin/env python3
"""AI が書いた下書きを、_raw/judgments.jsonl に取り込む（fingerprint などの機械的な項目はここで補う）。

使い方:
  apply_judgments.py judge   <下書き.jsonl> [--config ...]   行の形：{"case","axes","impact","kind"}
  apply_judgments.py explain <下書き.jsonl> [--config ...]   行の形：{"case","reason"}
judge は同じ内容の判断なら前の理由文を残す。explain は、今決まっている重要度を reason_level に記録する。
終了コード: 0=OK / 2=下書きか設定のエラー（1 行でも誤りがあれば何も書かない）
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _priority as pr


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=["judge", "explain"])
    parser.add_argument("draft")
    parser.add_argument("--config", default=".qa/test-priority.toml")
    args = parser.parse_args(argv)
    try:
        config = pr.load_config(args.config)
        draft = pr.read_draft(args.draft, args.mode)
        count = pr.apply_judge(config, draft) if args.mode == "judge" else pr.apply_explain(config, draft)
    except (pr.ConfigError, pr.InputError, OSError) as error:
        print(error, file=sys.stderr)
        return 2
    print(f"{count} judgments" if args.mode == "judge" else f"{count} reasons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
