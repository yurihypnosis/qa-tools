// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// backend/ の API を呼ぶ薄いクライアント。
export type Task = { id: number; name: string; dueDate: string | null; assigneeId: number | null; createdBy: number };
export type Member = { id: number; email: string; role: string | null };

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, { method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) => request<{ token: string }>("POST", "/auth/login", { email, password }),
  listTasks: () => request<Task[]>("GET", "/tasks"),
  getTask: (id: number) => request<Task>("GET", `/tasks/${id}`),
  createTask: (task: Omit<Task, "id" | "createdBy">) => request<Task>("POST", "/tasks", task),
  updateTask: (id: number, task: Partial<Task>) => request<Task>("PATCH", `/tasks/${id}`, task),
  deleteTask: (id: number) => request<void>("DELETE", `/tasks/${id}`),
  listMembers: () => request<Member[]>("GET", "/users"),
  updateProfile: (name: string) => request<void>("PATCH", "/users/me", { name }),
};
