# screen-list の仕様

アプリの**画面とダイアログを、1 行 1 件の CSV（`screens.csv`）に洗い出す**。「どの画面がどこに実装されていて、誰が開けるか」をそろえた一覧にして、テストの範囲を数える土台にする。言葉は [glossary.md](../glossary.md)、共通の約束は [contracts.md](../contracts.md) に従う。

- **入力**：ソースコード、code-map の出力（公開ファイルの F1・F2・F5）
- **出力**：`output/screen-list/screens.csv` と `manifest.json`。他のツール（test-priority）が読むのは `画面ID` 列と `画面名` 列（F4）

## 1. 小さく作る

| 方針 | 決めたこと |
| --- | --- |
| 画面があるか | **スクリプトが決める**（置き場所と import から機械的に）。AI は画面を増やさず、消せない |
| AI が書くもの | **画面名とロールだけ**（1 画面 1 行）。決められなければ `[未解決: 理由]`（P5） |
| 実行 | AI は 1 回の通し。分割・並列・サブエージェントは使わない |
| 更新 | ソースのファイルの内容のハッシュが変わった画面だけ、AI が名前とロールを書き直す（P6） |
| 除外 | 設定の `rules.exclude`（画面 ID のリスト）に書く。別の裁定ファイルは作らない |
| コマンド | スクリプトは `scripts/screens.py` 1 つ |

## 2. `screens.csv`

UTF-8 BOM 付き。1 行 1 件。行は `画面ID` の昇順。

| 列 | 誰が | 内容 |
| --- | --- | --- |
| `画面ID` | スクリプト | 画面は `<接頭辞>/<キー>`、ダイアログは `<接頭辞>#<キー>`（3）。一意 |
| `画面名` | AI | 利用者に見える名前（ページの見出し、ナビの文言など） |
| `種別` | スクリプト | `画面` か `ダイアログ` |
| `ロール` | AI | その画面を開ける（見える）ロール。`;` 区切り。語彙は設定の `rules.roles` ＋ `全員` |
| `URL` | スクリプト | URL のパス（例：`/settings`）。ダイアログと申告された画面は空 |
| `ソース` | スクリプト | `ファイル:行`。画面は `default export` の行（無ければ 1）。それ以外は 1 |
| `モジュール` | スクリプト | code-map の `tree.md` から引いたモジュール（F1）。引けなければ空 |
| `親画面ID` | スクリプト | ダイアログを開く画面の ID（`;` 区切り。3.3）。申告された画面は設定の `parent` |

## 3. プラットフォーム定義（UI フレームワーク）

`skills/screen-list/platforms/<名前>/candidates.py`（C9）が次を用意する。

| 名前 | 内容 |
| --- | --- |
| `PREFIX` | 画面 ID の接頭辞 |
| `candidates(repo, rules, reverse_imports)` | 候補の一覧を返す。各要素：`{"key", "kind", "file", "line", "url", "parents"}`。`reverse_imports` は code-map の `reverse_imports.jsonl`（F5）を `{ファイル: [import しているファイル]}` にしたもの。プラットフォーム定義は、code-map の他のファイルを読まない |

最初に作るのは `nextjs-app-router`（`PREFIX = "web"`）。

### 3.1 候補

| 候補 | 見つけ方 | 種別 |
| --- | --- | --- |
| 画面 | `app_dir`（`rules.app_dir`。無ければ `src/app`、無ければ `app`）の下の `page.tsx` `page.jsx` `page.ts` `page.js` | `画面` |
| ダイアログ | `reverse_imports` の、キー（ファイル）が `rules.dialog_imports`（ダイアログ部品のパスの前方一致のリスト）のどれかで始まるものの、import しているファイル。ただし `page` と `layout` のファイルは除く | `ダイアログ` |
| 申告された画面 | `rules.extra`（3.4） | `画面` |

### 3.2 キーと ID

| 候補 | キー | ID |
| --- | --- | --- |
| 画面 | URL のパス（先頭の `/` を除く）。`/` は `index` | `web/<キー>`（`/settings` → `web/settings`、`/` → `web/index`） |
| ダイアログ | ファイルのパス（リポジトリのルートから、拡張子を除く） | `web#<キー>` |
| 申告された画面 | `rules.extra` の `key` | `web/<key>` |

- URL のパスはフォルダ名から作る。`(auth)` のようなルートグループは含めない。`[id]` のような動的な部分は、書かれたまま残す。`_` で始まるフォルダは無いものとして扱う。`@` で始まるフォルダを含むページと、`(.)` で始まる（割り込みルート）フォルダを含むページは、候補にしない
- ID が重複したら止まる。**ページの URL（ダイアログはファイルの場所）を変えたときだけ、ID が変わる。** 画面名を変えても変わらない

### 3.3 親画面

ダイアログのファイルから、`reverse_imports` を上へ辿り、**最初に当たった `page` のファイル**の画面 ID を親とする（`page` より上は辿らない）。複数に当たれば全部（ID の昇順）。当たらなければ空。

### 3.4 申告された画面

