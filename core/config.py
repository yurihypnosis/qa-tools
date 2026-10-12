"""設定ファイル `.qa/<ツール名>.toml` の読み込み（全ツール共通。仕様：contracts.md の C3）。

Python 3.11 以上（tomllib）。エラーは、何をすればよいかを含む ValueError。
"""
import sys
import tomllib
from pathlib import Path

if sys.version_info < (3, 11):
    raise SystemExit(f"Python 3.11 以上が必要（今は {sys.version.split()[0]}）")

REQUIRED = ("platform", "source", "output", "checks")


def load(path, required=REQUIRED):
    path = Path(path)
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"{path} が無い。init を実行する") from None
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"{path} を TOML として読めない: {error}") from None
    missing = [key for key in required if key not in raw]
    if missing:
        raise ValueError(f"{path} に {', '.join(missing)} が無い")
    return raw


def project_root(config_path):
    """設定ファイル（<プロジェクト>/.qa/x.toml）から、利用側プロジェクトのルートを返す。"""
    return Path(config_path).resolve().parent.parent


def resolve_repo(root, name):
    """`source.repo` の名前から、ソースがあるディレクトリを返す。"." は利用側プロジェクト自身。"""
    root = Path(root)
    if name == ".":
        return root
    local = root / ".qa" / "local.toml"
    try:
        paths = tomllib.loads(local.read_text(encoding="utf-8")).get("repos", {})
    except FileNotFoundError:
        paths = {}
    if name not in paths:
        raise ValueError(f"リポジトリ {name!r} の場所が分からない。{local} の [repos] に `{name} = \"<絶対パス>\"` を書く")
    path = Path(paths[name])
    if not path.is_dir():
        raise ValueError(f"{local} の {name} = {str(path)!r} がディレクトリではない")
    return path
