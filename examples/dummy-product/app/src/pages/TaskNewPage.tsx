// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// タスク作成画面（/tasks/new）。作成すると、作ったタスクの詳細画面へ移る。
import { useState } from "react";
import { api } from "../api/client";

export function TaskNewPage() {
  const [name, setName] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function create() {
    if (name.trim() === "") {
      setError("タスク名を入力してください");
      return;
    }
    const task = await api.createTask({ name: name.trim(), dueDate: dueDate || null, assigneeId: null });
    location.assign(`/tasks/${task.id}`);
  }

  return (
    <main>
      <h1>タスクを作成</h1>
      <label>タスク名<input value={name} onChange={(e) => setName(e.target.value)} /></label>
      <label>期限<input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} /></label>
      {error && <p role="alert">{error}</p>}
      <button onClick={create}>作成</button>
    </main>
  );
}
