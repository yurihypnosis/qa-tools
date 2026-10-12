---
name: screen-list
description: アプリの画面とダイアログを 1 行 1 件の CSV（画面 ID・画面名・種別・ロール・URL・ソース・モジュール・親画面）に洗い出す。画面があるかどうかはスクリプトがソースから決め、AI が書くのは画面名とロールだけ。Use when the user asks to list, inventory, or count the screens (pages and dialogs) of an app — e.g. 「画面一覧を作って」「アプリの画面とダイアログを洗い出して」「テスト範囲の画面を数えたい」「どの画面を誰が開けるか一覧にして」「ソースが変わったので画面一覧を更新して」. Needs a code-map output of the same source.
license: MIT
metadata:
  version: "0.8.0"
---

# Screen List

## Overview

ソースコードと code-map の出力を読み、`output/screen-list/screens.csv` を作る。

- **画面とダイアログがあるか**：スクリプトが、ファイルの置き場所と import から決める。AI は増やさず、消せない
- **AI が書くもの**：画面名とロールだけ（1 画面 1 行）。ソースに根拠が無ければ `[未解決: 理由]`
- URL を変えずにページの中で切り替わる画面は、人が設定（`rules.extra`）に書いたものだけを数える

同じソースからは、同じ画面の一覧（ID・URL・ソース）ができる。仕様の正本は `docs/design/tools/screen-list.md`（プラグインのリポジトリ側）。

## 動詞

| 動詞 | やること | 読む reference |
| --- | --- | --- |
| `init` | 質問に答えて `.qa/screen-list.toml` を作る | [references/init.md](references/init.md) |
| `build` | 全画面の名前とロールを書いて、CSV を最初から作る | 下の「流れ」。名前は [references/names.md](references/names.md) |
| `update` | ソースの内容が変わった画面だけ、名前とロールを書き直す | 同上 |
| `check` | 出力を検査する。作り直さない | `screens.py check` |

その動詞に入ってから、対応する reference を読む。

## 入力と実行環境

- 設定ファイル `.qa/screen-list.toml`（無ければ `init`）
- code-map の出力（設定の `source.code_map`）。読むファイルの内容が、code-map が読んだときと同じであること。古さはスクリプトが、ファイルごとのハッシュで調べ、古いと止まる（止まらなければ同じ）。git でなくてもよい。止まったら、メッセージのとおり `code-map update` を先に実行する
- Python 3.11 以上と標準ライブラリだけ。`<skill>` は、この SKILL.md があるディレクトリ（skill の読み込み時に示される Base directory）。すべて `python3 <skill>/scripts/screens.py <サブコマンド>` の形で、作業ディレクトリ（利用側プロジェクトのルート）から実行する。終了コードは 0=OK、1=検査の指摘あり、2=設定か入力のエラー

## 流れ（build と update）

次のチェックリストを回答に書き写し、進むたびに印を付ける。

```
進み具合:
- [ ] 1 candidates：画面とダイアログの候補を列挙し、名前を書く画面を決めた
- [ ] 2 names：その全画面の名前とロールを下書きに書き、apply で取り込んだ
- [ ] 3 merge：screens.csv を書いた
- [ ] 4 finish：検査に通り、manifest.json を書いた
```

1. **candidates**：`python3 <skill>/scripts/screens.py candidates --fresh`（`build`）または `candidates`（`update`）。出力の JSON の `pending` が、名前を書く画面。終了コードが 2 なら、メッセージを見せて止まる（code-map が古い、設定が無い、など）。
2. **names**：`pending` が空なら飛ばす。空でなければ `references/names.md` を読み、`pending` の画面だけ名前とロールを書いて取り込む。
3. **merge**：`python3 <skill>/scripts/screens.py merge`。
4. **finish**：`python3 <skill>/scripts/screens.py finish`。終了コード 1 なら、指摘（JSON）の画面だけを直して 2 から 1 回だけやり直す。それでも通らなければ、指摘を報告して止まる（manifest.json は書かれていない）。

## 完了報告

次だけを報告して終える（言語は、`.qa/product.md` に出力言語があればそれ、無ければ日本語）。

1. 出力のパス（`output/screen-list/screens.csv`）
2. 件数：画面・ダイアログ（`screens.py check --json` の `stats`）
3. 今回 AI が名前を書いた画面と、使い回した画面の数
4. `[未解決: …]` を含む行の数と、その画面（人が決めること）
5. **申告漏れの可能性**：`candidates` の出力の `hints`（画面らしいが一覧に入っていないファイル）。1 件ずつ「ページの中で切り替わる画面か、ページ本体の部品か」を、ソースを読んで推測し、人に `rules.extra` への追加を提案する（AI が自分で追加しない）
6. 検査の結果。**検査が通っても、候補の列挙そのものの正しさは確かめていない**と一言添える

## Common Rationalizations

| 言い訳 | 実際 |
| --- | --- |
| 「ソースを見て、ほかにも画面がありそうなので、一覧に足す」 | 画面を増やせるのは、スクリプトの候補と、人が書いた `rules.extra` だけ。足したい画面は、人に `rules.extra` への追加を提案する |
| 「ロールが分からないが、それらしいロールを書いておく」 | 推測は、誤りと見分けがつかない。根拠が無ければ `[未解決: 理由]` |
| 「変わっていない画面も、念のため名前を書き直す」 | 書き直すと名前が変わり、前回との比較ができない。`pending` に載った画面だけ書く |
| 「検査に通らないが、manifest だけ書いておく」 | 通っていない出力を最新と記録すると、次の `update` が壊れた状態を前提にする |

## Red Flags

- `screens.csv` を、Write や Edit で直接書いた（`merge` が書く）
- 下書きに、`id` `name` `roles` 以外のキーを書いた
- `pending` に無い画面の名前を書き直した
- 検査のレシートを見ずに「OK」と報告した

## Verification

- [ ] `screens.py check --json` を最後に実行し、`status` を確認した
- [ ] `manifest.json` の `items` が `stats.rows` と一致する
- [ ] `update` では、`pending` に載っていない画面の行が前回と変わっていない
