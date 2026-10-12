# 画面とテストケースのすき間

`screens.csv` の画面 18 件と、テストケース 31 件を突き合わせた結果。

## テストケースが 1 件も無い画面（5 件）

| 画面ID | 画面名 |
| --- | --- |
| web/catalog | 問題集一覧 |
| web/code-tour | コードの読み方 |
| web/flashcards | 単語カード |
| web/g-kentei/cheatsheet | G検定チートシート |
| web/index | ダッシュボード |

## R1・R2 のケースがあるのに、sanity・smoke に 1 件も無い画面（0 件）

なし

## 画面 ID を引けなかったケース（1 件）

| ケース | 確認画面 |
| --- | --- |
| APP-TC-005 | 全画面 |

引けない名前は、`rules.screen_aliases` に画面 ID を書いて指定する。
