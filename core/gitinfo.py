"""ソースの git のコミットを取る（全ツール共通。仕様：contracts.md の C5 の source.commit）。"""
import subprocess
from pathlib import Path


def _git(repo, *args):
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ValueError(f"{repo} は git のリポジトリではない（または git が使えない）: {proc.stderr.strip()}")
    return proc.stdout.strip()


def head(repo, subpath="."):
    """HEAD のコミット（先頭 7 桁）。subpath の下に未コミットの変更があれば `+dirty` を付ける。"""
    repo = Path(repo)
    commit = _git(repo, "rev-parse", "--short=7", "HEAD")
    dirty = _git(repo, "status", "--porcelain", "--", subpath)
    return f"{commit}+dirty" if dirty else commit
