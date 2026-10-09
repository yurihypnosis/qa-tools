"""テスト共通：スクリプトを実際の CLI として実行し、終了コードと出力を返す。"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "test-case-generator" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run(script, *args):
    proc = subprocess.run(
        [sys.executable, "-I", str(SCRIPTS / script), *map(str, args)],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_json(script, *args):
    code, out, err = run(script, *args, "--json")
    return code, json.loads(out), err


def codes(receipt):
    return sorted(f["code"] for f in receipt["findings"])


def run_path(script, *args, cwd=None):
    """任意のスクリプトを `python3 -I` で実行する（core/ や他の skill 用）。"""
    proc = subprocess.run(
        [sys.executable, "-I", str(script), *map(str, args)],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return proc.returncode, proc.stdout, proc.stderr
