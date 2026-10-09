# screen-list の仕様

> **ドラフト**：#22 の仕様。実装（#23〜#25）の前に、読んで違和感のある所を直す。

アプリの**画面とダイアログを、1 行 1 件の CSV（`screens.csv`）に洗い出す**。「どの画面がどこに実装されていて、誰が開けるか」をそろえた一覧にして、テストの範囲を数える土台にする。言葉は [glossary.md](../glossary.md)、共通の約束は [contracts.md](../contracts.md) に従う。

- **状態**：未実装（v0.8.0。Issue #23〜#25）
- **入力**：ソースコード、code-map の出力（公開ファイルの F1・F2・F5）
- **出力**：`output/screen-list/screens.csv`、`manifest.json`。他のツール（test-priority）が読むのは `screens.csv` の `画面ID` 列と `画面名` 列（F4）

## 1. 方針：画面があるかはソースで決め、AI は名前と権限だけ

| 決めるもの | 誰が | 理由 |
| --- | --- | --- |
| 画面・ダイアログが**あるか**、その ID・種別・URL・ソース・モジュール・親 | スクリプト | ファイルの置き場所や import から機械的に決まる。AI に任せると、実行のたびに数が変わる（P3） |
| **画面名**・**ロール**・備考 | AI | ソースを読んで意味を判断する部分（P3）。決められなければ `[未解決: 理由]`（P5） |

画面の数は、AI の出力ではなく、スクリプトが列挙した候補の数で決まる。AI が「画面ではない」と思っても、候補を消せない。消したいときは、人が `adjudications.json` で除外する（7）。

## 2. 処理の流れ

| 段 | `--stage` | 誰が | 内容 |
| --- | --- | --- | --- |
| 候補 | `candidates` | スクリプト | プラットフォーム定義が画面・ダイアログの候補を列挙し、`_raw/candidates.jsonl` に書く（4）。code-map の `tree.md` でモジュールを、`reverse_imports.jsonl` で親画面を埋める |
| 分割 | `partition` | スクリプト | 候補を ID の昇順に、`rules.group_size` 件ずつのグループに分ける（仮：10） |
| 抽出 | `extract` | AI（グループごとに並列） | 候補のソースを読み、画面名・ロール・備考を `_raw/parts/<番号>.jsonl` に書く（5） |
| 結合 | `merge` | スクリプト | 候補と AI の part から `screens.csv` を書く |
| 完了 | `finish` | スクリプト | 検査（8）に通れば `manifest.json` を書く（C2） |

## 3. `screens.csv`

UTF-8 BOM 付き。1 行 1 件。行は `画面ID` の昇順。

| 列 | 誰が | 内容 |
| --- | --- | --- |
| `画面ID` | スクリプト | `<接頭辞>/<画面のキー>`（4.2）。一意 |
| `画面名` | AI | 利用者に見える名前（ページの見出し、ナビの文言など）。決められなければ `[未解決: 理由]` |
| `種別` | スクリプト | `画面` か `ダイアログ` |
| `ロール` | AI | その画面を開ける（見える）ロール。`;` 区切り。語彙は設定の `rules.roles` ＋ `全員`。決められなければ `[未解決: 理由]` |
| `URL` | スクリプト | URL のパス（例：`/settings`）。ダイアログは空 |
| `ソース` | スクリプト | `ファイル:行`。画面は `default export` の行（無ければ 1）。ダイアログはコンポーネントのファイルの先頭の行 |
| `モジュール` | スクリプト | `tree.md` から引いた、そのファイルのモジュール（F1）。引けなければ空 |
| `親画面ID` | スクリプト | ダイアログは、それを開く画面の ID（`;` 区切り。4.4）。画面は、設定の `rules.extra` の `parent`、それ以外は空 |
| `備考` | AI | 補足があれば 1 文。無ければ空 |

## 4. プラットフォーム定義（UI フレームワーク）

`skills/screen-list/platforms/<名前>/candidates.py` が用意する（C9）。共通部分は、フレームワークを知らない。

