# 出力例（DUMMY-001）

> ⚠️ このフォルダはテスト用のダミー情報から生成した出力例です。実在の製品・仕様ではありません。

`/qa-tools:test-design PBI: DUMMY-001` を実際に実行して得た成果物（2026-10-08）。ゲート1 では QA 役として次を回答してから進めた。

- 衝突 #1：仕様書の「100文字以内」を採用
- 絵文字・結合文字：見た目の 1 文字を 1 文字と数える
- その他の `[要確認]`：未回答のまま残す

| ファイル | 内容 | 検査 |
| --- | --- | --- |
| `DUMMY-001/step1-analysis.md` | テスト分析（衝突アラート 1 件） | — |
| `DUMMY-001/step2-viewpoints.md` | 観点 8 個 | `check_viewpoints.py`：OK |
| `DUMMY-001/step3-testcases.md` | テストケース 37 件 | `check_testcases.py --viewpoints`：OK |
