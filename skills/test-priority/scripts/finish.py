#!/usr/bin/env python3
"""検査（manifest 以外）に通ったら manifest.json を書く。通らなければ書かない（contracts.md の C2）。

使い方: finish.py [--config .qa/test-priority.toml]
  AI が今回何も作らなかったケース（_raw/plan.json に載らなかったもの）を、引き継ぎ（carried）と数える。
終了コード: 0=OK（manifest を書いた） / 1=検査に通らなかった / 2=入力エラー
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
        findings, stats = pr.check(config, skip_manifest=True)
    except (pr.ConfigError, pr.InputError) as error:
        print(error, file=sys.stderr)
        return 2
    if findings:
        receipt = {"check": "check_priority", "file": str(config["out_dir"]), "status": "fail", "findings": findings, "stats": stats}
        print(json.dumps(receipt, ensure_ascii=False))
        return 1
    items = stats["cases"]
    carried = pr.carried_count(config, pr.load_cases(config))
    pr.manifest.write(
        config["out_dir"],
        tool="test-priority",
        source={"files": config["cases_glob"], "hash": pr.source_hash(config)},
        config_hash_value=pr.manifest.config_hash(config["path"]),
        inputs={},
        generated_by={"claude": items - carried, "carried": carried},
        items=items,
    )
    print(f"manifest.json を書いた（{items} 件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
