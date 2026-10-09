#!/usr/bin/env python3
"""code-map のコマンド。仕様：docs/design/tools/code-map.md

  codemap.py survey --repo-path <リポジトリ> --root <ソースの root> --platform <言語,言語>   init 用。ディレクトリごとのファイル数
  codemap.py extract [--fresh]    lookup/ と _raw/ を書く。役割を書き直すモジュールを JSON で出す（--fresh：前回の役割を捨てる）
  codemap.py apply <下書き>       AI の役割の下書き（1 行：{"module","role"}）を検査して取り込む
  codemap.py assemble             modules/ index.md architecture.md SKILL.md を書く
  codemap.py check [--json] [--no-manifest]
  codemap.py finish               検査に通れば manifest.json を書く

どれも --config .qa/code-map.toml（既定）を取る。終了コード: 0=OK / 1=検査の指摘あり / 2=設定か入力のエラー
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _codemap as cm


def report(findings, stats, config, as_json):
    if as_json:
        print(json.dumps({"check": "check_codemap", "file": str(config["out"]), "status": "fail" if findings else "ok",
                          "findings": findings, "stats": stats}, ensure_ascii=False))
    else:
        print("\n".join(f"{f['code']} {f['file']}:{f['line']} " + json.dumps({k: v for k, v in f.items() if k not in ('code', 'file', 'line')}, ensure_ascii=False) for f in findings) or "OK")
    return 1 if findings else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["survey", "extract", "apply", "assemble", "check", "finish"])
    parser.add_argument("draft", nargs="?")
    parser.add_argument("--config", default=".qa/code-map.toml")
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-manifest", action="store_true")
    parser.add_argument("--repo-path")
    parser.add_argument("--root")
    parser.add_argument("--platform")
    args = parser.parse_args(argv)
    try:
        if args.command == "survey":
            if not (args.repo_path and args.root and args.platform):
                raise ValueError("--repo-path --root --platform が要る")
            print(json.dumps(cm.survey(args.repo_path, args.root, args.platform.split(",")), ensure_ascii=False))
            return 0
        config = cm.load_config(args.config)
        if args.command == "extract":
            print(json.dumps(cm.extract(config, fresh=args.fresh), ensure_ascii=False))
        elif args.command == "apply":
            if not args.draft:
                raise ValueError("下書きのファイルを指定する")
            print(f"{cm.apply_roles(config, cm.read_draft(args.draft))} roles")
        elif args.command == "assemble":
            print(f"{cm.assemble(config)} modules")
        elif args.command == "check":
            findings, stats = cm.check(config, skip_manifest=args.no_manifest)
            return report(findings, stats, config, args.json)
        else:
            findings, stats = cm.finish(config)
            return report(findings, stats, config, True) if findings else (print("manifest.json を書いた"), 0)[1]
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
