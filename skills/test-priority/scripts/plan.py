#!/usr/bin/env python3
"""update 用：何を AI がやり直すかを決める（core/carry.py で前回と比べる）。結果を JSON で出す。

使い方:
  plan.py judge   [--config ...]  判断のやり直しが要るケース（新規・内容が変わった）を _raw/pending.jsonl に書く
  plan.py explain [--config ...]  理由文のやり直しが要るケース（新規・重要度が変わった）を _raw/explain_input.jsonl に書く
                                  （先に judge の取り込みと decide.py が済んでいること）
どちらも _raw/plan.json に記録する。finish.py は、ここに載らなかったケースを「引き継ぎ」と数える。
終了コード: 0=OK / 2=設定か入力のエラー
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _priority as pr


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("stage", choices=["judge", "explain"])
    parser.add_argument("--config", default=".qa/test-priority.toml")
    args = parser.parse_args(argv)
    try:
        config = pr.load_config(args.config)
        result = pr.plan_judge(config) if args.stage == "judge" else pr.plan_explain(config)
    except (pr.ConfigError, pr.InputError) as error:
        print(error, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
