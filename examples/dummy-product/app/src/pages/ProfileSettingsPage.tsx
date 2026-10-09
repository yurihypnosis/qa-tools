// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// プロフィール設定画面（/settings/profile）。
import { useState } from "react";
import { api } from "../api/client";

export function ProfileSettingsPage() {
  const [name, setName] = useState("");
  const [saved, setSaved] = useState(false);

  async function save() {
    await api.updateProfile(name);
    setSaved(true);
  }

  return (
    <main>
      <h1>プロフィール設定</h1>
      <label>表示名<input value={name} onChange={(e) => setName(e.target.value)} /></label>
      <button onClick={save}>保存</button>
      {saved && <p role="status">保存しました</p>}
    </main>
  );
}
