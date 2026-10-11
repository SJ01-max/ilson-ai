import { useState } from 'react';
import { login } from '../api/auth.js';

/**
 * 로그인 화면 — POST /login (engine/api_server.py). 성공 시 토큰을 세션에 저장하고 onLogin 호출.
 */
export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const session = await login(username.trim(), password);
      onLogin(session);
    } catch (err) {
      setError(err.message ?? String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login">
      <form className="card login-card" onSubmit={submit} noValidate>
        <h1>일손배정 AI</h1>
        <p className="login-sub">양주시 공공형 계절근로 유휴 예보·배정 플랫폼</p>

        <label className="field">
          <span>아이디</span>
          <input
            type="text"
            name="username"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
          />
        </label>
        <label className="field">
          <span>비밀번호</span>
          <input
            type="password"
            name="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="primary-btn" disabled={busy || !username || !password}>
          {busy ? '확인 중…' : '로그인'}
        </button>
        <p className="login-hint">농협 공공형 담당자 계정으로 로그인하세요. MCP(Claude) 연동은 로그인과 별개로 동작합니다.</p>
      </form>
    </main>
  );
}
