#!/usr/bin/env python3
"""init 用：テストケースの領域・機能・確認画面を数えて JSON で出す（設定ファイルが無くても動く）。

使い方: survey.py --platform <プラットフォーム定義の名前> --glob <テストケースの glob> [--root <利用側プロジェクト>]
終了コード: 0=OK / 2=プラットフォーム定義か入力のエラー
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _priority as pr


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--platform", required=True)
    parser.add_argument("--glob", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    try:
        result = pr.survey(args.platform, args.root, args.glob)
    except (pr.ConfigError, pr.InputError) as error:
        print(error, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
