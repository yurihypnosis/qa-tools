// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// タスク削除の確認ダイアログ。タスク一覧画面の「削除」ボタンで開く。
import { api, type Task } from "../../api/client";
import { Dialog } from "../ui/Dialog";

type Props = { task: Task; open: boolean; onClose: () => void; onDeleted: (id: number) => void };

export function DeleteTaskDialog({ task, open, onClose, onDeleted }: Props) {
  async function confirm() {
    await api.deleteTask(task.id);
    onDeleted(task.id);
    onClose();
  }

  return (
    <Dialog title="タスクを削除しますか？" open={open} onClose={onClose}>
      <p>「{task.name}」を削除します。元に戻せません。</p>
      <button onClick={confirm}>削除する</button>
      <button onClick={onClose}>キャンセル</button>
    </Dialog>
  );
}
