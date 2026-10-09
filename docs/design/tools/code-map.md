# code-map の仕様

> **ドラフト**：#16 の仕様。実装（#17〜#21）の前に、読んで違和感のある所を直す。

ソースコードから、**どこに何があるか**を引ける索引（`lookup/`）と、モジュールごとの要約を作る。AI やテスターが、ソースを全部読まずに、場所・影響範囲・流れを調べるために使う。言葉は [glossary.md](../glossary.md)、共通の約束は [contracts.md](../contracts.md) に従う。

- **状態**：未実装（v0.6.0 で `init` `build` `check`、v0.7.0 で `update`。Issue #17〜#21）
- **入力**：ソースコード（git のリポジトリ）
- **出力**：`output/code-map/`。他のツール（screen-list）が読むのは、下の「公開ファイル」だけ

## 1. 何を作るか

| ファイル | 誰が作る | 公開 | 内容 |
| --- | --- | --- | --- |
| `manifest.json` | スクリプト（C5） | ✅ | どのコミットから、どの設定で作ったか |
| `lookup/tree.md` | スクリプト | ✅ | ファイルの一覧と、ファイルごとのモジュール（3.1） |
| `lookup/symbol_index.tsv` | スクリプト | ✅ | 公開シンボル（関数・クラスなど）の一覧（3.2） |
| `lookup/reverse_imports.jsonl` | スクリプト | ✅ | 「このファイルを、どのファイルが import しているか」（3.3） |
| `modules/<モジュール>.md` | スクリプトが、AI の要約とスクリプトの表を組み立てる | ✅ | モジュールごとの要約（4） |
| `architecture.md` | 同上 | ✅ | 全体像と、モジュール間の依存（5） |
| `index.md` | スクリプト | ✅ | モジュールの一覧（6） |
| `SKILL.md` | スクリプト（雛形から） | ✅ | この出力の辿り方（7） |
| `_raw/` | 両方 | — | 中間ファイル。他のツールは読まない |

## 2. 処理の流れ

| 段 | `--stage` | 誰が | 内容 |
| --- | --- | --- | --- |
| 抽出 | `extract` | スクリプト | ファイルを数え、import とシンボルを抜き出し、`lookup/` を書く。モジュールごとの材料（`_raw/modules/<モジュール>.json`）を書く |
| 要約 | `summarize` | AI（モジュールごとに並列） | 材料を読み、`_raw/summaries/<モジュール>.md` に `## 役割` と `## 主なファイル` を書く（4.1） |
| 全体像 | `overview` | AI | `_raw/overview.md` に `## 全体像` を書く（5） |
| 組み立て | `assemble` | スクリプト | `modules/` `architecture.md` `index.md` `SKILL.md` を書く |
| 完了 | `finish` | スクリプト | 検査（9）に通れば `manifest.json` を書く（C2） |

- AI が書くのは、**役割・主なファイルの説明・全体像の文章だけ**。依存先・依存元・公開シンボルの一覧は、スクリプトが `lookup/` から作る（P3）。AI は一覧を書かない
- `extract` は LLM を使わない。同じ入力（同じコミット）からは、1 バイトも違わない `lookup/` ができる（P6）

## 3. lookup の形

どれも、パスは**リポジトリのルートからの相対パス**（`/` 区切り）。行は文字列の昇順に並べる。

### 3.1 `lookup/tree.md`

```markdown
# ファイルツリー

| ファイル | モジュール | 言語 | 行数 |
| --- | --- | --- | --- |
| src/features/quiz/lib/streak.ts | features/quiz | typescript | 54 |
```

- 先頭の見出しと表の列は、この形に固定する。他のツールは、この表を読んでファイルからモジュールを引く（F1）
- `モジュール`は 4.2 の規則で決める。ルート直下のファイルは `(root)`
- 対象は `source.root` の下の、プラットフォーム定義が扱う拡張子のファイル（`exclude` に当たるものを除く）

### 3.2 `lookup/symbol_index.tsv`

ヘッダー行 `file<TAB>line<TAB>kind<TAB>name` ＋ 1 シンボル 1 行。

| 言語 | 対象のシンボル | `kind` |
| --- | --- | --- |
| TypeScript | `export` された function / class / interface / type / enum / const | `function` `class` `interface` `type` `enum` `const` |
| Python | トップレベルの def / class（名前が `_` で始まらないもの） | `function` `class` |

### 3.3 `lookup/reverse_imports.jsonl`

1 行 1 ファイル：`{"file": "src/lib/db.ts", "imported_by": ["src/app/page.tsx", "src/features/quiz/hooks/use-progress.ts"]}`。リポジトリ内のファイルへの import だけを数える（外部パッケージは含めない）。import されていないファイルの行は無い。

## 4. モジュール

### 4.1 要約（`modules/<モジュール>.md`）

モジュール名の `/` は、ファイル名では `__` にする（`features/quiz` → `modules/features__quiz.md`）。

