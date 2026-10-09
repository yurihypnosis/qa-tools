# code-map の仕様

ソースコードから、**どこに何があるか**を引ける索引（`lookup/`）と、モジュールごとの役割の説明を作る。AI や人が、ソースを全部読まずに、場所・影響範囲・流れを調べるために使う。言葉は [glossary.md](../glossary.md)、共通の約束は [contracts.md](../contracts.md) に従う。

- **入力**：ソースコード（git のリポジトリ）
- **出力**：`output/code-map/`。他のツール（screen-list）が読むのは「公開ファイル」（F1・F2・F5）

## 1. 小さく作る

| 方針 | 決めたこと |
| --- | --- |
| AI が書くもの | **モジュールごとの役割の説明 1 段落だけ**。ほかは全部、スクリプトが作る（P3） |
| 実行 | AI は 1 回の通しで書く。並列実行・サブエージェントは使わない |
| 更新 | モジュールのファイルの内容のハッシュが変わったモジュールだけ、AI が書き直す。git の差分は使わない（`core/plan.py` は作らない） |
| コマンド | スクリプトは `scripts/codemap.py` 1 つ。サブコマンドで分ける |

## 2. 出力

| ファイル | 誰が作る | 公開 | 内容 |
| --- | --- | --- | --- |
| `manifest.json` | スクリプト（C5） | ✅ | どのコミットから、どの設定で作ったか |
| `lookup/tree.md` | スクリプト | ✅ | ファイルと、ファイルごとのモジュール（3.1） |
| `lookup/symbol_index.tsv` | スクリプト | ✅ | 公開シンボルの一覧（3.2） |
| `lookup/reverse_imports.jsonl` | スクリプト | ✅ | 「このファイルを import しているファイル」（3.3） |
| `modules/<モジュール>.md` | スクリプト（AI の役割を組み込む） | ✅ | モジュールごとの説明（4） |
| `architecture.md` | スクリプト | ✅ | モジュール間の import 数の表 |
| `index.md` | スクリプト | ✅ | モジュールの一覧 |
| `SKILL.md` | スクリプト（雛形のコピー） | ✅ | この出力の辿り方（6） |
| `_raw/` | 両方 | — | 中間ファイル。他のツールは読まない |

## 3. lookup の形

パスは**リポジトリのルートからの相対パス**（`/` 区切り）。行は昇順。同じ入力から同じバイト列ができる（P6）。

### 3.1 `lookup/tree.md`

```markdown
# ファイルツリー

| ファイル | モジュール | 言語 | 行数 |
| --- | --- | --- | --- |
| src/features/quiz/lib/streak.ts | features/quiz | typescript | 54 |
```

見出しと列は固定。他のツールは、この表からファイルのモジュールを引く（F1）。

### 3.2 `lookup/symbol_index.tsv`

ヘッダー `file<TAB>line<TAB>kind<TAB>name` ＋ 1 シンボル 1 行。

| 言語 | 対象 | `kind` |
| --- | --- | --- |
| TypeScript | `export` された function / class / interface / type / enum / const | 左のとおり |
| Python | トップレベルの def / class（名前が `_` で始まらない） | `function` `class` |

### 3.3 `lookup/reverse_imports.jsonl`

1 行 1 ファイル：`{"file": "src/lib/db.ts", "imported_by": ["src/app/page.tsx", …]}`。リポジトリ内のファイルへの import だけ。import されていないファイルの行は無い。

## 4. モジュール

設定の `rules.module_depth`（整数）で決める。ファイルの `source.root` からのディレクトリの、先頭から `module_depth` 個までをモジュール名とする。ルート直下のファイルは `(root)`。

| ファイル（`root = src`、`module_depth = 2`） | モジュール |
| --- | --- |
| `src/features/quiz/lib/streak.ts` | `features/quiz` |
| `src/app/page.tsx` | `app`（ディレクトリが 1 段しか無い） |
| `src/proxy.ts` | `(root)` |

`modules/<モジュール>.md`（名前の `/` は `__` にする。`features/quiz` → `modules/features__quiz.md`）：

```markdown
# features/quiz

## 役割
（AI）このモジュールが何をするか。2〜4 文。

## 主なファイル
（スクリプト）代表ファイル（被参照数の多い上位 `rules.representatives` 個）と被参照数

## 公開シンボル
（スクリプト）symbol_index.tsv から

## 依存先
（スクリプト）import している他のモジュールと、import 数

## 依存元
（スクリプト）import されている他のモジュールと、import 数
```

見出しはこの 5 つ・この順に固定。`役割` の最初の 1 文が、`index.md` の「概要」になる。AI が `役割` に書くパス（バッククォートで囲む）は、`tree.md` にあるファイルだけにする。

## 5. 処理の流れ