| 名前 | 内容 |
| --- | --- |
| `PREFIX` | 画面 ID の接頭辞（例：`web`） |
| `candidates(repo_root, root, rules)` | 候補の一覧を返す。各要素：`{"key", "kind", "file", "line", "url"}`（`url` はダイアログなら null） |

最初に作るのは `nextjs-app-router`（`PREFIX = "web"`）。

### 4.1 `nextjs-app-router` の候補

| 候補 | 見つけ方 | 種別 |
| --- | --- | --- |
| 画面 | `app/` か `src/app/`（`rules.app_dir` で指定。無ければ、あるほう）の下の `page.tsx` `page.jsx` `page.ts` `page.js` | `画面` |
| ダイアログ | `rules.dialog_imports`（ダイアログ部品のパスの前方一致のリスト）のどれかを import しているファイル。ただし `page` と `layout` のファイルは除く（画面そのものであり、ダイアログの部品ではない） | `ダイアログ` |
| 申告された画面 | `rules.extra` に書かれたもの（4.5） | `画面` |

### 4.2 画面のキーと ID

| 候補 | キー | ID |
| --- | --- | --- |
| 画面 | URL のパス（先頭の `/` を除く）。`/` は `index` | `web/<キー>`（例：`/settings` → `web/settings`、`/` → `web/index`） |
| ダイアログ | ファイルのパス（リポジトリのルートから、拡張子を除く） | `web#<キー>`（例：`web#src/features/quiz/components/delete-dialog`） |
| 申告された画面 | `rules.extra` の `key` | `web/<key>` |

- URL のパスは、フォルダ名から作る。`(auth)` のようなルートグループのフォルダは URL に含めない。`[id]` のような動的な部分は、書かれたまま残す（`web/tasks/[id]`）。`_` で始まるフォルダは、無いものとして扱う。`@` で始まるフォルダを含む `page` は、親の画面の一部なので、候補にしない
- ID が重複したら、止まる（`DUPLICATE_ID`）。名前の変更（ファイルの移動）で ID が変わるのは仕様。画面名を変えても ID は変わらない
- 画面のキーを URL のパスにするので、**ページの URL を変えた**ときだけ、画面の ID が変わる

### 4.3 画面名・ロールを AI が決める材料

AI は、候補ごとに `ソース` のファイルを読む。画面は、ページのファイルから import している、同じアプリのコンポーネントも読んでよい（見出しやガードが、そこにあることが多いため）。ロールは、ページやレイアウトの認証・認可の処理（ガード、ロールの比較）から決める。コードに根拠が無ければ `[未解決: …]`。

### 4.4 親画面

ダイアログのファイルを起点に、`reverse_imports.jsonl`（F5）を上へ辿り、**最初に当たった `page` のファイル**の画面 ID を親とする。`page` を通り越して、さらに上は辿らない。複数の `page` に当たれば、全部（ID の昇順、`;` 区切り）。どの `page` にも当たらなければ空。

### 4.5 申告された画面 `rules.extra`

URL を変えずに、ページの中の状態で切り替わる表示（`?screen=` など）は、ファイルの置き場所からは見つけられない。画面として数えたいものは、**人が設定に書く**。

```toml
[[rules.extra]]
key = "index?screen=analysis"          # 画面 ID の後半。画面の中で一意
source = "src/features/quiz/screens/analysis-screen.tsx"
parent = "web/index"                    # 開く画面の ID
```

書かれたものは候補に入り、網羅チェックの期待にも入る。AI の判断で、勝手に画面を増やさない（P5）。

## 5. AI が書く part `_raw/parts/<番号>.jsonl`

1 候補 1 行。キーは `id` `name` `roles` `note` だけ。

```json
{"id": "web/settings", "name": "設定", "roles": ["全員"], "note": ""}
```

- `id` は、そのグループの候補の ID と一致しなければならない。足りない・余る ID があれば、取り込みでエラー（`apply_parts.py`。1 行でも誤りがあれば何も書かない）
- `roles` の値は、語彙の中か、`[未解決: 理由]` の 1 要素

## 6. 設定ファイル `.qa/screen-list.toml`