URL を変えずに、ページの中の状態で切り替わる表示は、ファイルの置き場所からは見つけられない。数えたいものは、**人が設定に書く**（AI が勝手に増やさない）。

```toml
[[rules.extra]]
key = "index?screen=analysis"     # 画面 ID の後半。一意
source = "src/features/quiz/screens/analysis-screen.tsx"
parent = "web/index"              # 開く画面の ID
```

## 4. 処理の流れ

| 段 | コマンド | 誰が | 内容 |
| --- | --- | --- | --- |
| 候補 | `screens.py candidates [--fresh]` | スクリプト | code-map の出力を読み（古ければ止まる）、候補を列挙して `_raw/candidates.jsonl` に書く。名前を書き直す画面（前回とソースのハッシュが違う、または新しい）を `_raw/pending.jsonl` に出す。`--fresh` は前回の名前を捨てる |
| 名前 | AI → `screens.py apply <下書き>` | AI | `pending.jsonl` の各画面の `ソース` を読み、下書き `_raw/names.draft.jsonl`（1 行：`{"id","name","roles"}`）を書く。`apply` が検査して `_raw/names.jsonl` に取り込む |
| 結合 | `screens.py merge` | スクリプト | 候補と名前から `screens.csv` を書く |
| 完了 | `screens.py finish` | スクリプト | 検査（6）に通れば `manifest.json` を書く（C2） |

- AI は、画面のファイルから import している同じアプリの部品も読んでよい（見出しやガードがそこにあることが多い）。ロールは、ページやレイアウトの認証・認可の処理から決める。コードに根拠が無ければ `[未解決: …]`
- `画面名` は 80 字以内。`roles` の値は、語彙の中か、`[未解決: 理由]` の 1 要素

## 5. 設定ファイル `.qa/screen-list.toml`

```toml
platform = "nextjs-app-router"

[source]
repo = "sample-app"
root = "src"                         # 未コミットの変更を調べる範囲（repo からの相対）。code-map の source.root と同じにする
code_map = "output/code-map"         # code-map の出力（利用側プロジェクトからの相対）

[output]
dir = "output/screen-list"

[rules]
dialog_imports = ["src/shared/components/ui/dialog"]   # 無ければ []。ダイアログの候補は無くなる
roles = ["管理者", "一般ユーザー"]                       # 必須。無ければ []（ロールは全員か未解決になる）
exclude = []                         # 候補から外す画面 ID。理由はコメントに書く

[checks]
run = ["coverage"]
```

- `rules.roles` のキーが無ければ `ConfigError`（`init` を勧める）
- code-map の `manifest.json` の `source.commit` が、ソースの今の版（コミット。未コミットの変更があれば `+dirty` も）と文字列として違うときは止まる（`code-map update` を勧める。F2）
- `rules.exclude` に、候補に無い ID があれば止まる

## 6. 検査 `check`（C6 の形）

| `code` | 条件 |
| --- | --- |
| `COVERAGE` | 候補（＋申告された画面、− 除外）の ID と、CSV の `画面ID` が一致しない |
| `VALUE` | `種別` が `画面` `ダイアログ` 以外、または `ロール` が語彙の外（`[未解決: …]` は可）、または `画面名` が空 |
| `DUPLICATE_ID` | `画面ID` が重複している |
| `MANIFEST` | manifest.json が無い、または必須のキーが欠けている |

`stats`：`candidates` `rows` `dialogs` `unresolved`（`[未解決: …]` を含む行の数）。

**確かめられること**：CSV が候補と一致していること（AI の抜け・余り、手での編集、古い CSV）。**確かめられないこと**：候補の列挙そのものの正しさ。「検査が通った」は「画面が全部ある」ことを意味しない。列挙は、プラットフォーム定義のテスト（fixture：ルートグループ、動的セグメント、`_` と `@` のフォルダ、ダイアログなど）で確かめる。

## 7. manifest.json（C5）

| キー | 値 |
| --- | --- |
| `source` | `{"repo": <設定の repo>, "commit": <先頭 7 桁>}`（`+dirty` もある。`core/gitinfo.py`） |
| `inputs` | `{"code-map": <読んだ code-map の manifest の source>}` |
| `generated_by` | `claude`：今回 AI が名前とロールを書いた行の数。`carried`：使い回した行の数。`script`：0 |
| `items` | CSV の行数 |

## 8. update

`build` と `update` の違いは、`candidates` に `--fresh` を付けるかだけ。付けなければ、ソースのハッシュ（そのファイルの内容と、親画面）が前回と同じ画面は、名前とロールを使い回す（`core/carry.py` の `split`）。ページの URL を変えると ID が変わるので、新しい画面として AI が書く。

## 9. 仮の値（P9）

| 値 | 初期値 | 見直し方 |
| --- | --- | --- |
| 親画面の辿り方（最初に当たった `page` で止める） | 左のとおり | 親が多すぎる・足りないダイアログが多ければ変える |
| 画面名を、ページから import している部品まで読んでよい | 読んでよい | `[未解決]` の数で測る |
| ハッシュの対象（ページのファイルの内容と親画面だけ） | 左のとおり | 部品だけが変わって名前が古くなる例が多ければ、対象を広げる |
