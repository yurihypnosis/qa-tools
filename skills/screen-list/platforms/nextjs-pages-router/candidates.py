"""プラットフォーム定義 nextjs-pages-router：Next.js の Pages Router（`pages/` の下のファイル = ページ）を列挙する。

ダイアログ・親画面・ヒントは、フレームワークに依存しないので、本体（scripts/_screens.py）が扱う。ここはページの見つけ方だけを持つ。
"""
import os
import posixpath
import re

PREFIX = "web"
NOT_DIALOG_STEMS = ("_app", "_document")
EXTENSIONS = (".tsx", ".jsx", ".ts", ".js")
NOT_PAGES = re.compile(r"\.(test|spec|stories)\.|\.d\.ts$")
DEFAULT_EXPORT = re.compile(r"^export\s+default\b", re.M)


def pages(repo, rules):
    """`pages_dir`（`rules.pages_dir`。無ければ `src/pages`、無ければ `pages`）の下のページを、{key, file, line, url} の一覧で返す。
    `api/`（API ルート）と、`_` で始まるファイル（`_app` `_document`）はページではない。`index` は、そのディレクトリの URL になる。"""
    pages_dir = rules.get("pages_dir") or ("src/pages" if (repo / "src" / "pages").is_dir() else "pages")
    base = repo / pages_dir
    if not base.is_dir():
        raise ValueError(f"{pages_dir} が {repo} の下に無い。rules.pages_dir を設定する")
    found = []
    for folder, dirs, names in os.walk(base):
        dirs.sort()
        rel = os.path.relpath(folder, base)
        segments = [] if rel == "." else rel.split(os.sep)
        if segments[:1] == ["api"]:
            continue
        for name in sorted(names):
            stem, ext = posixpath.splitext(name)
            if ext not in EXTENSIONS or stem.startswith("_") or NOT_PAGES.search(name):
                continue
            parts = segments if stem == "index" else segments + [stem]
            path = posixpath.join(pages_dir, *segments, name)
            text = (repo / path).read_text(encoding="utf-8", errors="replace")
            match = DEFAULT_EXPORT.search(text)
            found.append({"key": "/".join(parts) or "index", "file": path, "url": "/" + "/".join(parts),
                          "line": text.count("\n", 0, match.start()) + 1 if match else 1})
    return found
