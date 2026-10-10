# init — 設定ファイルを作る

## 契約

| 項目 | 内容 |
| --- | --- |
| 入力 | 読むリポジトリ、code-map の出力の場所 |
| 出力 | `.qa/screen-list.toml`（雛形：`assets/screen-list.template.toml`）。別のリポジトリなら `.qa/local.toml` |
| 検査 | 作った設定で `screens.py candidates --fresh` が動くこと（終了コード 0） |
| 次 | `build` |

## 手順

1. `.qa/screen-list.toml` が既にあれば、上書きしてよいか確かめる。だめなら止まる。
2. 読むリポジトリを聞く。利用側プロジェクト自身なら `repo = "."`。別のリポジトリなら、名前と絶対パスを聞き、`.qa/local.toml` の `[repos]` に書く（`.qa/screen-list.toml` には名前だけを書く）。code-map と同じ名前にする。
3. UI フレームワークを選ぶ。選択肢は `ls <skill>/platforms/` のディレクトリ名から作る（この reference や SKILL.md には書かない）。
4. code-map の出力の場所（既定 `output/code-map`）を確かめる。無ければ、先に code-map の `build` を勧めて止まる。
5. ダイアログの部品（ダイアログを開く共通部品）のファイルを聞く。分からなければ、ソースを検索して候補（`dialog`・`modal` を名前に持つファイル）を見せ、選んでもらう。無ければ `dialog_imports = []`。
6. ロールの一覧を聞く。`.qa/product.md` にロール表があれば、それを見せて確かめる。無ければ `roles = []`。
7. URL を変えずにページの中で切り替わる画面（タブ、`?screen=` など）があるか聞く。先に手順 10 の `candidates` を実行して、出力の `hints`（画面らしいが一覧に入っていないファイル）を見せるとよい。そのうち、ページの中で切り替わる画面だけを、1 つずつ `key` `source` `parent` を聞いて `rules.extra` に書く（ページ本体の部品は書かない）。
8. 除外したい画面があるか聞く（`rules.exclude`。まだ分からなければ空でよい）。
9. `assets/screen-list.template.toml` を雛形に、Write で `.qa/screen-list.toml` を作る。
10. `python3 <skill>/scripts/screens.py candidates --fresh` を実行する。終了コードが 0 であることと、`candidates` の件数が、アプリの画面の数として妥当かを確かめる。2 なら、メッセージに従って 1 回だけ直す。
11. 作った設定と件数を見せ、次は `build` だと伝えて終える。

## ルール

- 値を勝手に決めず、答えが無ければ聞く。聞くのは 1 度に 1 つ。
- 絶対パスを `.qa/screen-list.toml` に書かない。
