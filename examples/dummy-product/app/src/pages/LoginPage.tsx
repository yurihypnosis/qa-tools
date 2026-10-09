// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// ログイン画面（/login）。
import { useState } from "react";
import { api } from "../api/client";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    try {
      await api.login(email, password);
      location.assign("/tasks");
    } catch {
      setError("メールアドレスかパスワードが違います");
    }
  }

  return (
    <main>
      <h1>ログイン</h1>
      <label>メールアドレス<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
      <label>パスワード<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
      {error && <p role="alert">{error}</p>}
      <button onClick={submit}>ログイン</button>
    </main>
  );
}
