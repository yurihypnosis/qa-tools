// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// 全ダイアログが使う共通部品。screen-list はこの部品を import しているファイルをダイアログとして数える。
import type { ReactNode } from "react";

type Props = { title: string; open: boolean; onClose: () => void; children: ReactNode };

export function Dialog({ title, open, onClose, children }: Props) {
  if (!open) return null;
  return (
    <div role="dialog" aria-modal="true" aria-label={title}>
      <h2>{title}</h2>
      {children}
      <button onClick={onClose}>閉じる</button>
    </div>
  );
}
