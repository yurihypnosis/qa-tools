"""プラットフォーム定義 nextjs-app-router：Next.js の App Router のページを列挙する（docs/design/tools/screen-list.md の 3）。

ダイアログ・親画面・ヒントは、フレームワークに依存しないので、本体（scripts/_screens.py）が扱う。ここはページの見つけ方だけを持つ。
"""
import os
import posixpath
import re

PREFIX = "web"
NOT_DIALOG_STEMS = ("page", "layout")            # これらのファイルは、ダイアログの候補にしない
PAGE = re.compile(r"^page\.(tsx|jsx|ts|js)$")
GROUP = re.compile(r"^\(.*\)$")                 # ルートグループ (auth)
INTERCEPTING = re.compile(r"^\(\.{1,3}\)")       # 割り込みルート (.)photo
DEFAULT_EXPORT = re.compile(r"^export\s+default\b", re.M)


def pages(repo, rules):
    """`app_dir`（`rules.app_dir`。無ければ `src/app`、無ければ `app`）の下の page ファイルを、{key, file, line, url} の一覧で返す。"""
    app_dir = rules.get("app_dir") or ("src/app" if (repo / "src" / "app").is_dir() else "app")
    base = repo / app_dir
    if not base.is_dir():
        raise ValueError(f"{app_dir} が {repo} の下に無い。rules.app_dir を設定する")
    found = []
    for folder, dirs, names in os.walk(base):
        dirs.sort()
        rel = os.path.relpath(folder, base)
        segments = [] if rel == "." else rel.split(os.sep)
        if any(s.startswith(("@", "_")) or INTERCEPTING.match(s) for s in segments):
            continue
        parts = [s for s in segments if not GROUP.match(s)]
        for name in sorted(names):
            if PAGE.match(name):
                path = posixpath.join(app_dir, *segments, name)
                text = (repo / path).read_text(encoding="utf-8", errors="replace")
                match = DEFAULT_EXPORT.search(text)
                found.append({"key": "/".join(parts) or "index", "file": path, "url": "/" + "/".join(parts),
                              "line": text.count("\n", 0, match.start()) + 1 if match else 1})
    return found
