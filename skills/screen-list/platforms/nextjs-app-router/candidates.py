"""プラットフォーム定義 nextjs-app-router：Next.js の App Router の画面とダイアログの候補を列挙する（docs/design/tools/screen-list.md の 3）。"""
import fnmatch
import os
import posixpath
import re

PREFIX = "web"
PAGE = re.compile(r"^page\.(tsx|jsx|ts|js)$")
GROUP = re.compile(r"^\(.*\)$")                 # ルートグループ (auth)
INTERCEPTING = re.compile(r"^\(\.{1,3}\)")       # 割り込みルート (.)photo
DEFAULT_EXPORT = re.compile(r"^export\s+default\b", re.M)
# 画面らしいファイルの、よくある置き方。ページの中で切り替わる画面（申告が要るもの）の見落としに気づくための目印（確定ではない）
HINT_GLOBS = ("*/screens/*.tsx", "*/screens/*.jsx", "*-screen.tsx", "*Screen.tsx")


def _page_ids(repo, app_dir):
    pages = {}
    base = repo / app_dir
    for folder, dirs, names in os.walk(base):
        dirs.sort()
        rel = os.path.relpath(folder, base)
        segments = [] if rel == "." else rel.split(os.sep)
        if any(s.startswith(("@", "_")) or INTERCEPTING.match(s) for s in segments):
            continue
        parts = [s for s in segments if not GROUP.match(s)]
        key = "/".join(parts) or "index"
        for name in sorted(names):
            if not PAGE.match(name):
                continue
            path = posixpath.join(app_dir, *segments, name)
            text = (repo / path).read_text(encoding="utf-8", errors="replace")
            match = DEFAULT_EXPORT.search(text)
            line = text.count("\n", 0, match.start()) + 1 if match else 1
            pages[path] = {"key": key, "kind": "画面", "file": path, "line": line, "url": "/" + "/".join(parts), "parents": []}
    return pages


def _parents(start, importers, page_ids):
    """start から import を上へ辿り、最初に当たった page の ID を返す（page より上は辿らない）。"""
    found, seen, queue = set(), {start}, [start]
    while queue:
        for file in importers.get(queue.pop(), ()):
            if file in seen:
                continue
            seen.add(file)
            if file in page_ids:
                found.add(page_ids[file])
            else:
                queue.append(file)
    return sorted(found)


def candidates(repo, rules, reverse_imports):
    app_dir = rules.get("app_dir") or ("src/app" if (repo / "src" / "app").is_dir() else "app")
    if not (repo / app_dir).is_dir():
        raise ValueError(f"{app_dir} が {repo} の下に無い。rules.app_dir を設定する")
    pages = _page_ids(repo, app_dir)
    page_ids = {path: f"{PREFIX}/{p['key']}" for path, p in pages.items()}
    prefixes = tuple(rules.get("dialog_imports", []))
    dialogs = {}
    for target, importers in reverse_imports.items():
        if prefixes and target.startswith(prefixes):
            for file in importers:
                stem = posixpath.splitext(posixpath.basename(file))[0]
                if stem not in ("page", "layout") and not file.startswith(prefixes):
                    dialogs[file] = {"key": posixpath.splitext(file)[0], "kind": "ダイアログ", "file": file, "line": 1, "url": "",
                                     "parents": _parents(file, reverse_imports, page_ids)}
    return list(pages.values()) + list(dialogs.values())


def hints(files, rules):
    """画面らしいファイル（`rules.screen_hints` の glob。無ければ既定）を返す。files は code-map が読んだファイル。候補に入っているかは、呼び出し側が見る。"""
    globs = rules.get("screen_hints", HINT_GLOBS)
    return sorted(f for f in files if any(fnmatch.fnmatch(f, g) for g in globs))


def id_of(candidate):
    return f"{PREFIX}/{candidate['key']}" if candidate["kind"] == "画面" else f"{PREFIX}#{candidate['key']}"