```markdown
# features/quiz

## 役割
（AI）このモジュールが何をするか。2〜4 文。

## 主なファイル
（AI）材料の `representatives`（被参照数の多い上位ファイル）について、1 ファイル 1 行：`path` — 何をするか

## 公開シンボル
（スクリプト）symbol_index.tsv から、このモジュールのシンボルを表にしたもの

## 依存先
（スクリプト）このモジュールのファイルが import している、他のモジュールの一覧（import 数つき）

## 依存元
（スクリプト）このモジュールのファイルを import している、他のモジュールの一覧（import 数つき）
```

- 見出しは、この 5 つ・この順に固定する
- AI の部分に書く `path`（バッククォートで囲んだもの）は、`tree.md` にあり、そのモジュールに属するファイルでなければならない（検査 `ANCHOR`）
- 1 行目の `役割` の最初の 1 文は、`index.md` の「概要」になる

### 4.2 モジュールの決め方

設定の `rules.module_depth`（整数）で決める。ファイルの `source.root` からのディレクトリの、先頭から `module_depth` 個までをモジュール名とする。

| ファイル（`root = src`、`module_depth = 2`） | モジュール |
| --- | --- |
| `src/features/quiz/lib/streak.ts` | `features/quiz` |
| `src/features/mindset/index.ts` | `features/mindset` |
| `src/app/page.tsx` | `app`（ディレクトリが 1 段しか無いので、そこまで） |
| `src/proxy.ts` | `(root)` |

### 4.3 材料 `_raw/modules/<モジュール>.json`

AI（要約）に渡す入力。スクリプトが作る。ファイル名の `<モジュール>` は、4.1 と同じく `/` を `__` にしたもの（`_raw/modules/features__quiz.json`、`_raw/summaries/features__quiz.md`）。

| キー | 内容 |
| --- | --- |
| `module` | モジュール名 |
| `files` | ファイルの一覧（パス・行数） |
| `representatives` | 代表ファイル。そのファイルを import しているファイルの数（被参照数。同じモジュールのファイルも数える）が多い順、同数ならパスの昇順に並べた、上位 `rules.representatives` 個（仮：5） |
| `symbols` | そのモジュールの公開シンボル |
| `depends_on` `depended_by` | 依存先・依存元のモジュール |

AI は、材料の `representatives` のファイルを自分で読んで要約する。材料に無い事実（例：リポジトリ外の仕様）を書かない。

## 5. 全体像（`architecture.md`）

```markdown
# アーキテクチャ

## 全体像
（AI）レイヤーとデータの流れ。モジュール名は `index.md` にあるものだけを使う。

## モジュール間の依存
（スクリプト）モジュール × モジュールの import 数の表
```

## 6. `index.md`

スクリプトだけで作る。

```markdown
# モジュール一覧

| モジュール | ファイル数 | 公開シンボル数 | 概要 | 詳細 |
| --- | --- | --- | --- | --- |
| features/quiz | 21 | 38 | （役割の最初の 1 文） | [modules/features__quiz.md](modules/features__quiz.md) |
```

## 7. 出力の `SKILL.md`（辿り方）

雛形 `assets/output-skill.template.md` から、スクリプトが作る。AI も人も、この 4 つの辿り方で調べる。

| 問い | 辿り方 |
| --- | --- |
| 場所を探す | `lookup/symbol_index.tsv` で名前から `ファイル:行` を引く → `lookup/tree.md` でモジュールを引く → `modules/<モジュール>.md` |
| 影響範囲を見る | `lookup/reverse_imports.jsonl` で、そのファイルの依存元を辿る。モジュール単位なら `modules/<モジュール>.md` の `依存元` |
| 通称から実体を引く | `index.md` の概要と、各 `modules/*.md` の `役割` を、通称で検索する。見つかったモジュールの `主なファイル` を開く |
| 流れを追う | `architecture.md` の `モジュール間の依存` で順に辿り、各 `modules/*.md` を読む |

**最初に書く注意**：「この出力は、当たりを付けるための索引である。根拠はソースコードで、食い違ったらソースを信じる」

## 8. 設定ファイル `.qa/code-map.toml`

```toml
platform = ["typescript", "python"]

[source]
repo = "sample-app"             # "." なら利用側プロジェクト自身。別のリポジトリなら、絶対パスを .qa/local.toml の [repos] に書く
root = "src"                    # 読み始めるディレクトリ（repo からの相対パス）
exclude = ["**/*.test.ts"]      # 追加で除くもの（glob）。.git node_modules __pycache__ .next dist build は常に除く

[output]
dir = "output/code-map"

[rules]
module_depth = 2
representatives = 5             # 仮（12）

[rules.typescript]
tsconfig = "tsconfig.json"      # repo からの相対パス

[checks]
run = ["public-files"]
```

- `platform` は言語の配列。`root` の下に、どの言語のファイルも無ければ、止まる（C3 の 4）
- `source.repo` が `"."` でないとき、`manifest.json` の `source.repo` にはその名前を書く（絶対パスは書かない。C5）

## 9. プラットフォーム定義（言語）

