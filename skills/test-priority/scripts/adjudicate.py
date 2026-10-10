#!/usr/bin/env python3
"""人の裁定を output/test-priority/adjudications.json に記録する（core/carry.py）。

使い方:
  adjudicate.py <ケース> [--level R1〜R4] [--scale sanity|smoke|light|full|対象外] --reason <理由> [--config ...]
  adjudicate.py --remove <ケース> [--config ...]
記録したら、update を実行して結果に反映する。裁定は build でも消えない。
終了コード: 0=OK / 2=入力エラー（ケースが無い、理由が無い、など）
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _priority as pr


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("case", nargs="?")
    parser.add_argument("--level")
    parser.add_argument("--scale")
    parser.add_argument("--reason")
    parser.add_argument("--remove")
    parser.add_argument("--config", default=".qa/test-priority.toml")
    args = parser.parse_args(argv)
    try:
        config = pr.load_config(args.config)
        path = config["out_dir"] / "adjudications.json"
        if args.remove:
            if not pr.carry.forget(path, args.remove):
                raise pr.InputError(f"{args.remove} の裁定は無い")
            print(f"{args.remove} の裁定を消した")
            return 0
        if not args.case:
            raise pr.InputError("ケースを指定する（消すときは --remove）")
        value = pr.adjudicate(config, args.case, args.level, args.scale, args.reason)
    except (pr.ConfigError, pr.InputError) as error:
        print(error, file=sys.stderr)
        return 2
    print(f"{args.case} の裁定を記録した: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
