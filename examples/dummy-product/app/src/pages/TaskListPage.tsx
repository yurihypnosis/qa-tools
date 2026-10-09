// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// タスク一覧画面（/tasks）。作成日時の新しい順に並べ、各行から編集・削除のダイアログを開く。
import { useEffect, useState } from "react";
import { api, type Task } from "../api/client";
import { DeleteTaskDialog } from "../components/dialogs/DeleteTaskDialog";
import { TaskEditDialog } from "../components/dialogs/TaskEditDialog";

export function TaskListPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [editing, setEditing] = useState<Task | null>(null);
  const [deleting, setDeleting] = useState<Task | null>(null);

  useEffect(() => {
    api.listTasks().then(setTasks);
  }, []);

  return (
    <main>
      <h1>タスク一覧</h1>
      <a href="/tasks/new">タスクを作成</a>
      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            <a href={`/tasks/${task.id}`}>{task.name}</a>
            <button onClick={() => setEditing(task)}>編集</button>
            <button onClick={() => setDeleting(task)}>削除</button>
          </li>
        ))}
      </ul>
      {editing && (
        <TaskEditDialog task={editing} open onClose={() => setEditing(null)}
          onSaved={(saved) => setTasks(tasks.map((t) => (t.id === saved.id ? saved : t)))} />
      )}
      {deleting && (
        <DeleteTaskDialog task={deleting} open onClose={() => setDeleting(null)}
          onDeleted={(id) => setTasks(tasks.filter((t) => t.id !== id))} />
      )}
    </main>
  );
}
