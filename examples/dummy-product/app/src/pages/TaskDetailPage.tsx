// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// タスク詳細画面（/tasks/:taskId）。
import { useEffect, useState } from "react";
import { api, type Task } from "../api/client";

export function TaskDetailPage({ taskId }: { taskId: number }) {
  const [task, setTask] = useState<Task | null>(null);

  useEffect(() => {
    api.getTask(taskId).then(setTask);
  }, [taskId]);

  if (!task) return <p>読み込み中</p>;
  return (
    <main>
      <h1>{task.name}</h1>
      <dl>
        <dt>期限</dt>
        <dd>{task.dueDate ?? "なし"}</dd>
      </dl>
      <a href="/tasks">一覧に戻る</a>
    </main>
  );
}
