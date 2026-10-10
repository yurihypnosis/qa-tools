---
name: code-map
description: ソースコードから、どこに何があるか・変えると何に影響するか・モジュール同士がどうつながるかを引ける索引（ファイル一覧・シンボル・依存関係・モジュールごとの役割）を作る。依存関係や一覧はスクリプトが作り、AI が書くのはモジュールごとの役割の説明だけ。Use when the user asks to map, index, or summarize a codebase's structure — e.g. 「コードの索引を作って」「このリポジトリのどこに何があるか調べられるようにして」「モジュールの構成を整理して」「変更の影響範囲を調べられるようにして」「ソースが変わったので索引を更新して」.
license: MIT
metadata:
  version: "0.7.0"
---

# Code Map

## Overview

ソースコードを読み、`output/code-map/` に索引を作る。

- `lookup/`：ファイルの一覧とモジュール（`tree.md`）、公開シンボル（`symbol_index.tsv`）、「このファイルを import しているファイル」（`reverse_imports.jsonl`）
- `modules/<モジュール>.md`：モジュールごとの役割・主なファイル・公開シンボル・依存先・依存元
- `index.md` `architecture.md` `SKILL.md`：一覧、モジュール間の依存、出力の辿り方

AI が書くのは、**モジュールごとの役割の説明 1 段落だけ**。ほかはすべてスクリプトが作るので、同じソースからは同じ出力ができる。仕様の正本は `docs/design/tools/code-map.md`（プラグインのリポジトリ側）。

## 動詞

| 動詞 | やること | 読む reference |
| --- | --- | --- |
| `init` | 質問に答えて `.qa/code-map.toml` を作る | [references/init.md](references/init.md) |
| `build` | 全モジュールの役割を書いて、索引を最初から作る | 下の「流れ」。役割は [references/roles.md](references/roles.md) |
| `update` | 内容が変わったモジュールの役割だけを書き直す | 同上 |
| `check` | 出力を検査する。作り直さない | `codemap.py check` |

その動詞に入ってから、対応する reference を読む。

## 実行環境

Python 3.11 以上と標準ライブラリだけで動く（`pip install` は要らない）。`<skill>` は、この SKILL.md があるディレクトリ（skill の読み込み時に示される Base directory）。すべて `python3 <skill>/scripts/codemap.py <サブコマンド>` の形で、作業ディレクトリ（利用側プロジェクトのルート）から実行する。終了コードは 0=OK、1=検査の指摘あり、2=設定か入力のエラー。

## 流れ（build と update）

次のチェックリストを回答に書き写し、進むたびに印を付ける。

```
進み具合:
- [ ] 1 extract：ソースを読んで lookup/ を作り、役割を書くモジュールを決めた
- [ ] 2 roles：その全モジュールの役割を下書きに書き、apply で取り込んだ
- [ ] 3 assemble：modules/ などを組み立てた
- [ ] 4 finish：検査に通り、manifest.json を書いた
```

1. **extract**：`python3 <skill>/scripts/codemap.py extract --fresh`（`build`）または `extract`（`update`）。出力の JSON の `pending` が、役割を書くモジュールである。出力の `unresolved`（解決できなかった相対 import の件数）は、完了報告のために控える。終了コードが 2 なら、メッセージを見せて止まる（設定が無ければ `init` を勧める）。
2. **roles**：`pending` が空なら飛ばす。空でなければ `references/roles.md` を読み、`pending` のモジュールだけ役割を書いて取り込む。
3. **assemble**：`python3 <skill>/scripts/codemap.py assemble`。
4. **finish**：`python3 <skill>/scripts/codemap.py finish`。終了コード 1 なら、指摘（JSON）のモジュールだけを直して 2 から 1 回だけやり直す。それでも通らなければ、指摘を報告して止まる（manifest.json は書かれていない）。

## 完了報告

次だけを報告して終える（言語は、`.qa/product.md` に出力言語があればそれ、無ければ日本語）。

1. 出力のパス（`output/code-map/`）
2. 件数：ファイル・モジュール・公開シンボル（`codemap.py check --json` の `stats`）
3. 今回 AI が役割を書いたモジュールと、使い回したモジュールの数
4. `unresolved` の件数。多いときは、解決できていない import があるので、索引の依存が足りない可能性がある、と一言添える
5. 検査の結果

## Common Rationalizations

| 言い訳 | 実際 |
| --- | --- |
| 「役割に、依存先や公開シンボルも書いておく」 | 一覧はスクリプトが正確に作る。AI が書くと、実行のたびに変わり、古くなる |
| 「変わっていないモジュールも、念のため書き直す」 | 書き直すと文面が変わり、前回との比較ができない。`pending` に載ったモジュールだけ書く |
| 「ファイルを読まずに、モジュール名から役割を推測する」 | もっともらしい推測は、誤りに気づけない。`representatives` のファイルを読んで書く |
| 「検査に通らないが、manifest だけ書いておく」 | 通っていない出力を最新と記録すると、次の `update` が壊れた状態を前提にする |

## Red Flags

- `modules/` や `lookup/` のファイルを、Write や Edit で直接書いた（スクリプトが作る）
- 下書きに、`module` と `role` 以外のキーを書いた
- 役割に、`tree.md` に無いファイルのパスを書いた
- 検査のレシートを見ずに「OK」と報告した

## Verification

- [ ] `codemap.py check --json` を最後に実行し、`status` を確認した
- [ ] `manifest.json` の `items` が `stats.modules` と一致する
- [ ] `update` では、`pending` に載っていないモジュールの `modules/*.md` が前回と変わっていない
