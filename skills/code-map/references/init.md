# init — 設定ファイルを作る

## 契約

| 項目 | 内容 |
| --- | --- |
| 入力 | 索引を作りたいリポジトリの場所 |
| 出力 | `.qa/code-map.toml`（雛形：`assets/code-map.template.toml`）。別のリポジトリなら `.qa/local.toml` |
| 検査 | 作った設定で `codemap.py extract` が動くこと（終了コード 0） |
| 次 | `build` |

## 手順

1. `.qa/code-map.toml` が既にあれば、上書きしてよいか確かめる。だめなら止まる。
2. 読むリポジトリを聞く。利用側プロジェクト自身なら `repo = "."`。別のリポジトリなら、名前（例：`sample-app`）と絶対パスを聞き、`.qa/local.toml` の `[repos]` に `名前 = "絶対パス"` を書く（この絶対パスを `.qa/code-map.toml` に書かない）。
3. 言語を選ぶ。選択肢は `ls <skill>/platforms/` のディレクトリ名から作る（この reference や SKILL.md には書かない）。
4. ソースを読み始めるディレクトリ（`source.root`）を聞く。分からなければ、リポジトリ直下のディレクトリを見せて選んでもらう。
5. 次を実行して、ディレクトリごとのファイル数を調べる。
   ```bash
   python3 <skill>/scripts/codemap.py survey --repo-path <リポジトリの絶対パス> --root <source.root> --platform <言語,言語>
   ```
6. 結果を見せ、モジュールの粒度（`rules.module_depth`）を相談する。`source.root` から数えて何段目までのディレクトリを 1 モジュールにするか。ファイルが 1 モジュールに偏りすぎず、モジュールが多すぎない（目安：5〜20 個）段を勧める。
7. 除外したいファイル（テストなど）があれば聞く（`source.exclude`。glob）。
8. `assets/code-map.template.toml` を雛形に、Write で `.qa/code-map.toml` を作る。
9. `python3 <skill>/scripts/codemap.py extract --fresh` を実行して、終了コードが 0 であることと、モジュールの一覧が意図どおりかを確かめる。2 なら、メッセージに従って 1 回だけ直す。
10. 作った設定とモジュールの一覧を見せ、次は `build` だと伝えて終える。

## ルール

- 値を勝手に決めず、答えが無ければ聞く。聞くのは 1 度に 1 つ。
- 言語ごとの設定（`[rules.<言語>]`）が要るときは、その言語のプラットフォーム定義（`platforms/<言語>/scan.py` の docstring）に従う。
