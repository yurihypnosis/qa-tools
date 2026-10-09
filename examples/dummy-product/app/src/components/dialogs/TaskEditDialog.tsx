// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// タスク編集ダイアログ。タスク一覧画面の「編集」ボタンで開く。
import { useState } from "react";
import { api, type Task } from "../../api/client";
import { Dialog } from "../ui/Dialog";

type Props = { task: Task; open: boolean; onClose: () => void; onSaved: (task: Task) => void };

export function TaskEditDialog({ task, open, onClose, onSaved }: Props) {
  const [name, setName] = useState(task.name);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    if (name.trim() === "") {
      setError("タスク名を入力してください");
      return;
    }
    onSaved(await api.updateTask(task.id, { name: name.trim() }));
    onClose();
  }

  return (
    <Dialog title="タスク編集" open={open} onClose={onClose}>
      <label>
        タスク名
        <input value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      {error && <p role="alert">{error}</p>}
      <button onClick={save}>保存</button>
      <button onClick={onClose}>キャンセル</button>
    </Dialog>
  );
}
