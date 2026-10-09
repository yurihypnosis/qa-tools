// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// メンバー管理画面（/settings/members）。DUMMY管理者だけが開ける。
import { useEffect, useState } from "react";
import { api, type Member } from "../api/client";

export function MembersSettingsPage() {
  const [members, setMembers] = useState<Member[]>([]);

  useEffect(() => {
    api.listMembers().then(setMembers);
  }, []);

  return (
    <main>
      <h1>メンバー管理</h1>
      <table>
        <thead><tr><th>メールアドレス</th><th>ロール</th></tr></thead>
        <tbody>
          {members.map((m) => (
            <tr key={m.id}><td>{m.email}</td><td>{m.role ?? "ロールなし"}</td></tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