| 段 | コマンド | 誰が | 内容 |
| --- | --- | --- | --- |
| 抽出 | `codemap.py extract [--fresh]` | スクリプト | `lookup/` と `_raw/modules.json` を書く。役割を書き直すモジュール（前回と内容のハッシュが違う、または新しい）を `_raw/pending.jsonl` に書く。`--fresh` は前回の役割を捨てる |
| 役割 | AI → `codemap.py apply <下書き>` | AI | `pending.jsonl` の各モジュールの代表ファイルを読み、下書き `_raw/roles.draft.jsonl`（1 モジュール 1 行：`{"module", "role"}`）を書く。`apply` が検査して `_raw/roles.jsonl` に取り込む |
| 組み立て | `codemap.py assemble` | スクリプト | `modules/` `architecture.md` `index.md` `SKILL.md` を書く。消えたモジュールのファイルは消す |
| 完了 | `codemap.py finish` | スクリプト | 検査（9）に通れば `manifest.json` を書く（C2） |

`init` のために、`codemap.py survey` が `source.root` の下のディレクトリごとのファイル数を出す（`module_depth` を決める材料）。

## 6. 出力の `SKILL.md`（辿り方）

雛形 `assets/output-skill.template.md` をそのままコピーする。

| 問い | 辿り方 |
| --- | --- |
| 場所を探す | `lookup/symbol_index.tsv` で名前から `ファイル:行` → `lookup/tree.md` でモジュール → `modules/<モジュール>.md` |
| 影響範囲を見る | `lookup/reverse_imports.jsonl` で依存元を辿る。モジュール単位なら `modules/<モジュール>.md` の `依存元` |
| 通称から実体を引く | `index.md` の概要と各 `modules/*.md` の `役割` を、通称で検索する |
| 流れを追う | `architecture.md` の表で依存を辿り、各 `modules/*.md` を読む |

先頭の注意：「この出力は、当たりを付けるための索引である。根拠はソースコードで、食い違ったらソースを信じる」

## 7. 設定ファイル `.qa/code-map.toml`

```toml
platform = ["typescript", "python"]

[source]
repo = "sample-app"             # "." なら利用側プロジェクト自身。別のリポジトリは .qa/local.toml の [repos] に絶対パスを書く
root = "src"                    # 読み始めるディレクトリ（repo からの相対）
exclude = ["**/*.test.ts"]      # 追加で除く glob。.git node_modules __pycache__ .next dist build は常に除く

[output]
dir = "output/code-map"

[rules]
module_depth = 2
representatives = 5             # 仮（12）

[rules.typescript]
tsconfig = "tsconfig.json"      # repo からの相対

[checks]
run = ["public-files"]
```

`platform` は言語の配列。`root` の下に、どの言語のファイルも無ければ止まる（C3 の 4）。

## 8. プラットフォーム定義（言語）

`skills/code-map/platforms/<言語>/scan.py`（C9）が次を用意する。

| 名前 | 内容 |
| --- | --- |
| `EXTENSIONS` | 対象の拡張子 |
| `load(repo, options)` | その言語の準備（例：tsconfig を読む）。`analyze` に渡す `context` を返す |
| `analyze(repo, path, text, context)` | `{"imports": [リポジトリ内の import 先のパス], "unresolved": 解決できなかった相対 import の数, "symbols": [{"name","kind","line"}]}` |

最初の 2 つ（仮の方式。12）：`typescript` は正規表現で `import … from` `export … from` `import(` `require(` を抜き、相対パスと tsconfig の `paths`（`baseUrl` があればそれも）で解決する。`python` は標準ライブラリの `ast` で、`root` からの絶対 import と相対 import を解決する。

## 9. 検査 `check`（C6 の形）

| `code` | 条件 |
| --- | --- |
| `PUBLIC_MISSING` | 公開ファイル（2 の表の ✅）が無い。`tree.md` のモジュールの `modules/<モジュール>.md` が無い |
| `SECTION` | モジュールのファイルが、4 の 5 つの見出しをこの順に持たない。`役割` が空 |
| `ANCHOR` | `役割` に書かれたバッククォートのパスが、`tree.md` に無い |
| `MANIFEST` | manifest.json が無い、または必須のキーが欠けている |

`stats`：`files` `modules` `symbols` `unresolved`。

## 10. manifest.json（C5）

| キー | 値 |
| --- | --- |
| `source` | `{"repo": <設定の repo>, "commit": <先頭 7 桁>}`。`source.root` の下に未コミットの変更があれば `"<コミット>+dirty"`（`core/gitinfo.py`） |
| `generated_by` | `claude`：今回 AI が役割を書いたモジュール数。`carried`：前回の役割を使い回した数。`script`：0 |
| `items` | モジュール数 |
| `inputs` | `{}` |

## 11. update

`build` と `update` の違いは、`extract` に `--fresh` を付けるかだけ。付けなければ、モジュールの内容のハッシュ（そのモジュールのファイルの（パス、内容のハッシュ）の組をパスの昇順に並べたもの）が前回の役割と同じモジュールは、役割を使い回す（`core/carry.py` の `split`）。ほかのモジュールの `依存先` `依存元` `公開シンボル` は、スクリプトが毎回作り直す。

## 12. 仮の値（P9）

| 値 | 初期値 | 見直し方 |
| --- | --- | --- |
| `representatives` | 5 | 役割の質を、サンプルアプリで見る |
| 代表ファイルの選び方 | 被参照数の多い順 | 足りなければ他の指標を足す |
| TypeScript の import の解決 | 正規表現 ＋ tsconfig | `unresolved` の件数で測る |
