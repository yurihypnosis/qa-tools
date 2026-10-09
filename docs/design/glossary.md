# 用語集

docs/design/ の文書と、qa-tools の Issue で使う言葉の定義。**ここに無い言葉で設計を書かない。** 新しい言葉が要るときは、先にここへ足す。

## 置き場所

| 用語 | 定義 | 例 |
| --- | --- | --- |
| プラグインのディレクトリ | このリポジトリ（qa-tools）を clone した場所。読み取り専用として扱い、実行中に書き込まない | `~/work/qa-tools/` |
| 利用側プロジェクト | qa-tools を使う側のディレクトリ。Claude Code をここで起動する。設定と出力はここにある。読むソースコードは、ここか、個人設定ファイルで指した別のリポジトリにある | テストケースを読むとき：`examples/dummy-product/` をコピーした `/tmp/dummy-product/`。サンプルアプリを読むとき：`examples/sample-app/` をコピーしたディレクトリ（ソースは `.qa/local.toml` で指したサンプルアプリの clone） |
| 設定ファイル | 利用側プロジェクトの `.qa/<ツール名>.toml`。ツールごとに 1 つ | `.qa/code-map.toml` |
| 個人設定ファイル | 利用側プロジェクトの `.qa/local.toml`。人によって違う値（絶対パス）だけを書く。git に入れない | `[repos] sample-app = "/Users/me/sample-app"` |
| 出力ディレクトリ | 利用側プロジェクトの `output/<ツール名>/`。ツールが書き込むのはここだけ | `output/code-map/` |
| core | プラグインのディレクトリ直下の `core/`。2 つ以上のツールが使う Python スクリプトを置く | `core/manifest.py` |
| サンプルアプリ | qa-tools 自体を試すための入力にするアプリ。ソースコードを読むツール（code-map・screen-list）の E2E に使う。別のアプリに替えることがあるので、設計・Issue・ツールの中では「サンプルアプリ」と呼び、アプリ名を書かない。今は [yurihypnosis/my-learning-app](https://github.com/yurihypnosis/my-learning-app)（Next.js・TypeScript）。替えるときは、この行と `examples/sample-app/.qa/` の設定を直す | — |

## ツールと操作

| 用語 | 定義 | 例 |
| --- | --- | --- |
| ツール | `skills/<ツール名>/` にある 1 つの skill。1 つの成果物を作る | screen-list（ソースコード → 画面一覧 CSV） |
| 動詞 | ツールに渡す引数の最初の語。`init` / `build` / `update` / `check` の 4 つ | `/qa-tools:code-map build` の `build` |
| 成果物 | ツールが出力ディレクトリに書くファイルのうち、人や他のツールが使うもの | screen-list の `output/screen-list/screens.csv` |
| プラットフォーム定義 | アプリの種類（言語・フレームワーク・テストケースの形式）によって変わる処理をまとめたもの。`skills/<ツール名>/platforms/<名前>/` に置き、設定ファイルの `platform` で選ぶ（[contracts.md の C9](contracts.md#c9-プラットフォーム定義)） | screen-list の `nextjs-app-router` |
| 項目 | 成果物を数える単位。ツールごとに決まっている | code-map はモジュール 1 つ、screen-list と test-priority は CSV の 1 行 |
| 中間ファイル | 成果物を作る途中でツールが書くファイル。他のツールは読まない | code-map の `output/code-map/_raw/` |

## 記録と検査

| 用語 | 定義 | 混同しやすいもの |
| --- | --- | --- |
| manifest | 出力ディレクトリに 1 つだけ置く `manifest.json`。「どの入力（コミット）から、どの設定で、いつ作ったか」を記録する | 成果物そのものではない |
| 差分更新 | 動詞 `update` の処理。manifest に記録したコミットから今のコミットまでに変わった入力に対応する項目だけを作り直す | `build` は全部作り直す |
| 引き継ぎ | 差分更新のとき、入力が変わっていない項目を前回の出力からそのまま写すこと | 作り直して同じ結果になることではない |
| 裁定 | AI が決められなかったことに人が下した判断。`output/<ツール名>/adjudications.json` に記録し、次の実行でも使う | 設定ファイルに書く値ではない |
| 検査 | 動詞 `check` の処理。成果物を読んで、決めた規則に合っているかを Python スクリプトで確かめる。成果物は書き換えない | AI による目視のレビューではない |
| 検査結果 | 検査スクリプトが標準出力に出す JSON。`status` が `ok` か `fail` | — |
| 公開ファイル | 成果物のうち、他のツールが読んでよいと決めたファイル（と列）。一覧は [data-flow.md](data-flow.md) の表にある | 公開ファイル以外の出力は、他のツールから読んではいけない |

## 画面とテスト

| 用語 | 定義 | 例 |
| --- | --- | --- |
| 画面 | 利用者が 1 つの単位として見る表示。何を 1 画面と数えるかは、screen-list のプラットフォーム定義が決める | Next.js App Router では `page.tsx` 1 つ。Android なら Activity 1 つ |
| ダイアログ | 画面の上に開く部品で、独立した URL を持たないもの | 削除の確認ダイアログ |
| 画面 ID | screen-list が画面とダイアログに付ける識別子。`<接頭辞>/<画面のキー>` の形で、どちらもプラットフォーム定義が決める。画面名を変えても変わらない | `web/settings`（Next.js App Router、キーは URL のパス） |
| 未解決マーカー | 情報が足りず決められなかった箇所に書く文字列。`[未解決: 理由]` の形 | `[未解決: fixture の中身が分からない]` |

## test-priority の言葉

| 用語 | 定義 | 例 |
| --- | --- | --- |
| 重要度 | テストケースが壊れたときの困る度合い。`R1`（最も重要）〜`R4`。test-case-generator の「重要度/Priority」列（High / Medium / Low）とは別のもの | `R2` |
| 規模 | そのテストケースを含む最小の実行単位。`sanity` ⊂ `smoke` ⊂ `light` ⊂ `full`（大きい規模は小さい規模をすべて含む） | `smoke`（smoke・light・full で実行される） |
| 開始点 | 重要度を決めるときの出発の値。設定の機能の重み表から引く | `[rules.areas.DMY-TASK.weights]` の `3`（R3） |
| リスク軸 | 重要度を上げる根拠になる 3 つの観点：`data`（データの正しさ）、`permission`（権限の境界）、`blast`（影響の広がり）。test-case-generator の「観点（TP）」とは別のもの | `data` |
| 影響範囲 | 壊れたときの実害の大きさ。`cosmetic`（見た目だけ）、`stop`（業務が止まる）、`harm`（お金・法令・権限に実害） | `stop` |
| 種別（代表・応用） | `代表`：その機能の基本的な正常系の操作。`応用`：境界値・異常系・条件の組み合わせを変えたもの | `応用` |
| グループ | 代表を 1 件に絞る単位。設定の `group_by`（機能か画面）で決める | 確認画面が `タスク編集ダイアログ` のケースすべて |

## ツール名

| ツール名 | 状態 | 入力 → 成果物 |
| --- | --- | --- |
| test-case-generator | 実装済み | PBI の資料 → テストケース（15 列の Markdown 表） |
| test-priority | 未実装（v0.5.0） | テストケース → 重要度と規模の CSV |
| code-map | 未実装（v0.6.0） | ソースコード → コードの索引と要約（Markdown ＋ JSONL） |
| screen-list | 未実装（v0.8.0） | ソースコード → 画面一覧 CSV |
