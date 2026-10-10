#!/usr/bin/env python3
"""screen-list のコマンド。仕様：docs/design/tools/screen-list.md

  screens.py candidates [--fresh]   code-map の出力を読み、画面とダイアログの候補を列挙する。名前を書き直す画面を JSON で出す（--fresh：前回の名前を捨てる）
  screens.py apply <下書き>         AI の下書き（1 行：{"id","name","roles"}）を検査して取り込む
  screens.py merge                  screens.csv を書く
  screens.py check [--json] [--no-manifest]
  screens.py finish                 検査に通れば manifest.json を書く

どれも --config .qa/screen-list.toml（既定）を取る。終了コード: 0=OK / 1=検査の指摘あり / 2=設定か入力のエラー
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _screens as sc


def report(findings, stats, config, as_json):
    if as_json:
        print(json.dumps({"check": "check_screens", "file": str(config["out"]), "status": "fail" if findings else "ok",
                          "findings": findings, "stats": stats}, ensure_ascii=False))
    else:
        print("\n".join(f"{f['code']} {f['file']}:{f['line']} " + json.dumps({k: v for k, v in f.items() if k not in ('code', 'file', 'line')}, ensure_ascii=False) for f in findings) or "OK")
    return 1 if findings else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["candidates", "apply", "merge", "check", "finish"])
    parser.add_argument("draft", nargs="?")
    parser.add_argument("--config", default=".qa/screen-list.toml")
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-manifest", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = sc.load_config(args.config)
        if args.command == "candidates":
            print(json.dumps(sc.candidates(config, fresh=args.fresh), ensure_ascii=False))
        elif args.command == "apply":
            if not args.draft:
                raise ValueError("下書きのファイルを指定する")
            print(f"{sc.apply_names(config, sc.read_draft(args.draft, config))} names")
        elif args.command == "merge":
            print(f"{sc.merge(config)} rows")
        elif args.command == "check":
            findings, stats = sc.check(config, skip_manifest=args.no_manifest)
            return report(findings, stats, config, args.json)
        else:
            findings, stats = sc.finish(config)
            if findings:
                return report(findings, stats, config, True)
            print("manifest.json を書いた")
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