```toml
platform = "nextjs-app-router"

[source]
repo = "sample-app"
root = "."                      # 読み始めるディレクトリ（repo からの相対パス）

[output]
dir = "output/screen-list"

[rules]
app_dir = "src/app"             # 省略可
dialog_imports = ["src/shared/components/ui/dialog"]
roles = ["管理者", "一般ユーザー", "閲覧者"]
group_size = 10                 # 仮（11）

[checks]
run = ["coverage"]
```

- ロールの値は、`.qa/product.md` のロール表と同じものを使う
- code-map の出力（`output/code-map/`）が無い、または古い（`manifest.json` の `source.commit` が、今のコミットと違う）ときは、そのことを伝えて止まる（F2）

## 7. 人の裁定 `output/screen-list/adjudications.json`

```json
{
  "web/dev/preview": { "除外": true, "理由": "開発用のページで、利用者には出ない" },
  "web/settings/team": { "引き継ぎ元": "web/settings/members", "理由": "URL を変えたが、同じ画面" }
}
```

| キー | 意味 |
| --- | --- |
| `除外` | その候補を、CSV に入れず、網羅チェックの期待からも外す |
| `引き継ぎ元` | 新しい ID（キー）に、古い ID の画面名・ロール・備考を引き継ぐ（4.2：URL が変わると ID も変わるため） |

- `理由` は必須。記録は `adjudicate.py`（`core/carry.py`）で行い、`build` でも消えない
- 入力に無い ID を指していたら、検査が `ADJUDICATION_UNKNOWN_ID` を返す

## 8. 検査 `check_screens.py`（C6 の形）

| `code` | 条件 |
| --- | --- |
| `COLUMNS` | `screens.csv` の列が、3 の 9 列と違う |
| `VALUE` | `種別` が `画面` `ダイアログ` 以外、または `ロール` が語彙の外（`[未解決: …]` は可） |
| `COVERAGE` | 候補（＋申告された画面、− 除外）の ID と、CSV の `画面ID` が、完全には一致しない（`exact`） |
| `DUPLICATE_ID` | `画面ID` が重複している |
| `PARENT` | `親画面ID` が、CSV に無い ID を指している |
| `ADJUDICATION_UNKNOWN_ID` | 7 の裁定が、候補に無い ID を指している |
| `MANIFEST` | manifest.json が無い、または必須のキーが欠けている |

`stats`：`candidates` `rows` `unresolved`（`[未解決: …]` を含む行の数）`dialogs`。

## 9. manifest.json（C5）

| キー | 値 |
| --- | --- |
| `source` | `{"repo": <設定の repo>, "commit": <HEAD>}`（code-map と同じ決め方。`+dirty` もある） |
| `inputs` | `{"code-map": <読んだ code-map の manifest の source>}` |
| `generated_by` | `claude`：今回 AI が名前・ロールを書いた行の数。`carried`：前回の名前・ロールを使い回した行の数。`script`：0 |
| `items` | CSV の行数 |

## 10. update と引き継ぎ（#25 で実装）

- キーは `画面ID`、ハッシュは「`ソース` のファイルの内容と、ダイアログなら `親画面ID`」（`core/carry.py` の `split`）。変わっていない行の `画面名` `ロール` `備考` は、AI に書き直させない（P6）
- ID が消えて、ID が現れたとき、ソースの内容が同じなら「名前の変更の候補」として人に挙げる。人が `引き継ぎ元` を裁定すれば、そこから引き継ぐ。しなければ、新しい行として AI が書く
- 前回の code-map の `source.commit` と今回が違うときは、`tree.md` の `モジュール` と `reverse_imports.jsonl` の親画面を、スクリプトが全行で取り直す（AI は呼ばない）

## 11. 仮の値（P9）

| 値 | 初期値 | 見直し方 |
| --- | --- | --- |
| グループの大きさ `group_size` | 10 | AI が 1 回で読める量を、サンプルアプリで見て決める |
| 親画面の辿り方（最初に当たった `page` で止める） | 左のとおり | 親が多すぎる・足りないダイアログが多ければ、辿り方を変える |
| 画面名を、ページから import している部品まで読む | 読んでよい | `[未解決]` の数で測る |
