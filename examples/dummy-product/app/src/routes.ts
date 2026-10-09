// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// 画面のルート定義。1 エントリ = 1 画面。
import { LoginPage } from "./pages/LoginPage";
import { MembersSettingsPage } from "./pages/MembersSettingsPage";
import { ProfileSettingsPage } from "./pages/ProfileSettingsPage";
import { TaskDetailPage } from "./pages/TaskDetailPage";
import { TaskListPage } from "./pages/TaskListPage";
import { TaskNewPage } from "./pages/TaskNewPage";

export const routes = [
  { path: "/login", component: LoginPage, title: "ログイン画面", auth: false },
  { path: "/tasks", component: TaskListPage, title: "タスク一覧画面", auth: true },
  { path: "/tasks/new", component: TaskNewPage, title: "タスク作成画面", auth: true },
  { path: "/tasks/:taskId", component: TaskDetailPage, title: "タスク詳細画面", auth: true },
  { path: "/settings/profile", component: ProfileSettingsPage, title: "プロフィール設定画面", auth: true },
  { path: "/settings/members", component: MembersSettingsPage, title: "メンバー管理画面", auth: true, roles: ["DUMMY管理者"] },
];