`skills/code-map/platforms/<言語>/scan.py` が、次を用意する（C9）。共通部分は、言語の名前も構文も知らない。

| 名前 | 内容 |
| --- | --- |
| `EXTENSIONS` | 対象の拡張子（例：`(".ts", ".tsx")`） |
| `analyze(repo_root, root, path, all_files, options)` | 1 ファイルを読み、`{"lines": 行数, "imports": [...], "symbols": [...]}` を返す |

- `imports` の各要素：`{"spec": 書かれたとおりの文字列, "target": リポジトリ内のファイルのパス or null}`。`target` が null で相対 import なら「解決できなかった」、そうでなければ外部パッケージ。解決できなかった import の件数は、`extract` の出力と `check` の `stats.unresolved` に出す（失敗にはしない）
- `symbols` の各要素：`{"name", "kind", "line"}`（3.2 の対象のもの）
- `options`：設定の `rules.<言語>` の表

最初に作る 2 つ（仮の方式。12）：

| 言語 | 方式 |
| --- | --- |
| `typescript` | 正規表現で `import … from` `export … from` `import(` `require(` を抜く。`target` は、相対パス、tsconfig の `baseUrl` と `paths`（`@/*` など）の順に解決する。拡張子の補完（`.ts` `.tsx` `.js` `.jsx`）と `index.*` を試す |
| `python` | 標準ライブラリの `ast` で `import` と `from … import` を抜く。`target` は、`root` からの絶対 import と、相対 import を解決する（`a/b.py` と `a/b/__init__.py`） |

## 10. manifest.json（C5）

| キー | 値 |
| --- | --- |
| `source` | `{"repo": <設定の repo>, "commit": <HEAD のコミットの先頭 7 桁>}`。`source.root` の下に未コミットの変更があるときは、`"<コミット>+dirty"` |
| `generated_by` | `claude`：今回 AI が要約を書いたモジュールの数。`carried`：前回の要約を使い回したモジュールの数。`script`：0 |
| `items` | モジュールの数（`claude` ＋ `carried` と一致する） |
| `inputs` | `{}`（他のツールの出力を読まない） |

`+dirty` のとき、`update` は差分更新をせず、`build` をやり直すよう伝える。

## 11. 検査 `check_codemap.py`（C6 の形）

| `code` | 条件 |
| --- | --- |
| `PUBLIC_MISSING` | 公開ファイルが無い（1 の表の ✅ のもの） |
| `MODULE_MISSING` | `tree.md` のモジュールに `modules/<モジュール>.md` が無い、または `tree.md` に無いモジュールの要約がある |
| `SECTION` | 要約が、4.1 の 5 つの見出しを、この順に持っていない |
| `ANCHOR` | AI の部分のバッククォートのパスが、`tree.md` に無い、または別のモジュールのファイル |
| `REPRESENTATIVE` | 要約の `主なファイル` に、材料の `representatives` のパスが全部は無い（検査は `_raw/modules/` を読んでよい） |
| `LINK` | Markdown のリンク先が存在しない（`index.md` の詳細、`SKILL.md` など） |
| `PRIVATE_REF` | 公開ファイルが `_raw/` を参照している |
| `LOOKUP` | `symbol_index.tsv` か `reverse_imports.jsonl` が、`tree.md` に無いファイルを指している |
| `MANIFEST` | manifest.json が無い、または必須のキーが欠けている |

`stats`：`files` `modules` `symbols` `unresolved`（解決できなかった相対 import の数）。

## 12. 仮の値（P9）

| 値 | 初期値 | 見直し方 |
| --- | --- | --- |
| 代表ファイルの数 `representatives` | 5 | 要約の質を、サンプルアプリで見て決める |
| 代表ファイルの選び方 | 被参照数の多い順 | 他の指標（サイズ、名前）は、使ってみて足りなければ足す |
| TypeScript の import 解決の方式 | 正規表現 ＋ tsconfig | 取りこぼしが多ければ、方式を変える（`unresolved` の件数で測る） |

## 13. update（#20・#21 で実装）

- `core/plan.py` が、`manifest.json` の `source.commit` から今のコミットまでに変わったファイルを列挙する（追加・変更・削除・名前の変更）
- 変更ファイルを `tree.md` でモジュールに対応づける。**AI が要約を書き直すのは、ファイルが変わったモジュールだけ**。依存先・依存元・公開シンボルの一覧はスクリプトが作り直すので、他のモジュールの要約を AI が書き直す必要は無い
- 変更が大きいとき（初期値：モジュールの半分以上が変わった。仮）は、`build` と同じく全部作り直す
- 前回と今回のモジュールの要約は、`core/carry.py` の `split` で比べる。キーはモジュール名。ハッシュは、そのモジュールのファイルの（パス、内容のハッシュ）の組を、パスの昇順に並べたものから作る（ファイルの移動・名前の変更も、変わったと分かる）
- 今回のモジュールの一覧に無い前回のモジュールは、`modules/<モジュール>.md` と `_raw/` の要約を消す。新しいモジュールは、変わったモジュールと同じく AI が書く
