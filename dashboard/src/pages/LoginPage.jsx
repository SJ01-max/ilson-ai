import { useState } from 'react';
import { login } from '../api/auth.js';

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
      <header className="login-header">
        <div className="brand">
          <h1>일손배정<span className="brand-ai">AI</span></h1>
          <span className="sub">양주시 공공형<br />계절근로 운영</span>
        </div>
        <span className="login-header-note">담당자용 운영 시스템</span>
      </header>
      <div className="login-layout">
        <section className="login-intro" aria-labelledby="login-intro-title">
          <p className="section-kicker">양주시 · 공공형 계절근로</p>
          <h2 id="login-intro-title">필요한 일손을,<br />필요한 농가에.</h2>
          <p className="login-description">한 주의 인력 수요를 살펴보고,<br />농가별 배정과 투입 계획을 검토합니다.</p>
          <section className="login-preview" aria-label="배정 화면 구성 예시">
            <div className="section-heading"><h3>농가별 배정</h3><span>화면 구성 예시</span></div>
            <table>
              <thead><tr><th scope="col">농가</th><th scope="col">작업</th><th scope="col">인원</th></tr></thead>
              <tbody>
                <tr><td>농가 A</td><td>배 수확</td><td>3명</td></tr>
                <tr><td>농가 B</td><td>배추 정리</td><td>2명</td></tr>
              </tbody>
            </table>
            <p className="login-preview-note">추천 사유를 확인하고 배정안을 검토합니다.</p>
          </section>
        </section>
        <section className="login-form-section" aria-labelledby="login-form-title">
          <p className="section-kicker">담당자 접속</p>
          <h2 id="login-form-title">로그인</h2>
          <p className="login-sub">발급받은 담당자 계정으로 접속하세요.</p>
          <form className="login-card" onSubmit={submit} noValidate>
            <label className="field"><span>아이디</span><input type="text" name="username" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus /></label>
            <label className="field"><span>비밀번호</span><input type="password" name="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button type="submit" className="primary-btn" disabled={busy || !username || !password}>{busy ? '확인 중…' : '로그인'}</button>
          </form>
          <p className="login-hint">계정 문의는 공공형 계절근로 운영 담당자에게 연락해 주세요.</p>
        </section>
      </div>
      <footer className="login-footer"><span>일손배정 AI</span><span>양주시 공공형 계절근로 유휴 예보·배정 플랫폼</span></footer>
    </main>
  );
}
